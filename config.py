import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class ProjectConfig:
    WORKSPACE = os.path.join(BASE_DIR, "workspace_eq")
    SCRIPTS_DIR = os.path.join(BASE_DIR, "dmgr_scripts")
    ALPHA_SCRIPT = os.path.join(BASE_DIR, "alpha_kchi.py")
    DATA_ROOT = os.path.abspath(os.path.join(BASE_DIR, "dm_data"))
    USED_SCRIPT = "tlsector_eq"
    AUTHOR = "kchi"
    
    PYTHON_BIN = "/usr/local/gsim/.venv/bin/python"
    GSIM_RUN_SCRIPT = "/usr/local/gsim/run.py"
    GSIM_SUMMARY_SCRIPT = "/usr/local/gsim/tools/simsummary.py"
    
    START_DATE = "20110101"
    END_DATE = "20251231"

    # 回测统计模块配置
    # - StatsSimple: 传统多空统计
    # - StatsSimpleV5: 支持 mode=0/1/2
    STATS_MODULE = "StatsSimple"
    STATS_MODE = 0
    # mode=1（相对基准超额）时用到的指数收益字段
    STATS_INDEX_RET_FIELD = "aindexeodprices.s_dq_pctchange_000852"
    # 可选阈值参数（部分 Stats 模块会读取）
    STATS_THRES = 90


# 通联 table1-10 全部因子: {table_id: [factor_names]}
TABLE_FACTORS = {
    1: [
        "APB_SKEW", "ASHAREHOLDER_Z", "CORR_VP", "LPNP_Q", "NP_Q_YOY",
        "NP_TTM_QOQ", "NP_TTM_YOY", "NP_YTD_YOY", "OCFA", "REV_Q_YOY",
        "REV_TTM_QOQ", "REV_TTM_YOY", "REV_YTD_YOY", "RROC_Q", "SUDE",
        "SUDREV", "TA_ENTROPY", "UDSL_DWL", "UDSL", "UDSL_UCL",
    ],
    2: [
        "ROE_Q", "ROE_TTM", "ROE_Q_YOYD", "ROE_TTM_QOQD", "ROE_TTM_YOYD",
        "DTOP", "DIV_PAIDRATIO", "Q_ETOP", "Q_STOP", "D_Q_ETOP", "D_Q_STOP",
        "AI_SUDE", "CON_SUDE", "AI_SUDREV", "CON_SUDREV", "AI_NP_YOY", "AI_REV_YOY",
        "CON_NP_YOY", "CON_REV_YOY", "AI_ETOP",
    ],
    3: [
        "AI_ETOP_Z90", "AI_ETOP_Z180", "CON_DA_PE_20", "CON_DA_PE_40", "CON_DA_PE_60",
        "CON_DA_PS_20", "CON_DA_PS_40", "CON_DA_PS_60", "AST_DA12_ETOP", "AST_RANK_UPPCT",
        "AST_PROFIT_UPPCT", "GSA", "HK_HOLDRATIO_ALL", "HK_HOLDRATIO_B", "HK_HOLDRATIO_C",
        "FUND_TOP10_COUNT", "FUND_TOP10_WEIGHT_MEAN", "FUND_TOP10_WEIGHT_MAX",
        "FUND_TOP10_NEGVALUE_PCT", "NAIVE_WEIGHT_CHANGE_ASYM",
    ],
    4: [
        "FUND_TOP10_CHG_WEIGHT", "FUND_TOP10_CHG_VALUERAITO", "P_REPORT_DATE", "P_REPORT_DIFF",
        "HK_HOLDVOL_CHG_B20", "HK_HOLDVOL_CHG_C20", "HK_HOLDVOL_CHG_ALL20",
        "HK_HOLDVOL_CHG_B60", "HK_HOLDVOL_CHG_C60", "HK_HOLDVOL_CHG_ALL60",
        "HK_HOLDVOL_CHG_B120", "HK_HOLDVOL_CHG_C120", "HK_HOLDVOL_CHG_ALL120",
        "AI_DA_NP_30", "AI_DA_NP_60", "AI_DA_NP_90", "AI_DA_REV_30", "AI_DA_REV_60", "AI_DA_REV_90",
        "AI_DA_PE_30",
    ],
    5: [
        "AI_DA_PE_60", "AI_DA_PE_90", "AI_DA_PS_30", "AI_DA_PS_60", "AI_DA_PS_90",
        "AST_RPT_SENTIMENT_W", "AST_RPT_SENTIMENT_Z180", "AST_RPT_SENTIMENT_Z365", "AST_RPT_SENTIMENT_Z730",
        "FMZL_1Y_IPCNUM_SUM", "FMZL_1Y_RELATEDNUM_SUM", "FMZL_1Y_OWNPARENT_SUM",
        "FMZL_1Y_REVIEWDAY_SUM", "FMZL_1Y_RELATEDNUM_MAX", "BCVP_05M_20D", "OCVP_05M_20D",
        "CORR_VPL_05M_20D", "UPP_01M_20D", "DDP_01M_20D", "VOLL_01M_20D",
    ],
    6: [
        "FF3R2_20", "FF3SPMOM_20", "FF3SPVOL_20", "FF3SYSMOM_20", "FF3SYSVOL_20",
        "RMVOL_20", "RMVOL_60", "RMVOL_120", "TRVOL_20", "TRVOL_60", "TRVOL_120", "TRVOV",
        "MINTVAL_QUA_20D", "MINTVAL_SKEW_20D", "MINTVAL_MTS_20D", "MINTVAL_MTE_20D",
        "SECTVAL_KURT_20D", "OVAL_MBSR_20D", "GMM_MEAN_1M_20D", "GMM_DMEAN_1M_20D",
    ],
    7: [
        "FUND_TRACTION_20", "FUND_TRACTION_60", "SUR_EVENT", "SUR_INST",
        "GB_POST_NUM_30", "GB_POST_NUM_60", "GB_POST_NUM_90", "GB_POST_NUM_DA30",
        "T_ACCR_IS", "D_ACCR_IS", "T_ACCR_BS", "D_ACCR_BS", "NP_Q_ACC", "REV_Q_ACC",
        "NP_Q_SD", "OP_Q_SD", "REV_Q_SD", "ROIC_Q", "CFOA_Q", "PROFIT_TREND", "AT_TTM_QOQD",
    ],
    8: [
        "CCR_Q", "TOE_TTM_STD", "CFP_TTM_STD", "GOVERNANCE", "PROFIT_QQC", "GROWTH_QQC",
        "OPERATION_QQC", "Q_SCORE", "CON_DTOP", "CON_DTOP_Z90", "CON_DTOP_Z180",
        "CON_DTOP_DA30", "CON_DTOP_DA90", "CON_DPR", "AI_DTOP", "AI_DTOP_Z90", "AI_DTOP_Z180",
        "AI_DTOP_DA30", "AI_DTOP_DA90", "AI_DPR", "QES",
    ],
    9: [
        "NEWS_NUM_30", "NEWS_NUM_NEG_30", "NEWS_NUM_VOL_30", "NEWS_NUM_POS_VOL_30", "NEWS_NUM_VOL_LT",
        "GTRA_BUY_HOT", "GTRA_BUY_HOT_CHG", "GTRA_SELL_HOT_CHG", "GTRA_BUY_PCT", "GTRA_SELL_PCT",
        "GTRA_BUY_PCT_VOL", "GTRA_SELL_PCT_VOL", "XTRA_BUY_HOT", "XTRA_BUY_HOT_CHG", "XTRA_SELL_HOT_CHG",
        "XTRA_BUY_PCT", "XTRA_SELL_PCT", "XTRA_BUY_PCT_VOL", "XTRA_SELL_PCT_VOL",
        "GPOST_HOT", "GPOST_POS_PCT_VOL", "GPOST_NEG_PCT_VOL",
    ],
    10: [
        "GR_PE_TTM", "GR_PE_Q", "GR_PB", "GR_PCF_TTM", "GR_PCF_Q", "GR_PS_TTM", "GR_PS_Q",
        "DEP_ABR_RATIO", "TRANS_RATIO", "CREDIT_DEBT_RATIO", "FOREX_RATIO", "STATIC_NOTE_RATIO",
        "ABS_GPG_Q", "ABS_INVG", "KCI", "DTOA_YOYD", "IT_Q_YOYD", "IT_TTM_QOQD",
        "ART_Q_YOYD", "FAT_Q_YOYD", "FAT_TTM_QOQD", "OPER_L_YOY", "OPER_L_QOQ", "OPER_LR_YOYD",
    ],
}


def _build_alpha_list():
    """构建 ALPHA_LIST: ['t1_APB_SKEW', 't2_ROE_Q', ...]"""
    out = []
    for tid, factors in TABLE_FACTORS.items():
        for f in factors:
            out.append(f"t{tid}_{f}")
    return out


# 全部 208 个因子
ALPHA_LIST = _build_alpha_list()

# Dmgr 用: [(table_num, factor_name), ...]
FACTOR_TABLE_LIST = [
    (tid, f) for tid, factors in TABLE_FACTORS.items() for f in factors
]
