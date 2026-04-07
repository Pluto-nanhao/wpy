import argparse
import os
import glob

from config import ProjectConfig, TABLE_FACTORS
import main as main_mod


def _table1_alpha_list():
    return [f"t1_{f}" for f in TABLE_FACTORS.get(1, [])]


def _clear_table1_cap_cache():
    """清理 table1 的 tlsector_cap 缓存，避免不同参数试验复用旧 npy。"""
    cache_dir = os.path.join(
        ProjectConfig.DATA_ROOT, f"{ProjectConfig.AUTHOR}_{ProjectConfig.USED_SCRIPT}"
    )
    pattern = os.path.join(cache_dir, f"{ProjectConfig.AUTHOR}_{ProjectConfig.USED_SCRIPT}.tl_t1_*.npy")
    files = glob.glob(pattern)
    removed = 0
    for fp in files:
        try:
            os.remove(fp)
            removed += 1
        except OSError:
            pass
    print(f"已清理旧缓存: {removed} 个文件, 目录={cache_dir}", flush=True)


def run_one_trial(weight_mode, nan_mode, cap_transform):
    os.environ["CAP_WEIGHT_MODE"] = weight_mode
    os.environ["CAP_NAN_MODE"] = nan_mode
    os.environ["CAP_TRANSFORM"] = cap_transform

    base_dir = os.path.dirname(os.path.abspath(__file__))
    nan_short = "fill" if nan_mode == "fill_sector_mean" else "drop"
    trial_author = f"kchi_{weight_mode}_{nan_short}_{cap_transform}"
    ProjectConfig.AUTHOR = trial_author
    ProjectConfig.USED_SCRIPT = "tlsector_cap"
    ProjectConfig.WORKSPACE = os.path.join(
        base_dir, f"workspace_cap_t1_{weight_mode}_{nan_mode}_{cap_transform}"
    )

    main_mod.ALPHA_LIST = _table1_alpha_list()

    print("=" * 60, flush=True)
    print(
        f"开始试验: weight={weight_mode}, nan={nan_mode}, "
        f"transform={cap_transform}, 因子数={len(main_mod.ALPHA_LIST)}",
        flush=True,
    )
    print(f"AUTHOR={ProjectConfig.AUTHOR}", flush=True)
    print(f"WORKSPACE={ProjectConfig.WORKSPACE}", flush=True)
    print("=" * 60, flush=True)

    _clear_table1_cap_cache()
    main_mod.init_env()
    ok = main_mod.run_gsim()
    if not ok:
        raise SystemExit(1)
    main_mod.run_summaries_and_sort()


def main():
    parser = argparse.ArgumentParser(
        description="Run table1 sector-factor backtest with cap-weighting trials."
    )
    parser.add_argument(
        "--weight",
        choices=["cap_pct", "softmax"],
        default="cap_pct",
        help="Sector aggregation weight mode.",
    )
    parser.add_argument(
        "--nan",
        choices=["drop", "fill_sector_mean"],
        default="drop",
        help="How to handle NaN market cap.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all combinations: 2 weight modes x 2 NaN modes.",
    )
    parser.add_argument(
        "--cap-transform",
        choices=["none", "log1p"],
        default="none",
        help="Transform market cap before weighting.",
    )
    args = parser.parse_args()

    if args.all:
        for weight_mode in ["cap_pct", "softmax"]:
            for nan_mode in ["drop", "fill_sector_mean"]:
                for cap_transform in ["none", "log1p"]:
                    run_one_trial(weight_mode, nan_mode, cap_transform)
    else:
        run_one_trial(args.weight, args.nan, args.cap_transform)


if __name__ == "__main__":
    main()
