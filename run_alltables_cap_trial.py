import argparse
import glob
import os

from config import ALPHA_LIST, ProjectConfig
import main as main_mod


STRATEGIES = {
    "cap_pct_drop": {
        "weight": "cap_pct",
        "nan": "drop",
        "transform": "none",
    },
    "softmax_fill": {
        "weight": "softmax",
        "nan": "fill_sector_mean",
        "transform": "none",
    },
    "log1p_cap_pct_fill": {
        "weight": "cap_pct",
        "nan": "fill_sector_mean",
        "transform": "log1p",
    },
}


def _clear_cap_cache():
    cache_dir = os.path.join(
        ProjectConfig.DATA_ROOT, f"{ProjectConfig.AUTHOR}_{ProjectConfig.USED_SCRIPT}"
    )
    pattern = os.path.join(cache_dir, f"{ProjectConfig.AUTHOR}_{ProjectConfig.USED_SCRIPT}.tl_t*.npy")
    files = glob.glob(pattern)
    removed = 0
    for fp in files:
        try:
            os.remove(fp)
            removed += 1
        except OSError:
            pass
    print(f"已清理缓存: {removed} 个文件, 目录={cache_dir}", flush=True)


def run_one(strategy_name, keep_cache=False):
    cfg = STRATEGIES[strategy_name]
    os.environ["CAP_WEIGHT_MODE"] = cfg["weight"]
    os.environ["CAP_NAN_MODE"] = cfg["nan"]
    os.environ["CAP_TRANSFORM"] = cfg["transform"]

    base_dir = os.path.dirname(os.path.abspath(__file__))
    ProjectConfig.USED_SCRIPT = "tlsector_cap"
    ProjectConfig.AUTHOR = f"kchi_all_{strategy_name}"
    ProjectConfig.WORKSPACE = os.path.join(base_dir, f"workspace_cap_all_{strategy_name}")
    main_mod.ALPHA_LIST = ALPHA_LIST

    print("=" * 72, flush=True)
    print(
        f"开始全表试验: {strategy_name}, "
        f"weight={cfg['weight']}, nan={cfg['nan']}, transform={cfg['transform']}",
        flush=True,
    )
    print(f"AUTHOR={ProjectConfig.AUTHOR}", flush=True)
    print(f"WORKSPACE={ProjectConfig.WORKSPACE}", flush=True)
    print(f"ALPHA_COUNT={len(main_mod.ALPHA_LIST)}", flush=True)
    print("=" * 72, flush=True)

    if keep_cache:
        print("保留缓存: 跳过清理步骤（--keep-cache）", flush=True)
    else:
        _clear_cap_cache()
    main_mod.init_env()
    ok = main_mod.run_gsim()
    if not ok:
        raise SystemExit(1)
    out_csv = main_mod.run_summaries_and_sort()
    print(f"[{strategy_name}] 完成, 排序结果: {out_csv}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Run all-table cap aggregation trials and save ranking outputs."
    )
    parser.add_argument(
        "--strategy",
        choices=list(STRATEGIES.keys()),
        help="Run one strategy only.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all built-in strategies sequentially.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip strategies that already have ranking outputs.",
    )
    parser.add_argument(
        "--keep-cache",
        action="store_true",
        help="Do not clear dm_data cache before each strategy.",
    )
    args = parser.parse_args()

    def maybe_run(name):
        if args.resume:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            out_csv = os.path.join(
                base_dir, f"workspace_cap_all_{name}", "results", "factor_ranking.csv"
            )
            if os.path.isfile(out_csv) and os.path.getsize(out_csv) > 64:
                print(f"[resume] 已存在结果，跳过: {name} -> {out_csv}", flush=True)
                return
        run_one(name, keep_cache=args.keep_cache)

    if args.all:
        for name in STRATEGIES:
            maybe_run(name)
        return

    if args.strategy:
        maybe_run(args.strategy)
        return

    parser.error("请提供 --strategy 或 --all")


if __name__ == "__main__":
    main()
