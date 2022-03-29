# This task finds the bugs that are common beteween all Skylake processors.

import json
import luigi
import os
from pathlib import Path
import pprint

import matplotlib.pyplot as plt
from pipeline.parsedetailsintel import ParseDetailsIntel
from common import intel_cpu_prettynames, plainify_str
from timeline.timelineutil import fill_timeline_for_cpu, tupldate_to_int

skylake_cpu_names = [
    "intel_core_6",
    "intel_core_7_8",
    "intel_core_8_9",
    "intel_core_10",
]

#####
# Luigi task
#####

class CommonSkylake(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(CommonSkylake, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/figures/common_skylake.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        ret = []
        for cpu_name in skylake_cpu_names:
            ret.append(ParseDetailsIntel(cpu_name=cpu_name))
        return ret

    def run(self):
        num_cpus = len(skylake_cpu_names)
        ########################################
        # Get all the manufacturer's errata.
        ########################################

        errata_details_allgens = []
        for cpu_id in range(num_cpus):
            with open(self.input()[cpu_id].path, "r") as infile:
                errata_details_allgens.append(json.load(infile))

        ########################################
        # Find titles that are present in all Skylake processors
        ########################################

        # Create a title set for each cpu.
        title_sets = []
        for errata_dict in errata_details_allgens:
            title_sets.append(set())
            for _, erratum in errata_dict.items():
                title_sets[-1].add(plainify_str(erratum['title']))

        intersection_plaintitles = title_sets[0]
        for i in range(1, len(title_sets)):
            intersection_plaintitles = intersection_plaintitles.intersection(title_sets[i])
        intersection_plaintitles = list(intersection_plaintitles)
        print("len(intersection_plaintitles):", len(intersection_plaintitles))

        ########################################
        # Get the timelines for all these errata for all 4 CPU models.
        ########################################

        timelines = dict()
        for cpu_id, cpu_name in enumerate(skylake_cpu_names):
            errata_names = []
            # 1. Get the corresponding errata names.
            for plaintitle_id, plaintitle in enumerate(intersection_plaintitles):
                for erratumname, details in errata_details_allgens[cpu_id].items():
                    if plainify_str(details['title']) == plaintitle:
                        errata_names.append(erratumname)
                        break
                if len(errata_names) != plaintitle_id+1:
                    raise ValueError("Could not find erratum name in CPU `{}` for plaintitle `{}`.".format(cpu_name, plaintitle))
            # 2. Get the timeline.
            timelines[cpu_name] = fill_timeline_for_cpu(cpu_name, errata_names)

        #########################
        # Display the timeline.
        #########################

        # Draw one line per processor
        Xs = []
        Ys = []

        # Intel
        for cpu_id, cpu_name in enumerate(skylake_cpu_names):
            Xs.append([])
            Ys.append([])
            for dateint in timelines[cpu_name]:
                Xs[cpu_id].append(dateint)
                Ys[cpu_id].append(timelines[cpu_name][dateint])

        fig, ax = plt.subplots(figsize=(6, 2.5))

        for cpu_id, cpu_name in enumerate(skylake_cpu_names):
            ax.plot(Xs[cpu_id], Ys[cpu_id], marker='.', label=intel_cpu_prettynames[cpu_name])
        # Set the X labels
        xtick_locations = []
        for year in range(2008, 2024):
            xtick_locations.append(tupldate_to_int(1, year))
        ax.set_xticks(xtick_locations, range(2008, 2024))
        ax.set_xlim(tupldate_to_int(3, 2015), tupldate_to_int(8, 2020))
        ax.grid()
        ax.legend(loc="lower right", ncol=2)

        plt.xlabel("Disclosure date")
        plt.ylabel("Num. errata (cumul.)")
        fig.tight_layout()
        # fig.text(0.07, 0.5, "Cumulated number of disclosed errata", va='center', rotation='vertical')

        # Save more figures than what luigi would.
        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        plt.savefig(os.path.join(target_dir, "timeline_skylake.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "timeline_skylake.png"), dpi=300)
