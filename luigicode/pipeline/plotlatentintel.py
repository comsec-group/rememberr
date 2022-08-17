# Produces the figure of latent bugs for Intel designs.

import json
import luigi
import os
import pandas as pd
from pathlib import Path
import pprint

from timeline.timelineutil import strtodate, tupldate_to_int, MAX_MONTH, MAX_YEAR
import matplotlib.pyplot as plt
from pipeline.parsedetailsintel import ParseDetailsIntel
from common import intel_cpu_names, plainify_str

from matplotlib import rc
rc('font', **{'family':'serif', 'serif':['Times']})
rc('text', usetex=True)

#####
# Luigi task
#####

class LatentIntel(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(LatentIntel, self).__init__(*args, **kwargs)

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

        errata_details_allgens = {}
        for cpu_id in range(num_cpus):
            with open(self.input()[cpu_id].path, "r") as infile:
                errata_details_allgens.update(json.load(infile))


        ########################################
        # Find titles that are present in a pair of processors.
        ########################################

        # timeline[dateint] = {set of (plaintitle, intel_cpu_name)}
        timeline = []
        for _ in range(tupldate_to_int(MAX_MONTH, MAX_YEAR)):
            timeline.append(list())

        errata_dates_xlsx = '../errata_dates.xlsx'
        xl = pd.ExcelFile(errata_dates_xlsx)
        for intel_cpu_name_id, intel_cpu_name in enumerate(intel_cpu_names):
            curr_df = xl.parse(intel_cpu_name)

            for _, row in curr_df.iterrows():
                datestr = row['date']
                if datestr and type(datestr) != float and row['erratum'] in errata_details_allgens:
                    timeline[tupldate_to_int(*strtodate(row['date']))].append((plainify_str(errata_details_allgens[row['erratum']]['title']), intel_cpu_name_id))

        ########################################
        # Count the number of errata addition per date
        ########################################

        num_new_errata = []
        for time_id in range(tupldate_to_int(MAX_MONTH, MAX_YEAR)):
            num_new_errata.append(len(timeline[time_id]))

        ########################################
        # Count the forward and backward latent errata per date
        ########################################

        # Lists of sets of plaintitles
        fwd_latent = []
        bwd_latent = []

        for _ in range(tupldate_to_int(MAX_MONTH, MAX_YEAR)):
            fwd_latent.append(set())
            bwd_latent.append(set())

        for time_id in range(tupldate_to_int(MAX_MONTH, MAX_YEAR)-1):
            for curr_erratum_plaintitle, curr_cpu_gen in timeline[time_id]:
                for next_time_id in range(time_id+1, tupldate_to_int(MAX_MONTH, MAX_YEAR)):
                    for next_erratum_plaintitle, next_cpu_gen in timeline[next_time_id]:
                        if next_erratum_plaintitle == curr_erratum_plaintitle:
                            if next_cpu_gen > curr_cpu_gen:
                                for interm_time_id in range(time_id, next_time_id):
                                    fwd_latent[interm_time_id].add(curr_erratum_plaintitle)
                            elif next_cpu_gen < curr_cpu_gen:
                                for interm_time_id in range(time_id, next_time_id):
                                    bwd_latent[interm_time_id].add(curr_erratum_plaintitle)

        fwd_latent_nums = list(map(len, fwd_latent))
        bwd_latent_nums = list(map(len, bwd_latent))

        ########################################
        # Plot
        ########################################


        fig, ax = plt.subplots(figsize=(6, 2.5))

        # Ticks
        ax.grid()
        ax.plot(list(range(len(fwd_latent))), fwd_latent_nums, label='forward-latent')
        ax.plot(list(range(len(bwd_latent))), bwd_latent_nums, label='backward-latent')
        ax.legend()

        xtick_locations = []
        for year in range(2008, 2024):
            xtick_locations.append(tupldate_to_int(1, year))
        ax.set_xticks(xtick_locations, range(2008, 2024), rotation=45)
        ax.set_xlim(tupldate_to_int(8, 2008), tupldate_to_int(6, 2022))
        ax.set_ylabel('Number of latent errata')

        fig.tight_layout()

        # Save more figures than what luigi would.
        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        plt.savefig(os.path.join(target_dir, "latent_errata.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "latent_errata.png"), dpi=300)
