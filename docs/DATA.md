# Data Inventory

This project separates source code from generated data. The generated matrices and backtest workspaces are large and should not be committed to GitHub unless a separate storage policy is chosen.

## Raw Inputs

These inputs are read from the local Gsim/data environment:

| Data | Expected Location | Used By |
| --- | --- | --- |
| Datayes/Tonglian factor tables | `/datasvc/rawdata/equ_fancy_factors_table{1-10}` | `Dmgr_tlsector_eq.py`, `Dmgr_tlsector_cap.py` |
| Sector classification | `/datasvc/rawdata/AShareWindIndustry/` through `Basedata` | sector aggregation scripts |
| Trading universe | Gsim `ALL_TRD` | alpha and aggregation filtering |
| Market cap | Gsim `cap` data | `Dmgr_tlsector_cap.py` |
| Index returns | `/datasvc/rawdata/aindexeodprices/` | `StatsSimpleV5` mode 1 |
| Calendar and security IDs | `/datasvc/rawdata/wind_calendar.csv`, `/datasvc/rawdata/secID` | generated Gsim XML |

## Generated Data

| Directory | Contents | Git Policy |
| --- | --- | --- |
| `dm_data/` | Generated sector factor `.npy` matrices, one matrix per factor and aggregation strategy. | Ignored. Large binary cache. |
| `workspace_eq/` | Equal-weight baseline configs, logs, PnL files, and ranking outputs. | Ignored. Reproducible run output. |
| `workspace_cap_t1_*/` | Table1 cap aggregation experiment output. | Ignored. Reproducible run output. |
| `workspace_cap_all_*/` | Full table1-10 cap aggregation experiment output. | Ignored. Reproducible run output. |
| `workspace_combo_*/` | Combined-factor backtest output. | Ignored. Reproducible run output. |

The local `dm_data/kchi_cap_pct_drop_none_tlsector_cap/` cache currently contains 208 `.npy` files. Many files are about 171 MB each, so committing them directly would make the repository impractical for normal GitHub use.

## Rebuild Policy

Regenerate caches and workspaces from source scripts:

```bash
python3 main.py
python3 run_alltables_cap_trial.py --all
python3 run_alltables_cap_stats_v5.py --all
```

If these generated outputs need to be shared, use a separate artifact store or Git LFS after confirming repository quota and access rules.

