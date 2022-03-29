# Produces the heredity figure for Intel and AMD designs.

from collections import defaultdict
import json
import luigi
import numpy as np
import os
from pathlib import Path
import pprint
import re

import matplotlib.pyplot as plt
from pipeline.uniqueintel import UniqueIntel
from pipeline.uniqueamd import UniqueAMD

# Human-crafted and human-controlled regexes corresponding to the various possible workarounds.
workaround_regexes = [
    ('BIOS/Firmware', [r'bios', r'firmware', r'\bL0s\b']),
    ('Software', [r'software', r'do not', r'code', r'writ', r'read', r'handler', r'performance', r'ipi', r'disable.*perfmon', r'located', r'sampling', r'driver', r'algorithm', r'sequence', r'command', r'set to a value', r'counter', r'instruction', r'operating system', r'vmm', r'by setting', r'remain at the amd recommended values', r'hypervisor', r'virtual address', r'system pa', r'then use', r'always map', r'retry the operation']),
    ('Peripherals', [r'pcie?\s*(?:agent|device|end\s*point|egress)', r'pcie\s*end\s*point', r'\#.*\bpins?\b', r'second\s*reset', r'\brail\b', r'\blink\b', r'\bvldt\b', r'frequency', r'\bprecharge\b']),
    ('None', [r'none', r'^no$', r'^no\s*workaround']),
    ('Absent', [r'no field for', r'information on a'])
]

#####
# Luigi task
#####

class WorkaroundsIntelAMD(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(WorkaroundsIntelAMD, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/figures/workarounds_intel.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        return [UniqueIntel(), UniqueAMD()]

    def run(self):
        ########################################
        # Get all the unique errata.
        ########################################

        with open(self.input()[0].path, "r") as infile:
            intel_all_unique_errata = json.load(infile)
        with open(self.input()[1].path, "r") as infile:
            amd_all_unique_errata = json.load(infile)

        ########################################
        # Classify all the errata.
        ########################################

        intel_errata_classification = defaultdict(int)
        for erratum in intel_all_unique_errata:
            if not 'workaround' in erratum:
                intel_errata_classification['absent'] += 1
            else:
                is_classified = False
                for category, curr_regexes in workaround_regexes:
                    for curr_regex in curr_regexes:
                        if re.search(curr_regex, erratum['workaround'], re.IGNORECASE | re.DOTALL) is not None:
                            is_classified = True
                            intel_errata_classification[category] += 1
                            break
                    if is_classified:
                        break
                if not is_classified:
                    raise ValueError("Could not classify Intel erratum with workaround:\n\t{}".format(erratum['workaround']))

        amd_errata_classification = defaultdict(int)
        for erratum in amd_all_unique_errata:
            if not 'workaround' in erratum:
                amd_errata_classification['absent'] += 1
            else:
                is_classified = False
                for category, curr_regexes in workaround_regexes:
                    for curr_regex in curr_regexes:
                        if re.search(curr_regex, erratum['workaround'].lower(), re.DOTALL) is not None:
                            is_classified = True
                            amd_errata_classification[category] += 1
                            break
                    if is_classified:
                        break
                if not is_classified:
                    raise ValueError("Could not classify AMD erratum with workaround:\n\t{}".format(erratum['workaround']))

        ########################################
        # Do the plot.
        ########################################

        Xs = [i for i in range(len(workaround_regexes))]
        xlabels = [name for name,_ in workaround_regexes]
        intel_ys = []
        for category, _ in workaround_regexes:
            intel_ys.append(intel_errata_classification[category])
        amd_ys = []
        for category, _ in workaround_regexes:
            amd_ys.append(amd_errata_classification[category])

        print("intel_ys:", intel_ys)
        print("amd_ys:", amd_ys)

        # Normalize to get percentage
        INTEL_NUM_UNIQUE_ERRATA = 772
        AMD_NUM_UNIQUE_ERRATA = 377
        intel_ys = list(map(lambda x: round(100*x/INTEL_NUM_UNIQUE_ERRATA, 1), intel_ys))
        amd_ys = list(map(lambda x: round(100*x/AMD_NUM_UNIQUE_ERRATA, 1), amd_ys))

        width = 0.35

        AX_INTEL = 0
        AX_AMD   = 1
        fig, ax = plt.subplots(1, 2, figsize=(6, 2.5))
        interm_bars = ax[AX_INTEL].bar(Xs, intel_ys,  width)
        ax[AX_INTEL].bar_label(interm_bars)
        interm_bars = ax[AX_AMD].bar(Xs, amd_ys,  width)
        ax[AX_AMD].bar_label(interm_bars)

        ax[AX_INTEL].grid(axis='y')
        ax[AX_INTEL].set_axisbelow(True)
        ax[AX_INTEL].set_xticks(np.arange(len(xlabels), step=1))
        ax[AX_INTEL].set_xticklabels(xlabels, rotation=45)
        ax[AX_AMD].grid(axis='y')
        ax[AX_AMD].set_axisbelow(True)
        ax[AX_AMD].set_xticks(np.arange(len(xlabels), step=1))
        ax[AX_AMD].set_xticklabels(xlabels, rotation=45)

        ax[AX_INTEL].set_title("Intel")
        ax[AX_AMD].set_title("AMD")

        ax[AX_INTEL].set_ylabel('Proportion of errata (%)')

        ax[AX_INTEL].set_ylim(0, 48)
        ax[AX_AMD].set_ylim(0, 48)

        plt.xticks(rotation = 45)
        fig.tight_layout()

        # Save more figures than what luigi would.
        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        plt.savefig(os.path.join(target_dir, "workarounds_intel_amd.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "workarounds_intel_amd.png"), dpi=300)
