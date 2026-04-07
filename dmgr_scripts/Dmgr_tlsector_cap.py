from gsim.utils.NioData import *
from gsim.data import DataManagerMapped
from gsim.data import DataRegistry as dr
from gsim.data import Universe as uv
import numpy as np
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import FACTOR_TABLE_LIST, ProjectConfig
except ImportError:
    print("Error: Could not import FACTOR_TABLE_LIST from config.py. Please check the file and try again.")
    FACTOR_TABLE_LIST = [(1, "APB_SKEW"), (1, "TA_ENTROPY")]

class Dmgrtlsector(DataManagerMapped):
    def __init__(self):
        DataManagerMapped.__init__(self)

        # 全表因子列表: [(table_id, factor_name), ...]
        self.factor_list = FACTOR_TABLE_LIST

        # 环境变量控制试验方式:
        #   CAP_WEIGHT_MODE: cap_pct | softmax
        #   CAP_NAN_MODE:    drop | fill_sector_mean
        #   CAP_TRANSFORM:   none | log1p
        self.weight_mode = os.getenv("CAP_WEIGHT_MODE", "cap_pct").strip().lower()
        self.nan_mode = os.getenv("CAP_NAN_MODE", "drop").strip().lower()
        self.cap_transform = os.getenv("CAP_TRANSFORM", "none").strip().lower()
        if self.weight_mode not in ("cap_pct", "softmax"):
            raise ValueError(f"Unsupported CAP_WEIGHT_MODE={self.weight_mode}")
        if self.nan_mode not in ("drop", "fill_sector_mean"):
            raise ValueError(f"Unsupported CAP_NAN_MODE={self.nan_mode}")
        if self.cap_transform not in ("none", "log1p"):
            raise ValueError(f"Unsupported CAP_TRANSFORM={self.cap_transform}")

        for tid, f in self.factor_list:
            tag = f't{tid}_{f}'
            setattr(self, f'tl_{tag.lower()}', NIO_MATRIX())

    def initialize(self, id, path, cfg):
        DataManagerMapped.initialize(self, id, path, cfg)

        print(
            f"[{self.tag}] 全表试验参数: "
            f"CAP_WEIGHT_MODE={self.weight_mode}, CAP_NAN_MODE={self.nan_mode}, "
            f"CAP_TRANSFORM={self.cap_transform}"
        )

        for tid, f in self.factor_list:
            tag = f't{tid}_{f}'
            matrix = getattr(self, f'tl_{tag.lower()}')
            self.addDailyData(matrix, f'{self.tag}.tl_{tag.lower()}')

    def dependencies(self):
        DataManagerMapped.dependencies(self)
        dr.registerDependency(self.mid, 'sector')
        dr.registerDependency(self.mid, 'cap')
        dr.registerDependency(self.mid, 'ALL_TRD')

        for tid, f in self.factor_list:
            dr.registerDependency(self.mid, f'equ_fancy_factors_table{tid}.{f}')

    @staticmethod
    def _softmax(x):
        x = np.asarray(x, dtype=np.float64)
        x_max = np.max(x)
        ex = np.exp(x - x_max)
        s = np.sum(ex)
        if s <= 0:
            return np.ones_like(x) / len(x)
        return ex / s

    def loadData(self, di_start):
        self.fillnan(di_start, len(uv.Dates))

        d_sector = dr.getData('sector').data
        d_cap = dr.getData('cap').data
        d_all_trd = dr.getData('ALL_TRD').data

        for tid, f in self.factor_list:
            tag = f't{tid}_{f}'
            print(f'[{self.tag}] Calculating (all-table-cap-trial) Sector Factor: {tag}...')

            d_feat = dr.getData(f'equ_fancy_factors_table{tid}.{f}').data
            out_matrix = getattr(self, f'tl_{tag.lower()}')

            for di in range(di_start, len(uv.Dates)):
                if uv.Dates[di] < int(ProjectConfig.START_DATE)+256: 
                    continue
                

                if di % 100 == 0:
                    print(f'[{tag}] Processing date index: {di}, date: {uv.Dates[di]}')
                daily_sector = d_sector[di]
                daily_cap = d_cap[di-1] 
                daily_feat = d_feat[di]
                daily_trd = d_all_trd[di]

                valid_sec_values = []
                sec_to_idx = {}

                sector_to_items = {}
                for ii in range(len(daily_sector)):
                    sec = daily_sector[ii]
                    if sec <= 0 or daily_trd[ii] == 0 or np.isnan(daily_feat[ii]):
                        continue
                    if sec not in sector_to_items:
                        sector_to_items[sec] = []
                    sector_to_items[sec].append((daily_feat[ii], daily_cap[ii]))

                valid_caps_all = daily_cap[
                    (~np.isnan(daily_cap)) &
                    (daily_sector > 0) &
                    (daily_trd != 0) &
                    (~np.isnan(daily_feat))
                ]
                global_cap_mean = np.mean(valid_caps_all) if len(valid_caps_all) > 0 else np.nan

                for sec, items in sector_to_items.items():
                    feats = np.array([x[0] for x in items], dtype=np.float64)
                    caps_raw = np.array([x[1] for x in items], dtype=np.float64)

                    if self.nan_mode == "drop":
                        keep = ~np.isnan(caps_raw)
                        feats = feats[keep]
                        caps = caps_raw[keep]
                    else:  # fill_sector_mean
                        caps = caps_raw.copy()
                        nan_mask = np.isnan(caps)
                        if np.any(nan_mask):
                            valid = ~nan_mask
                            if np.any(valid):
                                fill_val = np.mean(caps[valid])
                            else:
                                fill_val = global_cap_mean
                            if np.isnan(fill_val):
                                # 当前日全市场都缺 cap，无法市值加权，跳过该行业
                                continue
                            caps[nan_mask] = fill_val

                    if len(feats) == 0:
                        continue

                    caps = np.maximum(caps, 0.0)
                    if np.sum(caps) <= 0:
                        continue

                    if self.cap_transform == "log1p":
                        caps = np.log1p(caps)
                        if np.sum(caps) <= 0:
                            continue

                    if self.weight_mode == "cap_pct":
                        w = caps / np.sum(caps)
                    else:  # softmax
                        w = self._softmax(caps)

                    val = np.sum(feats * w)
                    valid_sec_values.append(val)
                    sec_to_idx[sec] = val

                if len(valid_sec_values) == 0:
                    continue

                vals_array = np.array(valid_sec_values)
                
                v_mean = np.mean(vals_array)
                v_std = np.std(vals_array)
                
                if v_std > 1e-6:
                    vals_array = (vals_array - v_mean) / v_std
                else:
                    vals_array = vals_array - v_mean 

                vals_array = np.clip(vals_array, -3.0, 3.0)

                final_sector_map = dict(zip(sec_to_idx.keys(), vals_array))

                for ii in range(len(daily_sector)):
                    sec = daily_sector[ii]
                    out_matrix[di, ii] = final_sector_map.get(sec, np.nan)

        return