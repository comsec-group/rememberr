# Produces the heredity figure for Intel designs.

import json
import luigi
import numpy as np
import os
from pathlib import Path
import pprint

import matplotlib.pyplot as plt
from pipeline.parsedetailsintel import ParseDetailsIntel
from common import intel_cpu_names, intel_cpu_prettynames, plainify_str

# Choose another mode to get a lighter figure. This parameter is not yet implemented.
HEREDITY_FILTER = 'ALL'
# HEREDITY_FILTER = 'MOBILE_ONLY'
# HEREDITY_FILTER = 'DESKTOP_ONLY'

#####
# Luigi task
#####

class HeredityIntel(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(HeredityIntel, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/figures/heredity_intel.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        ret = []
        for cpu_name in intel_cpu_names:
            ret.append(ParseDetailsIntel(cpu_name=cpu_name))
        return ret

    def run(self):
        num_cpus = len(intel_cpu_names)
        ########################################
        # Get all the manufacturer's errata.
        ########################################

        errata_details_allgens = []
        for cpu_id in range(num_cpus):
            with open(self.input()[cpu_id].path, "r") as infile:
                errata_details_allgens.append(json.load(infile))

        ########################################
        # Find titles that are present in a pair of processors.
        ########################################

        # Create a title set for each cpu.
        title_sets = []
        for errata_dict in errata_details_allgens:
            title_sets.append(set())
            for _, erratum in errata_dict.items():
                title_sets[-1].add(plainify_str(erratum['title']))

        my_intersection_matrix = np.array([[0 for _ in intel_cpu_names] for _ in intel_cpu_names])

        for low_cpuname_id in range(num_cpus):
            for high_cpuname_id in range(low_cpuname_id, num_cpus):
                my_intersection_matrix[low_cpuname_id][high_cpuname_id] = len(title_sets[low_cpuname_id].intersection(title_sets[high_cpuname_id]))

        ########################################
        # Generate the heatmap data
        ########################################

        # Use a mask to only display the upper half.
        mask = np.tri(num_cpus, num_cpus, -1)
        data = np.ma.array(my_intersection_matrix, mask=mask)
        print(data)

        ########################################
        # Plot the heatmap
        ########################################

        fig, ax = plt.subplots(figsize=(12, 8))

        ax.matshow(data)
        ax.tick_params(bottom=False)

        # Print the values in boxes
        for (i, j), z in np.ndenumerate(data):
            if i <= j:
                ax.text(j, i, '{}'.format(z), ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor='white', edgecolor='0.3'))

        # Ticks
        ax.set_xticks(np.arange(len(intel_cpu_names), step=1))
        ax.set_yticks(list(range(0,len(intel_cpu_names))))
        ax.set_xticklabels(map(lambda x: intel_cpu_prettynames[x], intel_cpu_names), rotation=45)
        ax.set_yticklabels(map(lambda x: intel_cpu_prettynames[x], intel_cpu_names))
        fig.tight_layout()

        # Save more figures than what luigi would.
        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        plt.savefig(os.path.join(target_dir, "heredity_intel.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "heredity_intel.png"), dpi=300)
