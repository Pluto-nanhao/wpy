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

MODES = {
    0: "long_short",
    1: "excess_zz1000",
    2: "top10_long_short",
}


def _clear_strategy_cache(author):
    cache_dir = os.path.join(ProjectConfig.DATA_ROOT, f"{author}_tlsector_cap")
    pattern = os.path.join(cache_dir, f"{author}_tlsector_cap.tl_t*.npy")
    files = glob.glob(pattern)
    removed = 0
    for fp in files:
        try:
            os.remove(fp)
            removed += 1
        except OSError:
            pass
    print(f"已清理缓存: {removed} 个文件, 目录={cache_dir}", flush=True)


def _workspace(strategy_name, mode):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, f"workspace_cap_all_{strategy_name}_m{mode}")


def _ranking_path(strategy_name, mode):
    return os.path.join(_workspace(strategy_name, mode), "results", "factor_ranking.csv")


def run_one(strategy_name, mode):
    cfg = STRATEGIES[strategy_name]
    os.environ["CAP_WEIGHT_MODE"] = cfg["weight"]
    os.environ["CAP_NAN_MODE"] = cfg["nan"]
    os.environ["CAP_TRANSFORM"] = cfg["transform"]

    ProjectConfig.USED_SCRIPT = "tlsector_cap"
    ProjectConfig.AUTHOR = f"kchi_all_{strategy_name}"
    ProjectConfig.WORKSPACE = _workspace(strategy_name, mode)
    ProjectConfig.STATS_MODULE = "StatsSimpleV5"
    ProjectConfig.STATS_MODE = mode
    ProjectConfig.STATS_INDEX_RET_FIELD = "aindexeodprices.s_dq_pctchange_000852"
    ProjectConfig.STATS_THRES = 90
    main_mod.ALPHA_LIST = ALPHA_LIST

    print("=" * 86, flush=True)
    print(
        f"开始回测: strategy={strategy_name}, mode={mode}({MODES[mode]}), "
        f"weight={cfg['weight']}, nan={cfg['nan']}, transform={cfg['transform']}",
        flush=True,
    )
    print(f"AUTHOR={ProjectConfig.AUTHOR}", flush=True)
    print(f"WORKSPACE={ProjectConfig.WORKSPACE}", flush=True)
    print(f"ALPHA_COUNT={len(main_mod.ALPHA_LIST)}", flush=True)
    print("=" * 86, flush=True)

    main_mod.init_env()
    ok = main_mod.run_gsim()
    if not ok:
        raise SystemExit(1)
    out_csv = main_mod.run_summaries_and_sort()
    print(f"[{strategy_name}][mode={mode}] 完成, 排序结果: {out_csv}", flush=True)


def main():
    parser = argparse.ArgumentParser(
        description="Run all-table cap trials with StatsSimpleV5 mode=0/1/2."
    )
    parser.add_argument(
        "--strategy",
        choices=list(STRATEGIES.keys()),
        help="Run one strategy only.",
    )
    parser.add_argument(
        "--mode",
        type=int,
        choices=[0, 1, 2],
        help="Run one mode only.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all strategies x all modes.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip tasks with existing ranking outputs.",
    )
    parser.add_argument(
        "--keep-cache",
        action="store_true",
        help="Do not clear strategy cache before first mode run.",
    )
    args = parser.parse_args()

    def should_skip(strategy_name, mode):
        if not args.resume:
            return False
        out_csv = _ranking_path(strategy_name, mode)
        if os.path.isfile(out_csv) and os.path.getsize(out_csv) > 64:
            print(f"[resume] 已存在结果，跳过: {strategy_name}, mode={mode} -> {out_csv}", flush=True)
            return True
        return False

    def run_strategy_all_modes(strategy_name):
        author = f"kchi_all_{strategy_name}"
        if not args.keep_cache:
            _clear_strategy_cache(author)
        else:
            print(f"[{strategy_name}] 保留缓存（--keep-cache）", flush=True)
        for mode in MODES:
            if should_skip(strategy_name, mode):
                continue
            run_one(strategy_name, mode)

    if args.all:
        for strategy_name in STRATEGIES:
            run_strategy_all_modes(strategy_name)
        return

    if args.strategy and args.mode is not None:
        if not args.keep_cache:
            _clear_strategy_cache(f"kchi_all_{args.strategy}")
        if not should_skip(args.strategy, args.mode):
            run_one(args.strategy, args.mode)
        return

    parser.error("请使用 --all 或同时提供 --strategy 和 --mode")


if __name__ == "__main__":
    main()
