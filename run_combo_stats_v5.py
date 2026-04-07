import argparse
import os
import subprocess
import shutil

from config import ProjectConfig


COMBO_NPY = (
    "/home/wangpy/sectorfeature/sectorfeature/"
    "dm_data/kchi_all_log1p_cap_pct_fill_tlsector_cap/combo.npy"
)

MODES = {
    0: "long_short",
    1: "excess_zz1000",
    2: "top10_long_short",
}


def _log(msg):
    print(msg, flush=True)


def _init_env(workspace):
    for sub in ["configs", "logs", "pnls", "results"]:
        path = os.path.join(workspace, sub)
        if os.path.exists(path) and sub == "configs":
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)


def _build_xml(workspace, mode, combo_npy):
    pnl_dir = os.path.join(workspace, "pnls")
    alpha_script = ProjectConfig.ALPHA_SCRIPT

    xml_content = f'''<gsim>
  <Constants backdays="256" niodatapath="/datasvc/data/cc/" niomapprivate="true" authorWeight="combo_v5:1.0," time_intensive="false"/>
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

    <Data id="Basedata" module="/usr/local/gsim/source_ref/base_data_2026.py" rawpricePath="/datasvc/rawdata/rawprice" industryPath="/datasvc/rawdata/AShareWindIndustry/" ST="/datasvc/rawdata/AShareST" path="" niomapprivate="true"/>
    <Data id="ipo" module="/usr/local/gsim/gsim/data/module/ipo.py" dataPath="/datasvc/rawdata/secID" path="" niomapprivate="true"/>
    <Data id="PriceLimit" module="/usr/local/gsim/gsim/data/module/price_limit.py" dataPath="/datasvc/rawdata/pricelimit" niomapprivate="true"/>
    <Data id="adjfactor" module="DmgrAdjfactor" dataPath="/datasvc/rawdata/adjfactor" niomapprivate="true" path=""/>
    <Data id="ashareeodprices" module="Dmgrashareeodprices" dataPath="/datasvc/rawdata/ashareeodprices/" niomapprivate="true"/>
    <Data id="adjprice" module="DmgrAdjprice" niomapprivate="true" path=""/>
    <Data id="AShareMoneyFlow" module="DmgrAShareMoneyFlow" dataPath="/datasvc/rawdata/AShareMoneyFlow/" niomapprivate="true"/>
    <Alpha id="AlphaMod" module="{alpha_script}"/>
  </Modules>

  <Portfolio id="ComboPort" booksize="20e6" homecurrency="CNY">
    <Stats module="StatsSimpleV5" mode="{mode}" index_ret="aindexeodprices.s_dq_pctchange_000852" thres="90" tradePrice="close" tax="0." fee="0." slippage="0." printStats="true" dumpPnl="true" pnlDir="{pnl_dir}"/>
    <Alpha id="combo" module="AlphaMod" npydata="{combo_npy}" universeId="ALL_TRD" booksize="20e6" delay="1" ndays="20" dumpAlphaFile="false" dumpAlphaDir="alpha" st="20">
      <Description name="combo" author="combo_v5" birthday="20240101" category="factor" universe="ALL_TRD" delay="1"/>
      <Operations>
        <Operation module="AlphaOpPower" exp="1.0"/>
      </Operations>
    </Alpha>
  </Portfolio>
</gsim>
'''
    xml_path = os.path.join(workspace, "configs", "cfg_combo.xml")
    with open(xml_path, "w") as f:
        f.write(xml_content)
    return xml_path


def _run_summary(workspace):
    pnl_file = os.path.join(workspace, "pnls", "combo")
    out_csv = os.path.join(workspace, "results", "combo_summary.csv")
    res = subprocess.run(
        [ProjectConfig.PYTHON_BIN, ProjectConfig.GSIM_SUMMARY_SCRIPT, pnl_file],
        capture_output=True,
        text=True,
    )
    with open(out_csv, "w") as f:
        f.write(res.stdout)
    return out_csv


def run_one(mode, combo_npy):
    workspace = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        f"workspace_combo_log1p_cap_pct_fill_m{mode}",
    )
    _log("=" * 72)
    _log(f"开始 combo 回测: mode={mode}({MODES[mode]})")
    _log(f"COMBO_NPY={combo_npy}")
    _log(f"WORKSPACE={workspace}")
    _log("=" * 72)

    _init_env(workspace)
    xml_path = _build_xml(workspace, mode, combo_npy)
    log_path = os.path.join(workspace, "logs", "gsim_combo.log")

    with open(log_path, "w") as f_log:
        proc = subprocess.Popen(
            [ProjectConfig.PYTHON_BIN, ProjectConfig.GSIM_RUN_SCRIPT, xml_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:
            f_log.write(line)
            f_log.flush()
            print(line, end="", flush=True)
        proc.wait()

    if proc.returncode != 0:
        raise SystemExit(proc.returncode)

    summary_csv = _run_summary(workspace)
    _log(f"[mode={mode}] 完成: {summary_csv}")


def main():
    parser = argparse.ArgumentParser(description="Backtest combo.npy with StatsSimpleV5 mode 0/1/2.")
    parser.add_argument(
        "--mode",
        type=int,
        choices=[0, 1, 2],
        help="Run one mode only.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all 3 modes sequentially.",
    )
    parser.add_argument(
        "--combo-npy",
        default=COMBO_NPY,
        help="Path to combo raw binary matrix file.",
    )
    args = parser.parse_args()

    if args.all:
        for mode in [0, 1, 2]:
            run_one(mode, args.combo_npy)
        return

    if args.mode is not None:
        run_one(args.mode, args.combo_npy)
        return

    parser.error("请使用 --all 或 --mode")


if __name__ == "__main__":
    main()
