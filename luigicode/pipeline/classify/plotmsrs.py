# This script is used to count the occurrence of MSRs in errata.

from collections import defaultdict
import json
import luigi
import numpy as np
import os
from pathlib import Path
import pprint

import matplotlib.pyplot as plt
from pipeline.classify.classifymsrsintel import INTEL_MSR_NAMES

intel_msr_prettylabels = [
    'MCx_STATUS',
    'DEBUGCTL'
    'PERF_GBL_CTRL',
    'RTIT_CTL',
    'PERF_GBL_STATUS',
    'PMCx',
    'BR_INST_RETIRED',
    'RTIT_STATUS',
    'MISC_ENABLE',
    'TSC_DEADLINE'
]

# [
# 'MSR0000_0401',
# 'MSR0000_0402',
# 'MSRC001_1037',
# 'MSRC001_1030',
# 'MSRC001_0003',
# 'MSRC001_0000',
# 'MSRC001_1033',
# 'MSRC001_1036',
# 'MSRC001_0015',
# 'MSR0000_0403'
# ]

intel_msr_prettylabels = [
    'MCx_STATUS',
    'MCx_ADDR',
    'IBS_OP_DATAx',
    'IBS_FETCH_CTL',
    'CPUID_PWR_THERM',
    'PERF_LEGACY_CTL3',
    'PERF_LEGACY_CTL0',
    'IBS_OP_CTL',
    'BR_INST_RETIRED',
    'RTIT_STATUS',
]

amd_msr_prettylabels_dict = {
    'MSR0000_0001':  '',
    'MSR0000_00E7': 'MSR_IA32_MPERF',
    'MSR0000_00E8': 'MSR_IA32_APERF',
    'MSR0000_01DC': 'MSR_LASTBRANCHTOIP',
    'MSR0000_0401': 'MCx_STATUS',
    'MSR0000_0402': 'MCx_ADDR',
    'MSR0000_0403': 'MCx_MISC',
    'MSR0000_0404': 'MCx_CTL',
    'MSR0000_0410': 'MCx_CTL',
    'MSR0000_0411': 'MCx_STATUS',
    'MSR0000_0419': 'MCx_STATUS',
    'MSR0004_1162': '',
    'MSRC000_0080': 'EFER',
    'MSRC000_0084': 'SYSCALL_FLAG_MASK',
    'MSRC000_00E9': 'IRPerfCount',
    'MSRC001_0000': 'PERF_LEGACY_CTR',
    'MSRC001_0003': 'PERF_LEGACY_CTR',
    'MSRC001_0015': 'HWCR',
    'MSRC001_0050': 'SMI_ON_IO_TRAP',
    'MSRC001_0051': 'SMI_ON_IO_TRAP',
    'MSRC001_0052': 'SMI_ON_IO_TRAP',
    'MSRC001_0053': 'SMI_ON_IO_TRAP',
    'MSRC001_0055': 'IntPend',
    'MSRC001_0062': 'PStateCtl',
    'MSRC001_0063': 'PStateStat',
    'MSRC001_0064': 'PStateDef',
    'MSRC001_0068': 'PStateDef',
    'MSRC001_006B': 'PStateDef',
    'MSRC001_0072': 'PstateLimit',
    'MSRC001_0073': 'CStateBaseAddr',
    'MSRC001_0074': 'CStateBaseAddr',
    'MSRC001_0200': 'PERF_CTL',
    'MSRC001_0201': 'PERF_CTL',
    'MSRC001_0202': 'PERF_CTL',
    'MSRC001_0203': 'PERF_CTL',
    'MSRC001_0204': 'PERF_CTL',
    'MSRC001_0205': 'PERF_CTL',
    'MSRC001_0206': 'PERF_CTL',
    'MSRC001_0207': 'PERF_CTL',
    'MSRC001_0208': 'PERF_CTL',
    'MSRC001_0209': 'PERF_CTL',
    'MSRC001_020A': 'PERF_CTL',
    'MSRC001_020B': 'PERF_CTL',
    'MSRC001_0230': 'ChL3PmcCfg',
    'MSRC001_0231': 'ChL3PmcCfg',
    'MSRC001_1030': 'IBS_FETCH_CTL',
    'MSRC001_1031': 'IBS_FETCH_LINADDR',
    'MSRC001_1032': 'IBS_FETCH_PHYSADDR',
    'MSRC001_1033': 'IBS_OP_CTL',
    'MSRC001_1034': 'IBS_OP_RIP',
    'MSRC001_1035': 'IBS_OP_DATAx',
    'MSRC001_1036': 'IBS_OP_DATAx',
    'MSRC001_1037': 'IBS_OP_DATAx',
    'MSRC001_1038': 'IBS_DC_LINADDR',
    'MSRC001_1039': 'IBS_DC_PHYSADDR',
    'MSRC001_103A': 'IBS_CTL',
    'MSRC001_103B': 'BP_IBSTGT_RIP',
}

amd_common_msrs = [
    ['MSR0000_0401', 'MSR0000_0411', 'MSR0000_0419'], # MCx_STATUS
    ['MSR0000_0404', 'MSR0000_0410'], # MCx_CTL
    ['MSR0000_0411', 'MSR411'],
    ['MSR0000_00E7', 'MSR0000_000E7'],
    ['MSRC001_0000', 'MSRC001_0003'], # PERF_LEGACY_CTR
    ['MSRC001_0064', 'MSRC001_0068', 'MSRC001_006B'], # PStateDef
    ['MSRC001_0073', 'MSRC001_0074'], # CStateBaseAddr
    ['MSRC001_0200', 'MSRC001_0201', 'MSRC001_0202', 'MSRC001_0203', 'MSRC001_0204', 'MSRC001_0205', 'MSRC001_0206', 'MSRC001_0207', 'MSRC001_0208', 'MSRC001_0209', 'MSRC001_020A', 'MSRC001_020B'], # PERF_CTL
    ['MSRC001_1035', 'MSRC001_1036', 'MSRC001_1037'], # IBS_OP_DATAx
]

#####
# Luigi task
#####

class PlotMSRs(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(PlotMSRs, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        if "ERRATA_ROOTDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_ROOTDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/figures/trig_ctx_eff_amd.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        return []

    def run(self):
        ########################################
        # Load all the classified data.
        ########################################

        intel_path = os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'msrs', 'observable_intel.json')
        amd_path = os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'msrs', 'observable_amd.json')

        # dict[plain_title] = {chosen: list, is_human: Bool}
        intel_data = {}
        amd_data = {}

        # Intel
        with open(intel_path) as f:
            intel_data = json.load(f)
        # AMD
        with open(amd_path) as f:
            amd_data = json.load(f)

        ########################################
        # Compute the number of occurrences for each MSR.
        ########################################

        # dict[msr_id] = num_occurrences
        intel_msrs = defaultdict(int)
        amd_msrs = defaultdict(int)

        # Intel
        for v in intel_data.values():
            for msr_name_id in range(len(v['chosen'])):
                msr_name = v['chosen'][msr_name_id]
                intel_msrs[msr_name] += 1
        # AMD
        for v in amd_data.values():
            already_seen_msr_classes = set()
            for msr_name_id in range(len(v['chosen'])):
                doskip = False
                msr_name = v['chosen'][msr_name_id]
                for l in amd_common_msrs:
                    if msr_name in l:
                        if l[0] in already_seen_msr_classes:
                            # This corresponds to a duplicate.
                            doskip = True
                            break
                        msr_name = l[0]
                        already_seen_msr_classes.add(msr_name)
                if doskip:
                    continue
                amd_msrs[msr_name] += 1


        ########################################
        # Sort the MSR statistics.
        ########################################


        intel_labels, intel_vals = zip(*dict(sorted(intel_msrs.items(), key=lambda item: item[1], reverse=True)).items())
        amd_labels, amd_vals = zip(*dict(sorted(amd_msrs.items(), key=lambda item: item[1], reverse=True)).items())

        intel_labels = list(intel_labels)
        intel_vals = list(intel_vals)
        amd_labels = list(amd_labels)
        amd_vals = list(amd_vals)

        # Take only the 10 most popular MSRs

        intel_labels = intel_labels[:10]
        intel_vals = intel_vals[:10]
        amd_labels = amd_labels[:10]
        amd_vals = amd_vals[:10]

        intel_vals = list(map(lambda v: round(v/7.72, 1), intel_vals))
        amd_vals = list(map(lambda v: round(v/3.77, 1), amd_vals))


        ########################################
        # Do the plots.
        ########################################

        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)

        # Intel
        AX_INTEL = 0
        AX_AMD   = 1

        fig, ax = plt.subplots(1, 2, figsize=(6, 3.5), sharey=True)
        intel_bars = ax[AX_INTEL].bar(range(len(intel_vals)), intel_vals)
        ax[AX_INTEL].bar_label(intel_bars)
        ax[AX_INTEL].grid(axis='y')
        ax[AX_INTEL].set_axisbelow(True)
        ax[AX_INTEL].set_xticks(np.arange(len(intel_msr_prettylabels)), step=1)
        ax[AX_INTEL].set_xticklabels(intel_msr_prettylabels, rotation=90)
        ax[AX_INTEL].set_ylabel('Affected errata (%)')
        ax[AX_INTEL].set_title('Intel')
        ax[AX_INTEL].set_ylim(0, 7.9)

        amd_bars = ax[AX_AMD].bar(range(len(amd_vals)), amd_vals)
        ax[AX_AMD].bar_label(amd_bars)
        ax[AX_AMD].grid(axis='y')
        ax[AX_AMD].set_axisbelow(True)
        ax[AX_AMD].set_xticks(np.arange(len(amd_labels)), step=1)
        ax[AX_AMD].set_xticklabels(map(lambda x: amd_msr_prettylabels_dict[x], amd_labels), rotation=90)
        # ax[AX_AMD].set_ylabel('Number of errata')
        ax[AX_AMD].set_title('AMD')

        fig.tight_layout()
        # Save more figures than what luigi would.
        plt.savefig(os.path.join(target_dir, "msrs_intel_amd.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "msrs_intel_amd.png"), dpi=300)
