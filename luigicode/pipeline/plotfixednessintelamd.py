# Produces the fixedness plot for Intel processors.

from collections import defaultdict
import json
import luigi
import numpy as np
import os
from pathlib import Path
import pprint

import matplotlib.pyplot as plt
from pipeline.parsedetailsamd import ParseDetailsAMD
from pipeline.parseoverviewintel import ParseOverviewIntel
from common import intel_cpu_names, intel_cpu_prettynames, amd_cpu_names, amd_cpu_prettynames_abbrev

from matplotlib import rc
rc('font', **{'family':'serif', 'serif':['Times']})
rc('text', usetex=True)

intel_fixedness_row_indices = {
    "intel_core_1_desktop": (2,),
    "intel_core_1_mobile":  (2,),
    "intel_core_2_desktop": (2,),
    "intel_core_2_mobile":  (2,),
    "intel_core_3_desktop": (3,),
    "intel_core_3_mobile":  (2,),
    "intel_core_4_desktop": (1,),
    "intel_core_4_mobile":  (2,),
    "intel_core_5_desktop": (1,),
    "intel_core_5_mobile":  (2,),
    "intel_core_6":         (7,),
    "intel_core_7_8":       (0,1,2,3,4,5,6,7,8,9),
    "intel_core_8_9":       (0,1,2,3,4,5,6),
    "intel_core_10":        (0,1,2,3,4,5),
    "intel_core_11":        (0,),
    "intel_core_12":        (0,1),
}

#####
# Luigi task
#####

class FixednessIntelAMD(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(FixednessIntelAMD, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/figures/fixedness_intel.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        ret = []
        for cpu_name in intel_cpu_names:
            ret.append(ParseOverviewIntel(cpu_name=cpu_name))
        for cpu_name in amd_cpu_names:
            ret.append(ParseDetailsAMD(cpu_name=cpu_name))
        return ret

    def run(self):
        num_intel_cpus = len(intel_cpu_names)
        num_amd_cpus   = len(amd_cpu_names)

        ########################################
        # Get all the manufacturer's overviews.
        ########################################

        intel_errata_overviews_allgens = []
        for cpu_id in range(num_intel_cpus):
            with open(self.input()[cpu_id].path, "r") as infile:
                intel_errata_overviews_allgens.append(json.load(infile))
        amd_errata_details_allgens = []
        for cpu_id in range(num_amd_cpus):
            with open(self.input()[num_intel_cpus + cpu_id].path, "r") as infile:
                amd_errata_details_allgens.append(json.load(infile))

        ########################################
        # Get the fixedness for each CPU independently.
        ########################################
        
        intel_num_fixed = []
        intel_num_notfixed = []

        for cpu_id, cpu_name in enumerate(intel_cpu_names):
            intel_num_fixed.append(0)
            intel_num_notfixed.append(0)
            for _, overview_row in intel_errata_overviews_allgens[cpu_id].items():
                print(overview_row)
                isfixed = False
                for fixedness_row_id in intel_fixedness_row_indices[cpu_name]:
                    if 'fixed' in overview_row[fixedness_row_id].lower() or 'plan' in overview_row[fixedness_row_id].lower():
                        isfixed = True
                        break
                if isfixed:
                    intel_num_fixed[cpu_id] += 1
                else:
                    intel_num_notfixed[cpu_id] += 1
        
        amd_num_fixed = []
        amd_num_notfixed = []

        for cpu_id, cpu_name in enumerate(amd_cpu_names):
            amd_num_fixed.append(0)
            amd_num_notfixed.append(0)
            for erratumkey, erratum in amd_errata_details_allgens[cpu_id].items():
                if 'no' in erratum['status'].lower():
                    amd_num_notfixed[cpu_id] += 1
                else:
                    amd_num_fixed[cpu_id] += 1

        self.pp.pprint(intel_num_fixed)
        self.pp.pprint(intel_num_notfixed)
        self.pp.pprint(amd_num_fixed)
        self.pp.pprint(amd_num_notfixed)

        
        ########################################
        # Do the plot.
        ########################################
        
        intel_nofixes_ys = []
        intel_fixeds_ys  = []
        for cpu_id in range(num_intel_cpus):
            intel_nofixes_ys.append(0)
            intel_fixeds_ys.append(intel_num_notfixed[cpu_id])
        amd_nofixes_ys = []
        amd_fixeds_ys  = []
        for cpu_id in range(num_amd_cpus):
            amd_nofixes_ys.append(0)
            amd_fixeds_ys.append(amd_num_notfixed[cpu_id])

        width = 0.35

        AX_INTEL = 0
        AX_AMD   = 1
        fig, ax = plt.subplots(1, 2, sharey=True, figsize=(6, 3))
        ax[AX_INTEL].bar(range(num_intel_cpus), intel_num_notfixed, width, bottom=intel_nofixes_ys, label='No fix')
        ax[AX_INTEL].bar(range(num_intel_cpus), intel_num_fixed,  width, bottom=intel_fixeds_ys, label='Fix')
        ax[AX_AMD].bar(range(num_amd_cpus), amd_num_notfixed, width, bottom=amd_nofixes_ys, label='No fix')
        ax[AX_AMD].bar(range(num_amd_cpus), amd_num_fixed,  width, bottom=amd_fixeds_ys, label='Fix')

        ax[AX_INTEL].grid(axis='y')
        ax[AX_INTEL].set_axisbelow(True)
        ax[AX_INTEL].set_xticks(np.arange(len(intel_cpu_names), step=1))
        ax[AX_INTEL].set_xticklabels(map(lambda x: intel_cpu_prettynames[x], intel_cpu_names), rotation=45)
        ax[AX_INTEL].set_title('Intel')
        ax[AX_AMD].grid(axis='y')
        ax[AX_AMD].set_axisbelow(True)
        ax[AX_AMD].set_xticks(np.arange(len(amd_cpu_names), step=1))
        ax[AX_AMD].set_xticklabels(map(lambda x: amd_cpu_prettynames_abbrev[x], amd_cpu_names), rotation=45)
        ax[AX_AMD].set_title('AMD')

        ax[AX_INTEL].set_ylabel('Number of errata')
        # ax[AX_INTEL].legend(framealpha=1)
        # ax[AX_AMD].set_ylabel('Number of errata')
        ax[AX_AMD].legend(framealpha=1)

        ax[AX_INTEL].set_ylim(0, 205)
        ax[AX_AMD].set_ylim(0, 205)

        plt.sca(ax[AX_INTEL])
        plt.xticks(rotation = 90)
        plt.sca(ax[AX_AMD])
        plt.xticks(rotation = 90)

        fig.tight_layout()

        # Save more figures than what luigi would.
        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        plt.savefig(os.path.join(target_dir, "cpufix_intel_amd.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "cpufix_intel_amd.png"), dpi=300)
