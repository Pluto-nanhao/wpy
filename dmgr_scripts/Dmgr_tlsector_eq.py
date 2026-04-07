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
    print("Error: Could not import FACTOR_TABLE_LIST from config.py.")
    FACTOR_TABLE_LIST = [(1, "APB_SKEW"), (1, "TA_ENTROPY")]  # fallback

# 生成 factor_tag: t1_APB_SKEW 等，用于矩阵命名
def _tag(tid, f):
    return f"t{tid}_{f}"


class Dmgrtlsector(DataManagerMapped):
    def __init__(self):
        DataManagerMapped.__init__(self)
        self.factor_list = FACTOR_TABLE_LIST  # [(table_num, factor_name), ...]

        for tid, f in self.factor_list:
            tag = _tag(tid, f)
            setattr(self, f'tl_{tag.lower()}', NIO_MATRIX())

    def initialize(self, id, path, cfg):
        DataManagerMapped.initialize(self, id, path, cfg)
        for tid, f in self.factor_list:
            tag = _tag(tid, f)
            matrix = getattr(self, f'tl_{tag.lower()}')
            self.addDailyData(matrix, f'{self.tag}.tl_{tag.lower()}')

    def dependencies(self):
        DataManagerMapped.dependencies(self)
        dr.registerDependency(self.mid, 'sector')
        dr.registerDependency(self.mid, 'ALL_TRD')
        for tid, f in self.factor_list:
            dr.registerDependency(self.mid, f'equ_fancy_factors_table{tid}.{f}')

    def loadData(self, di_start):
        self.fillnan(di_start, len(uv.Dates))
        d_sector = dr.getData('sector').data
        d_all_trd = dr.getData('ALL_TRD').data

        for tid, f in self.factor_list:
            tag = _tag(tid, f)
            print(f'[{self.tag}] Calculating Winsorized & Equal-Weighted Sector Factor: {tag}...')

            d_feat = dr.getData(f'equ_fancy_factors_table{tid}.{f}').data
            out_matrix = getattr(self, f'tl_{tag.lower()}')

            for di in range(di_start, len(uv.Dates)):
                if uv.Dates[di] < int(ProjectConfig.START_DATE) + 256:
                    continue
                if di % 100 == 0:
                    print(f'[{tag}] Processing date index: {di}, date: {uv.Dates[di]}')

                daily_sector = d_sector[di]
                daily_feat = d_feat[di].copy()
                daily_trd = d_all_trd[di]

                valid_idx = np.where((~np.isnan(daily_feat)) & (daily_trd != 0) & (daily_sector > 0))[0]

                if len(valid_idx) > 0:
                    f_values = daily_feat[valid_idx]
                    median = np.median(f_values)
                    mad = np.median(np.abs(f_values - median))
                    limit_up = median + 3 * 1.4826 * mad
                    limit_down = median - 3 * 1.4826 * mad
                    f_values = np.clip(f_values, limit_down, limit_up)
                    f_mean = np.mean(f_values)
                    f_std = np.std(f_values)
                    if f_std > 0:
                        f_values = (f_values - f_mean) / f_std
                    daily_feat[valid_idx] = f_values

                sector_stats = {}
                for idx in valid_idx:
                    sec = daily_sector[idx]
                    val = daily_feat[idx]
                    if sec not in sector_stats:
                        sector_stats[sec] = [0.0, 0]
                    sector_stats[sec][0] += val
                    sector_stats[sec][1] += 1

                sector_avg = {s: (v[0] / v[1]) for s, v in sector_stats.items()}

                for ii in range(len(daily_sector)):
                    sec = daily_sector[ii]
                    out_matrix[di, ii] = sector_avg.get(sec, np.nan)

        return
