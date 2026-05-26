# wpy sector rotation backtest

This repository contains a Gsim-based A-share sector rotation factor framework. It converts stock-level Datayes/Tonglian `equ_fancy_factors_table1-10` factors into sector-level factor matrices, then backtests each sector factor and ranks results by Sharpe.

## What It Does

1. Defines 208 raw factors from `equ_fancy_factors_table1-10` in `config.py`.
2. Aggregates stock-level factor values to sector-level signals through either:
   - equal-weight aggregation with winsorization and standardization; or
   - market-cap-weighted aggregation with configurable cap handling.
3. Writes generated sector factor matrices as `.npy` files under `dm_data/`.
4. Builds a Gsim XML config and runs all factors as Alpha modules.
5. Parses PnL summaries and writes factor rankings to each workspace's `results/factor_ranking.csv`.

## Main Files

| Path | Purpose |
| --- | --- |
| `config.py` | Project config, date range, Gsim paths, and full table1-10 factor list. |
| `main.py` | Builds Gsim XML, runs backtests, parses summaries, and ranks factors. |
| `alpha_kchi.py` | Alpha module that reads precomputed `.npy` matrices and emits prior-day signal values. |
| `dmgr_scripts/Dmgr_tlsector_eq.py` | Equal-weight sector factor generator. |
| `dmgr_scripts/Dmgr_tlsector_cap.py` | Market-cap-weighted sector factor generator. |
| `run_table1_cap_trial.py` | Table1-only cap aggregation experiments. |
| `run_alltables_cap_trial.py` | Full table1-10 cap aggregation experiments. |
| `run_alltables_cap_stats_v5.py` | Full table1-10 cap experiments with `StatsSimpleV5` modes. |
| `run_combo_stats_v5.py` | Backtests a combined factor matrix. |
| `docs/项目交接说明.md` | Original handoff notes and experiment conclusions. |
| `docs/DATA.md` | Data inventory and storage policy. |

## Requirements

This project is tied to an internal Gsim environment and raw data layout:

- Python runtime: `/usr/local/gsim/.venv/bin/python`
- Gsim runner: `/usr/local/gsim/run.py`
- Summary tool: `/usr/local/gsim/tools/simsummary.py`
- Raw factor data: `/datasvc/rawdata/equ_fancy_factors_table{1-10}`
- Market and universe data under `/datasvc/rawdata/` and `/datasvc/data/cc/`

The repository stores code and documentation only. Generated `.npy` factor matrices and workspace outputs are intentionally ignored because they are large and environment-specific.

## Run

Equal-weight baseline:

```bash
cd /mnt/storage/work/hwang/wpy
python3 main.py
```

Full-table market-cap aggregation trials:

```bash
python3 run_alltables_cap_trial.py --all
```

Full-table trials with `StatsSimpleV5` modes:

```bash
python3 run_alltables_cap_stats_v5.py --all
```

Single strategy and mode:

```bash
python3 run_alltables_cap_stats_v5.py --strategy softmax_fill --mode 0
```

## Output

Each run creates a workspace such as `workspace_eq/` or `workspace_cap_all_softmax_fill_m0/` with:

- `configs/`: generated XML files.
- `logs/`: Gsim logs.
- `pnls/`: per-factor PnL files.
- `results/factor_ranking.csv`: factor ranking by Sharpe.

## Current Notes

The handoff notes report that, in table1 experiments, `softmax + fill_sector_mean` had the best overall Sharpe distribution. Full table1-10 cap experiments are scaffolded through `run_alltables_cap_trial.py` and `run_alltables_cap_stats_v5.py`.

