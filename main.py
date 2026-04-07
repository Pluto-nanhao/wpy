import os
import subprocess
import shutil
from config import ProjectConfig, ALPHA_LIST

def _log(msg, flush=True):
    """打印并立即刷新，确保终端能看到"""
    print(msg, flush=flush)

def init_env():
    sub_dirs = ['configs', 'logs', 'pnls', 'results']
    for sub in sub_dirs:
        path = os.path.join(ProjectConfig.WORKSPACE, sub)
        if os.path.exists(path) and sub == 'configs':
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
    _log(f"Environment initialized at: {ProjectConfig.WORKSPACE}")

def get_alpha_path(alpha_name):
    file_name = f"{ProjectConfig.AUTHOR}_{ProjectConfig.USED_SCRIPT}.tl_{alpha_name.lower()}.npy"
    return os.path.join(ProjectConfig.DATA_ROOT, f"{ProjectConfig.AUTHOR}_{ProjectConfig.USED_SCRIPT}", file_name)

def _table_data_modules():
    """生成 table1-10 的 Data 模块 XML"""
    lines = []
    for i in range(1, 11):
        lines.append(
            f'\t\t<Data id="equ_fancy_factors_table{i}" '
            f'module="/usr/local/gsim/source_ref/Dmgr_equ_fancy_factors_table{i}.py" '
            f'dataPath="/datasvc/rawdata/equ_fancy_factors_table{i}" niomapprivate="true"/>'
        )
    return '\n'.join(lines)


def _stats_xml(pnl_dir):
    """按 ProjectConfig 生成 Stats XML。"""
    if ProjectConfig.STATS_MODULE == "StatsSimpleV5":
        thres_attr = ""
        if ProjectConfig.STATS_THRES is not None:
            thres_attr = f'thres="{ProjectConfig.STATS_THRES}" '
        return (
            f'<Stats module="StatsSimpleV5" mode="{ProjectConfig.STATS_MODE}" '
            f'index_ret="{ProjectConfig.STATS_INDEX_RET_FIELD}" '
            f'{thres_attr}'
            f'tradePrice="close" tax="0." fee="0." slippage="0." '
            f'printStats="true" dumpPnl="true" pnlDir="{pnl_dir}"/>'
        )
    return (
        f'<Stats module="StatsSimple" tradePrice="close" tax="0." fee="0." '
        f'slippage="0." printStats="true" dumpPnl="true" pnlDir="{pnl_dir}"/>'
    )

def build_xml_all():
    """构建包含全部 208 个 Alpha 的单一 XML"""
    dmgr_path = os.path.join(ProjectConfig.SCRIPTS_DIR, f"Dmgr_{ProjectConfig.USED_SCRIPT}.py")
    alpha_script = ProjectConfig.ALPHA_SCRIPT
    pnl_dir = os.path.join(ProjectConfig.WORKSPACE, "pnls")

    alpha_blocks = []
    for alpha_id in ALPHA_LIST:
        npy_path = get_alpha_path(alpha_id)
        alpha_blocks.append(f'''
    <Alpha id="{alpha_id}" module="AlphaMod" npydata="{npy_path}" universeId="ALL_TRD" booksize="20e6" delay="1" ndays="20" dumpAlphaFile="false" dumpAlphaDir="alpha" st="20">
      <Description name="{alpha_id}" author="{ProjectConfig.AUTHOR}" birthday="20240101" category="factor" universe="ALL_TRD" delay="1"/>
      <Operations>
        <Operation module="AlphaOpPower" exp="1.0"/>
      </Operations>
    </Alpha>''')

    table_modules = _table_data_modules()
    stats_xml = _stats_xml(pnl_dir)

    xml_content = f'''<gsim>
  <Constants backdays="256" niodatapath="/datasvc/data/cc/" niomapprivate="true" authorWeight="{ProjectConfig.AUTHOR}:1.0," time_intensive="false"/>
  <Universe startdate="{ProjectConfig.START_DATE}" enddate="{ProjectConfig.END_DATE}" secID="/datasvc/rawdata/secID" holidaysfile="/datasvc/rawdata/holidays" calendarfile="/datasvc/rawdata/wind_calendar.csv"/>

  <Modules>
    <Data id="FULL" module="/usr/local/gsim/gsim/data/module/umgr_full.py" path="" niomapprivate="true"/>
    <Data id="ALL" module="UmgrAll" path="" niomapprivate="true"/>
    <Data id="ALL_TRD" module="UmgrTrd" path="" niomapprivate="true"/>
    <Data id="ALL_GIM" module="/usr/local/gsim/gsim/data/module/umgr_gim.py" path="" niomapprivate="true"/>

    <Data id="HS300" module="/usr/local/gsim/source_ref/umgr_index.py" dataPath="/datasvc/rawdata/HS300/" niomapprivate="true"/>
    <Data id="ZZ500" module="/usr/local/gsim/source_ref/umgr_index.py" dataPath="/datasvc/rawdata/ZZ500/" niomapprivate="true"/>
    <Data id="ZZ1000" module="/usr/local/gsim/source_ref/umgr_index.py" dataPath="/datasvc/rawdata/ZZ1000/" niomapprivate="true"/>
    <Data id="aindexeodprices" module="Dmgraindexeodprices" dataPath="/datasvc/rawdata/aindexeodprices/" niomapprivate="true"/>

    {table_modules}

    <Data id="Basedata" module="/usr/local/gsim/source_ref/base_data_2026.py" rawpricePath="/datasvc/rawdata/rawprice" industryPath="/datasvc/rawdata/AShareWindIndustry/" ST="/datasvc/rawdata/AShareST" path="" niomapprivate="true"/>

    <Data id="ipo" module="/usr/local/gsim/gsim/data/module/ipo.py" dataPath="/datasvc/rawdata/secID" path="" niomapprivate="true"/>
    <Data id="PriceLimit" module="/usr/local/gsim/gsim/data/module/price_limit.py" dataPath="/datasvc/rawdata/pricelimit" niomapprivate="true"/>
    <Data id="adjfactor" module="DmgrAdjfactor" dataPath="/datasvc/rawdata/adjfactor" niomapprivate="true" path=""/>
    <Data id="ashareeodprices" module="Dmgrashareeodprices" dataPath="/datasvc/rawdata/ashareeodprices/" niomapprivate="true"/>
    <Data id="adjprice" module="DmgrAdjprice" niomapprivate="true" path=""/>
    <Data id="AShareMoneyFlow" module="DmgrAShareMoneyFlow" dataPath="/datasvc/rawdata/AShareMoneyFlow/" niomapprivate="true"/>

    <Data id="{ProjectConfig.AUTHOR}_{ProjectConfig.USED_SCRIPT}" module="{dmgr_path}" niodatapath="{ProjectConfig.DATA_ROOT}" niomapprivate="false"/>
    <Alpha id="AlphaMod" module="{alpha_script}"/>
  </Modules>

  <Portfolio id="MyPort" booksize="20e6" homecurrency="CNY">
    {stats_xml}
    {''.join(alpha_blocks)}
  </Portfolio>
</gsim>
'''
    xml_path = os.path.join(ProjectConfig.WORKSPACE, "configs", "cfg_all_factors.xml")
    os.makedirs(os.path.dirname(xml_path), exist_ok=True)
    with open(xml_path, "w") as f:
        f.write(xml_content)
    return xml_path

def run_gsim():
    """运行 Gsim 回测（一次运行全部 208 个因子），输出同时写入日志和终端"""
    _log(">>> 构建 XML 配置...")
    xml_path = build_xml_all()
    _log(f"    XML 已生成: {xml_path}")
    log_path = os.path.join(ProjectConfig.WORKSPACE, "logs", "gsim_all.log")
    _log(
        f">>> Running Gsim (208 factors, "
        f"{ProjectConfig.STATS_MODULE}, mode={ProjectConfig.STATS_MODE})... 日志: {log_path}"
    )
    with open(log_path, 'w') as f_log:
        proc = subprocess.Popen(
            [ProjectConfig.PYTHON_BIN, ProjectConfig.GSIM_RUN_SCRIPT, xml_path],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        for line in proc.stdout:
            f_log.write(line)
            f_log.flush()
            print(line, end='', flush=True)
        proc.wait()
    if proc.returncode != 0:
        _log(f"FAILED (exit={proc.returncode}). 详情见: {log_path}")
        return False
    _log("SUCCESS: Gsim completed.")
    return True

def run_summaries_and_sort():
    """对每个 PnL 运行 simsummary，解析结果并按 Sharpe 排序"""
    pnl_dir = os.path.join(ProjectConfig.WORKSPACE, "pnls")
    results_dir = os.path.join(ProjectConfig.WORKSPACE, "results")
    csv_path = os.path.join(ProjectConfig.WORKSPACE, "results", "factor_ranking.csv")

    _log(f">>> 正在对 {len(ALPHA_LIST)} 个因子运行 simsummary...")
    rows = []
    for i, alpha_id in enumerate(ALPHA_LIST):
        if (i + 1) % 50 == 0 or i == 0:
            _log(f"  simsummary 进度: {i+1}/{len(ALPHA_LIST)}")
        pnl_file = os.path.join(pnl_dir, alpha_id)
        if not os.path.isfile(pnl_file):
            continue
        res = subprocess.run(
            [ProjectConfig.PYTHON_BIN, ProjectConfig.GSIM_SUMMARY_SCRIPT, pnl_file],
            capture_output=True, text=True
        )
        out = res.stdout.strip()
        if not out:
            continue
        lines = [l for l in out.strip().split('\n') if l.strip()]
        if not lines:
            continue
        last_line = lines[-1]
        # 格式: dates long short pnl %ret %tvr sharpe(IR) %dd %win fitness ddStart ddEnd
        # 注意: sharpe(IR) 列格式不固定，正数 "0.30( 0.02)" 有空格(13列)，负数 "-0.92(-0.06)" 无空格(12列)
        parts = last_line.split()
        if len(parts) < 10:
            continue
        # sharpe: 找含 "(" 的 token 并提取数字
        sharpe_f = 0.0
        for p in parts:
            if '(' in p:
                try:
                    sharpe_f = float(p.split('(')[0])
                except ValueError:
                    pass
                break
        # pnl, ret 固定在前列
        pnl_m = parts[3] if len(parts) > 3 else "0"
        ret = parts[4] if len(parts) > 4 else "0"
        # %dd %win 从右往左固定: ... %dd %win fitness ddStart ddEnd
        dd = parts[-5] if len(parts) >= 5 else "0"
        win = parts[-4] if len(parts) >= 4 else "0"
        rows.append((alpha_id, sharpe_f, ret, pnl_m, dd, win))

    rows.sort(key=lambda x: x[1], reverse=True)

    with open(csv_path, 'w') as f:
        f.write("factor_id,sharpe,ret_pct,pnl_M,max_dd,win_rate\n")
        for r in rows:
            f.write(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}\n")

    _log(f"\n=== 因子收益排序 (按 Sharpe) Top 25 ===")
    _log("factor_id,sharpe,ret_pct,pnl_M,max_dd,win_rate")
    for r in rows[:25]:
        _log(f"{r[0]},{r[1]},{r[2]},{r[3]},{r[4]},{r[5]}")
    _log(f"\n完整结果已保存至: {csv_path}")
    return csv_path

if __name__ == "__main__":
    _log("=" * 50)
    _log("sectorfeature 启动")
    init_env()
    _log(f"共 {len(ALPHA_LIST)} 个因子 (table1-10)")
    _log("=" * 50)
    if not run_gsim():
        exit(1)
    _log("=" * 50)
    run_summaries_and_sort()
    _log("\n" + "=" * 50)
    _log("全部完成")
