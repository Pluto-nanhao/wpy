# 行业轮动测算体系

本文档基于当前 `wpy` 项目整理一套完整的行业轮动测算体系，用于把股票层面的通联因子加工成行业层面的轮动信号，并通过 Gsim 回测框架评估因子的行业配置效果。

这套体系的核心目标不是训练一个黑箱模型，而是建立一条可复现的研究流水线：

1. 从股票因子出发，构造行业因子。
2. 用行业因子形成可交易的行业排序信号。
3. 在统一组合规则下回测每个信号。
4. 用收益、风险、稳定性指标筛选可用于行业轮动的因子。
5. 对不同聚合方式、组合模式、统计口径做横向比较。

## 1. 系统定位

行业轮动模型回答的问题是：在每个交易日，哪些行业相对更值得配置，哪些行业应当低配或回避。

当前项目采用“股票因子到行业信号”的路径：

- 输入：股票级别的通联 `equ_fancy_factors_table1-10` 原始因子。
- 加工：按 Wind 行业分组，对行业内股票因子做等权或市值加权聚合。
- 输出：每个交易日、每只股票对应一个行业层面的因子值。同一行业内股票值相同。
- 回测：Gsim 根据行业因子值构建组合，输出每个因子的 PnL 和统计指标。
- 排名：按 Sharpe 等指标筛选行业轮动信号。

代码映射：

| 模块 | 作用 |
| --- | --- |
| `config.py` | 因子池、日期、路径、统计参数配置。 |
| `dmgr_scripts/Dmgr_tlsector_eq.py` | 等权行业因子生成。 |
| `dmgr_scripts/Dmgr_tlsector_cap.py` | 市值加权行业因子生成。 |
| `alpha_kchi.py` | 从 `.npy` 因子矩阵读取前一日信号。 |
| `main.py` | 生成 Gsim XML、运行回测、解析并排序结果。 |
| `run_table1_cap_trial.py` | table1 小样本聚合方式实验。 |
| `run_alltables_cap_trial.py` | 全表市值聚合实验。 |
| `run_alltables_cap_stats_v5.py` | 全表多统计模式实验。 |
| `run_combo_stats_v5.py` | 组合因子回测。 |

## 2. 数据体系

### 2.1 原始数据

| 数据 | 来源路径 | 用途 |
| --- | --- | --- |
| 股票因子 | `/datasvc/rawdata/equ_fancy_factors_table{1-10}` | 构造行业因子。 |
| 行业分类 | `/datasvc/rawdata/AShareWindIndustry/`，通过 `Basedata` 读取 | 股票归属行业。 |
| 可交易股票池 | Gsim `ALL_TRD` | 过滤停牌、不可交易样本。 |
| 市值数据 | Gsim `cap` | 市值加权行业聚合。 |
| 指数收益 | `/datasvc/rawdata/aindexeodprices/` | 超额收益统计。 |
| 日历与证券列表 | `/datasvc/rawdata/wind_calendar.csv`、`/datasvc/rawdata/secID` | Gsim universe 构建。 |

### 2.2 因子池

当前因子池定义在 `config.py` 的 `TABLE_FACTORS` 中，覆盖 table1-10 共 208 个因子。

因子 ID 统一命名为：

```text
t{table_id}_{factor_name}
```

示例：

```text
t1_CORR_VP
t2_ROE_Q
t9_GTRA_SELL_PCT_VOL
t10_GR_PE_TTM
```

系统会自动生成两个列表：

- `ALPHA_LIST`：回测用 Alpha ID 列表。
- `FACTOR_TABLE_LIST`：数据管理模块读取因子时使用的 `(table_id, factor_name)` 列表。

### 2.3 生成数据

| 目录 | 内容 | 是否入库 |
| --- | --- | --- |
| `dm_data/` | 行业因子 `.npy` 矩阵缓存。 | 不入库。 |
| `workspace_eq/` | 等权聚合回测输出。 | 不入库。 |
| `workspace_cap_t1_*/` | table1 聚合方式实验输出。 | 不入库。 |
| `workspace_cap_all_*/` | 全表聚合方式实验输出。 | 不入库。 |
| `workspace_combo_*/` | 组合因子回测输出。 | 不入库。 |

这些目录由脚本生成，体量大且依赖本地数据环境，因此只记录生成规则，不直接上传 GitHub。

## 3. 行业因子构造

行业轮动信号的关键环节是把股票因子聚合成行业因子。当前项目支持两类聚合方式。

### 3.1 等权聚合

实现文件：`dmgr_scripts/Dmgr_tlsector_eq.py`

每日处理流程：

1. 读取当日股票因子 `daily_feat`。
2. 读取当日行业分类 `daily_sector`。
3. 读取当日可交易状态 `daily_trd`。
4. 保留满足以下条件的股票：
   - 因子值非空；
   - 股票可交易；
   - 行业分类有效。
5. 对全市场有效股票因子做 MAD winsorize：
   - 中位数：`median`
   - MAD：`median(abs(x - median))`
   - 上下限：`median +/- 3 * 1.4826 * MAD`
6. 对 winsorize 后的因子做横截面标准化。
7. 在每个行业内对股票因子等权平均。
8. 把行业平均值回填给该行业内所有股票。

信号含义：

```text
行业因子值 = 行业内有效股票标准化因子的等权平均
```

适用场景：

- 作为基础基线。
- 衡量因子在行业层面的平均暴露。
- 避免单只大市值股票过度影响行业信号。

主要风险：

- 小市值股票和大市值股票权重相同，可能与真实行业指数权重有偏离。
- 行业内股票数量差异会影响行业信号稳定性。

### 3.2 市值加权聚合

实现文件：`dmgr_scripts/Dmgr_tlsector_cap.py`

每日处理流程：

1. 读取股票因子、行业分类、可交易状态和前一日市值。
2. 按行业收集有效股票。
3. 处理市值缺失。
4. 对市值进行可选变换。
5. 根据市值生成行业内股票权重。
6. 计算行业加权因子。
7. 对所有行业因子值做横截面标准化。
8. 将标准化行业值 clip 到 `[-3, 3]`。
9. 把行业值回填给该行业内所有股票。

支持的实验参数：

| 参数 | 取值 | 含义 |
| --- | --- | --- |
| `CAP_WEIGHT_MODE` | `cap_pct` | 行业内按市值占比加权。 |
| `CAP_WEIGHT_MODE` | `softmax` | 对行业内市值做 softmax 后加权。 |
| `CAP_NAN_MODE` | `drop` | 市值缺失股票剔除。 |
| `CAP_NAN_MODE` | `fill_sector_mean` | 市值缺失用行业均值填充，行业全缺失时用全市场均值回退。 |
| `CAP_TRANSFORM` | `none` | 不变换市值。 |
| `CAP_TRANSFORM` | `log1p` | 先做 `log(1 + cap)`，降低超大市值集中度。 |

信号含义：

```text
行业因子值 = sum(行业内股票因子 * 行业内股票市值权重)
```

适用场景：

- 更贴近真实行业指数或可配置行业组合。
- 希望行业信号由行业内核心权重股主导。
- 对比不同市值处理方式对行业轮动效果的影响。

主要风险：

- 原始市值占比可能让少数龙头股主导行业信号。
- softmax 对市值尺度敏感，使用前需要确认市值单位和分布。
- `log1p` 会降低大市值影响，但可能削弱有效信号。

## 4. 信号滞后与可交易性

`alpha_kchi.py` 中 Alpha 生成逻辑使用：

```python
self.alpha[valid_idx] = self.data[di - 1, valid_idx]
```

这意味着第 `di` 日交易使用第 `di-1` 日已经生成的行业信号，避免直接使用当日未来信息。

组合配置中默认：

```xml
delay="1"
tradePrice="close"
tax="0."
fee="0."
slippage="0."
```

解释：

- `delay=1`：信号滞后一日执行。
- `tradePrice=close`：按收盘价统计交易。
- 交易成本为 0：当前用于纯因子研究，不反映真实交易冲击。

后续若用于实盘或准实盘评估，应补充：

- 手续费；
- 印花税；
- 滑点；
- 行业 ETF 或行业成分股复制约束；
- 换手率约束；
- 最大行业偏离约束。

## 5. 回测体系

### 5.1 基础回测

入口：

```bash
python3 main.py
```

流程：

1. `init_env()` 创建 `configs/`、`logs/`、`pnls/`、`results/`。
2. `build_xml_all()` 生成 `cfg_all_factors.xml`。
3. `run_gsim()` 调用 Gsim 回测。
4. `run_summaries_and_sort()` 逐个 PnL 调 `simsummary.py`。
5. 输出 `factor_ranking.csv`。

基础统计模块：

```text
StatsSimple
```

输出字段：

| 字段 | 含义 |
| --- | --- |
| `factor_id` | 因子 ID。 |
| `sharpe` | Sharpe 比率。 |
| `ret_pct` | 年化收益率。 |
| `pnl_M` | 累计 PnL，单位百万。 |
| `max_dd` | 最大回撤。 |
| `win_rate` | 胜率。 |

### 5.2 StatsSimpleV5 多模式回测

入口：

```bash
python3 run_alltables_cap_stats_v5.py --all
```

支持模式：

| mode | 名称 | 含义 |
| --- | --- | --- |
| `0` | `long_short` | 标准多空。 |
| `1` | `excess_zz1000` | 相对中证1000超额收益。 |
| `2` | `top10_long_short` | Top10 分组多空。 |

用途：

- `mode=0` 看纯多空因子强弱。
- `mode=1` 看相对基准的行业配置价值。
- `mode=2` 看头部行业选择效果。

## 6. 实验设计

### 6.1 等权基线

目标：建立基础可比结果。

运行：

```bash
python3 main.py
```

产出：

```text
workspace_eq/results/factor_ranking.csv
```

比较重点：

- Sharpe 排名前 25 的因子。
- 正 Sharpe 因子数量。
- table1-10 各类因子的整体分布。

### 6.2 table1 聚合方式试验

目标：在小样本因子上快速比较聚合方式。

运行全部组合：

```bash
python3 run_table1_cap_trial.py --all
```

实验维度：

```text
2 个权重方式 x 2 个缺失处理 x 2 个市值变换 = 8 组
```

已有阶段结论：

| 方案 | 平均 Sharpe | 中位 Sharpe | Top5 均值 | Top10 均值 | Sharpe > 0 因子数 |
| --- | ---: | ---: | ---: | ---: | ---: |
| `cap_pct + drop` | 0.2415 | 0.1300 | 0.6820 | 0.4500 | 17 |
| `softmax + fill_sector_mean` | 0.3830 | 0.3700 | 0.6880 | 0.5970 | 19 |
| `log1p(cap) -> cap_pct + fill_sector_mean` | 0.1840 | 0.1500 | 0.6260 | 0.4400 | 14 |

阶段判断：

- `softmax + fill_sector_mean` 整体表现最好，适合作为全表试验优先方案。
- `cap_pct + drop` 对头部因子较友好，可保留为基线。
- `log1p(cap)` 降低大市值集中度，但在 table1 上收益表现较弱。

### 6.3 全表聚合方式试验

目标：把 table1 结论推广到 table1-10 全部 208 个因子。

运行：

```bash
python3 run_alltables_cap_trial.py --all
```

内置策略：

| 策略 | 权重方式 | 缺失处理 | 市值变换 |
| --- | --- | --- | --- |
| `cap_pct_drop` | `cap_pct` | `drop` | `none` |
| `softmax_fill` | `softmax` | `fill_sector_mean` | `none` |
| `log1p_cap_pct_fill` | `cap_pct` | `fill_sector_mean` | `log1p` |

产出：

```text
workspace_cap_all_cap_pct_drop/results/factor_ranking.csv
workspace_cap_all_softmax_fill/results/factor_ranking.csv
workspace_cap_all_log1p_cap_pct_fill/results/factor_ranking.csv
```

### 6.4 全表多统计模式试验

目标：同时比较聚合方式和组合统计模式。

运行：

```bash
python3 run_alltables_cap_stats_v5.py --all
```

任务矩阵：

```text
3 个聚合策略 x 3 个统计模式 = 9 组回测
```

产出：

```text
workspace_cap_all_{strategy}_m{mode}/results/factor_ranking.csv
```

## 7. 评价指标体系

单因子层面：

| 指标 | 解释 | 用途 |
| --- | --- | --- |
| Sharpe | 收益风险比 | 首要排序指标。 |
| 年化收益 | 策略收益强度 | 判断收益是否有经济意义。 |
| 最大回撤 | 极端亏损 | 过滤风险过大的因子。 |
| 胜率 | 盈利日期占比 | 判断收益稳定性。 |
| PnL | 累计盈亏 | 看长期累积效果。 |

因子组层面：

| 指标 | 解释 |
| --- | --- |
| 平均 Sharpe | 一组因子的整体表现。 |
| 中位 Sharpe | 降低极端因子影响。 |
| Top5/Top10 平均 Sharpe | 头部可选因子的强度。 |
| 正 Sharpe 因子数 | 有效因子覆盖率。 |
| 分 table 表现 | 判断因子类别差异。 |

建议的筛选标准：

1. Sharpe 排名前列。
2. 年化收益为正且不依赖单一年份。
3. 最大回撤可控。
4. 在不同统计模式下不明显失效。
5. 在不同聚合方式下方向稳定。
6. 同类因子不过度重复。

## 8. 结果组织规范

建议所有实验统一使用以下结构：

```text
workspace_{aggregation}_{scope}_{strategy}_m{mode}/
├── configs/
│   └── cfg_all_factors.xml
├── logs/
│   └── gsim_all.log
├── pnls/
│   ├── t1_CORR_VP
│   └── ...
└── results/
    └── factor_ranking.csv
```

命名建议：

| 字段 | 示例 | 含义 |
| --- | --- | --- |
| `aggregation` | `eq`、`cap` | 聚合类型。 |
| `scope` | `t1`、`all` | 因子范围。 |
| `strategy` | `softmax_fill` | 聚合策略。 |
| `mode` | `m0`、`m1`、`m2` | 统计模式。 |

## 9. 组合因子扩展

单因子筛选后，可以进一步构造组合因子。

当前项目提供 `run_combo_stats_v5.py`，用于回测一个已有 `combo.npy`。

组合因子构造建议：

1. 从单因子排名中筛选候选因子。
2. 去除高度相关或逻辑重复的因子。
3. 对因子方向统一。
4. 做横截面标准化。
5. 按等权、IC 加权、Sharpe 加权或稳健排名加权合成。
6. 重新回测组合因子。

组合因子评价重点：

- 是否高于单因子 Top 因子。
- 回撤是否降低。
- 年份间表现是否更平滑。
- 换手率是否可接受。
- 是否依赖某一类因子。

## 10. 风险控制与健壮性检查

### 10.1 数据检查

每次实验前应检查：

- 因子覆盖率；
- 每日有效股票数量；
- 每日有效行业数量；
- 行业分类是否缺失；
- 市值缺失比例；
- 极端值数量；
- 生成 `.npy` 文件数量是否等于因子数。

### 10.2 回测检查

每次实验后应检查：

- Gsim 是否正常结束；
- `pnls/` 文件数量是否等于 Alpha 数量；
- `factor_ranking.csv` 是否非空；
- simsummary 解析字段是否错位；
- Top 因子是否有异常极端 PnL；
- 多个 workspace 是否混用缓存。

### 10.3 防止缓存串扰

市值加权实验会通过不同 `AUTHOR` 和 `WORKSPACE` 隔离缓存。

运行批量实验时，默认应清理对应 `dm_data/{author}_tlsector_cap/` 下的旧 `.npy` 文件。只有确认参数完全一致时才使用 `--keep-cache`。

## 11. 推荐研究流程

第一步：跑等权基线。

```bash
python3 main.py
```

第二步：在 table1 上比较聚合方式。

```bash
python3 run_table1_cap_trial.py --all
```

第三步：选择候选聚合方式，跑全表。

```bash
python3 run_alltables_cap_trial.py --all
```

第四步：用 `StatsSimpleV5` 做多口径评估。

```bash
python3 run_alltables_cap_stats_v5.py --all
```

第五步：汇总各 workspace 的 `factor_ranking.csv`，比较：

- 聚合方式；
- 统计模式；
- 因子表来源；
- 正收益覆盖；
- Top 因子重合度。

第六步：构造组合因子并回测。

```bash
python3 run_combo_stats_v5.py --all --combo-npy <combo.npy路径>
```

## 12. 当前项目状态说明

当前仓库上传到 GitHub 的内容包括：

- 源代码；
- 项目说明；
- 数据目录说明；
- 行业轮动测算体系文档。

以下内容不上传：

- `dm_data/` 下的大型 `.npy` 缓存；
- `workspace*/` 下的回测产物；
- Python 编译缓存。

原因：

- `.npy` 文件体量很大，单文件约百 MB 级；
- workspace 结果依赖本地 Gsim 环境；
- 这些文件可以通过脚本重新生成；
- GitHub 普通仓库不适合存放大规模二进制研究缓存。

## 13. 后续优化方向

建议后续补充：

1. 自动汇总多个 `factor_ranking.csv` 的比较脚本。
2. 因子相关性分析和去冗余模块。
3. 分年度、分市场环境、分行业数量的稳定性报表。
4. 交易成本和换手约束。
5. 行业 ETF 或行业指数成分复制方案。
6. 组合因子自动构建流程。
7. HTML 或 notebook 形式的研究报告输出。
8. 大文件使用 Git LFS 或对象存储统一管理。

