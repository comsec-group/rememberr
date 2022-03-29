# This file provides common functions and data structures.

import json
import os
import re

triggers = [
    "trg_CFG_pag",
    "trg_CFG_vmc",
    "trg_CFG_wrg",
    "trg_EXT_bus",
    "trg_EXT_iom",
    "trg_EXT_pci",
    "trg_EXT_ram",
    "trg_EXT_rst",
    "trg_EXT_usb",
    "trg_FEA_cid",
    "trg_FEA_cus",
    "trg_FEA_dbg",
    "trg_FEA_fpu",
    "trg_FEA_mon",
    "trg_FEA_tra",
    "trg_FLT_mca",
    "trg_FLT_ovf",
    "trg_FLT_swf",
    "trg_FLT_tmr",
    "trg_MBR_cbr",
    "trg_MBR_mbr",
    "trg_MBR_pbr",
    "trg_MOP_atp",
    "trg_MOP_fen",
    "trg_MOP_flc",
    "trg_MOP_mmp",
    "trg_MOP_nst",
    "trg_MOP_ptw",
    "trg_MOP_seg",
    "trg_MOP_spe",
    "trg_POW_pwc",
    "trg_POW_tht",
    "trg_PRV_ret",
    "trg_PRV_vmt",
]

contexts = [
    "ctx_FEA_sec",
    "ctx_CFG_sgc",
    "ctx_PHY_pkg",
    "ctx_PHY_tmp",
    "ctx_PHY_vol",
    "ctx_PRV_boo",
    "ctx_PRV_smm",
    "ctx_PRV_vmg",
    "ctx_PRV_vmh",
]

effects = [
    "eff_CRP_prf",
    "eff_CRP_reg",
    "eff_EXT_mmd",
    "eff_EXT_pci",
    "eff_EXT_ram",
    "eff_EXT_usb",
    "eff_FLT_fid",
    "eff_FLT_fms",
    "eff_FLT_fsp",
    "eff_FLT_mca",
    "eff_FLT_unc",
    "eff_HNG_boo",
    "eff_HNG_crh",
    "eff_HNG_hng",
    "eff_HNG_unp",
]

intel_cpu_prettynames = {
    "intel_core_1_desktop": "Core 1 (D)",
    "intel_core_1_mobile":  "Core 1 (M)",
    "intel_core_2_desktop": "Core 2 (D)",
    "intel_core_2_mobile":  "Core 2 (M)",
    "intel_core_3_desktop": "Core 3 (D)",
    "intel_core_3_mobile":  "Core 3 (M)",
    "intel_core_4_desktop": "Core 4 (D)",
    "intel_core_4_mobile":  "Core 4 (M)",
    "intel_core_5_desktop": "Core 5 (D)",
    "intel_core_5_mobile":  "Core 5 (M)",
    "intel_core_6":         "Core 6",
    "intel_core_7_8":       "Core 7-8",
    "intel_core_8_9":       "Core 8-9",
    "intel_core_10":        "Core 10",
    "intel_core_11":        "Core 11",
    "intel_core_12":        "Core 12",
}
intel_cpu_names = list(intel_cpu_prettynames.keys())

amd_cpu_prettynames = {
    "amd_10h":    "Family 10h",
    "amd_11h":    "Family 11h",
    "amd_12h":    "Family 12h",
    "amd_14h":    "Family 14h",
    "amd_15h_00": "Family 15h-0",
    "amd_15h_10": "Family 15h-1",
    "amd_15h_30": "Family 15h-3",
    "amd_15h_70": "Family 15h-7",
    "amd_16h_00": "Family 16h-0",
    "amd_16h_30": "Family 16h-3",
    "amd_17h_00": "Family 17h-0",
    "amd_17h_30": "Family 17h-3",
    "amd_19h":    "Family 19h",
}
amd_cpu_names = list(amd_cpu_prettynames.keys())

amd_cpu_prettynames_abbrev = {
    "amd_10h":    "Fam. 10h",
    "amd_11h":    "Fam. 11h",
    "amd_12h":    "Fam. 12h",
    "amd_14h":    "Fam. 14h",
    "amd_15h_00": "Fam. 15h-0",
    "amd_15h_10": "Fam. 15h-1",
    "amd_15h_30": "Fam. 15h-3",
    "amd_15h_70": "Fam. 15h-7",
    "amd_16h_00": "Fam. 16h-0",
    "amd_16h_30": "Fam. 16h-3",
    "amd_17h_00": "Fam. 17h-0",
    "amd_17h_30": "Fam. 17h-3",
    "amd_19h":    "Fam. 19h",
}
assert(set(amd_cpu_prettynames.keys()) == set(amd_cpu_prettynames_abbrev.keys()))

# Pages where the errata details are provided.
# Both bounds are included.
# This data was collected manually.
details_pages = {
    "intel_core_1_desktop": (20, 65),
    "intel_core_1_mobile":  (23, 59),
    "intel_core_2_desktop": (21, 63),
    "intel_core_2_mobile":  (22, 58),
    "intel_core_3_desktop": (22, 54),
    "intel_core_3_mobile":  (22, 55),
    "intel_core_4_desktop": (23, 64),
    "intel_core_4_mobile":  (24, 71),
    "intel_core_5_desktop": (16, 46),
    "intel_core_5_mobile":  (18, 51),
    "intel_core_6":         (29, 85),
    "intel_core_7_8":       (26, 65),
    "intel_core_8_9":       (20, 58),
    "intel_core_10":        (20, 60),
    "intel_core_11":        (12, 19),
    "intel_core_12":        (14, 23),
    "amd_10h":              (44, 146),
    "amd_11h":              (17, 36),
    "amd_12h":              (23, 52),
    "amd_14h":              (23, 71),
    "amd_15h_00":           (24, 94),
    "amd_15h_10":           (20, 63),
    "amd_15h_30":           (16, 25),
    "amd_15h_70":           (15, 27),
    "amd_16h_00":           (16, 36),
    "amd_16h_30":           (15, 33),
    "amd_17h_00":           (18, 63),
    "amd_17h_30":           (16, 46),
    "amd_19h":              (17, 66),
}


cpu_prefixes = {
    "intel_core_1_desktop": "AAJ",
    "intel_core_1_mobile":  "AAT",
    "intel_core_2_desktop": "BJ",
    "intel_core_2_mobile":  "BK",
    "intel_core_3_desktop": "BV",
    "intel_core_3_mobile":  "BU",
    "intel_core_4_desktop": "HSD",
    "intel_core_4_mobile":  "HSM",
    "intel_core_5_desktop": "BDD",
    "intel_core_5_mobile":  "BDM",
    "intel_core_6":         "SKL",
    "intel_core_7_8":       "KBL",
    "intel_core_8_9":       "",
    "intel_core_10":        "CML",
    "intel_core_11":        "RKL",
    "intel_core_12":        "ADL",
}
assert(set(intel_cpu_prettynames.keys()) == set(cpu_prefixes.keys()))

trigger_classes_map = {
    "trg_CFG_pag": "trg_CFG",
    "trg_EXT_bus": "trg_EXT",
    "trg_EXT_iom": "trg_EXT",
    "trg_EXT_pci": "trg_EXT",
    "trg_EXT_ram": "trg_EXT",
    "trg_EXT_rst": "trg_EXT",
    "trg_EXT_usb": "trg_EXT",
    "trg_FEA_cus": "trg_FEA",
    "trg_FEA_dbg": "trg_FEA",
    "trg_FEA_fpu": "trg_FEA",
    "trg_FLT_ill": "trg_FLT",
    "trg_FLT_ovf": "trg_FLT",
    "trg_FLT_tmr": "trg_FLT",
    "trg_MBR_cbr": "trg_MBR",
    "trg_MBR_mbr": "trg_MBR",
    "trg_MBR_pbr": "trg_MBR",
    "trg_MOP_atp": "trg_MOP",
    "trg_MOP_fen": "trg_MOP",
    "trg_MOP_flc": "trg_MOP",
    "trg_MOP_mmp": "trg_MOP",
    "trg_MOP_nst": "trg_MOP",
    "trg_MOP_ptw": "trg_MOP",
    "trg_MOP_seg": "trg_MOP",
    "trg_POW_pwc": "trg_POW",
    "trg_PRV_ret": "trg_PRV",
    "trg_PRV_vmt": "trg_PRV",
    "trg_FLT_mca": "trg_FLT",
    "trg_FEA_mon": "trg_FEA",
    "trg_POW_tht": "trg_POW",
    "trg_CFG_vmc": "trg_CFG",
    "trg_FLT_swf": "trg_FLT",
    "trg_FEA_tra": "trg_FEA",
    "trg_CFG_wrg": "trg_CFG",
    "trg_FEA_cid": "trg_FEA",
    "trg_MOP_spe": "trg_MOP",
}

trigger_classes = [
    'trg_MBR',
    'trg_MOP',
    'trg_FLT',
    'trg_PRV',
    'trg_CFG',
    'trg_POW',
    'trg_EXT',
    'trg_FEA',
]

# Simplifies a string, typically an erratum title, to match it with different errata.
def plainify_str(in_str: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", in_str.strip()).lower()

# Transform CPU name to path of a path to a PDF (readable by camelot).
def cpuname_to_pdfpath(cpuname):
    if "ERRATA_BUILDDIR" not in os.environ:
        raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
    return os.path.join(os.environ["ERRATA_BUILDDIR"], 'pdfs', cpuname+".pdf")

# Transform CPU name to path of a path to a generated text file.
def cpuname_to_txtpath(cpuname):
    if "ERRATA_BUILDDIR" not in os.environ:
        raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
    return os.path.join(os.environ["ERRATA_BUILDDIR"], 'txts', cpuname+".txt")

# Check from the erratum title whether the erratum has been removed.
def is_erratum_removed(erratumkey, title):
    is_removed = (
        ("<" in title and ">" in title and "removed" in title.lower())
        or ("erratum"   in title.lower() and "removed" in title.lower())
        or ("duplicate" in title.lower() and "removed" in title.lower())
        or ("deleted"   in title.lower() and "refer" in title.lower())
        or ("replaced"  in title.lower() and "by" in title.lower() and "errat" in title.lower())
        or len(title) < 3
    )
    if is_removed:
        print("Removing erratum {} with title `{}`.".format(erratumkey, title))
    return is_removed

# Assumes that the corresponding CPU errata document has been parsed.
def plaintitle_to_erratumname(cpuname, plaintitle):
    if "ERRATA_BUILDDIR" not in os.environ:
        raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")

    filepath = os.path.join(os.environ["ERRATA_BUILDDIR"], 'parsed', "{}_details".format(cpuname))
    if not os.path.exists(filepath):
        raise ValueError('No such file: `{}`. Make sure the document is parsed for CPU `{}`.'.format(filepath, cpuname))

    with open(filepath, 'r') as f:
        dict_content = json.load(f)

    for erratumname, details in dict_content.items():
        if plainify_str(details['title']) == plaintitle:
            return erratumname
    raise ValueError("plaintitle `{}` not found for CPU `{}`".format(plaintitle, cpuname))
