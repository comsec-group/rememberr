# Produces the heredity figure for Intel designs.

import json
import luigi
import numpy as np
import os
from pathlib import Path
import pprint
from collections import defaultdict, Counter

import matplotlib.pyplot as plt
from pipeline.parsedetailsintel import ParseDetailsIntel
from common import intel_cpu_names, intel_cpu_prettynames, plainify_str

from matplotlib import rc
rc('font', **{'family':'serif', 'serif':['Times']})
rc('text', usetex=True)

intel_cpu_names_nomobile = list(filter(lambda x: "mobile" not in x, intel_cpu_names))

#####
# Luigi task
#####

class HeredityBarsIntel(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(HeredityBarsIntel, self).__init__(*args, **kwargs)

        # Ensure that the target builddir environment variable exists.
        if "ERRATA_BUILDDIR" not in os.environ:
            raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
        self.pp = pprint.PrettyPrinter(indent=4, width=200)

    def output(self):
        # Actually, this is a root job so we make sure that it never produces its output file like this.
        return luigi.LocalTarget('{}/figures/hereditybars_intel.dummy'.format(os.environ["ERRATA_BUILDDIR"]), format=luigi.format.Nop)

    def requires(self):
        ret = dict()
        for cpu_name in intel_cpu_names:
            ret[cpu_name] = ParseDetailsIntel(cpu_name=cpu_name)
        return ret

    def run(self):
        ########################################
        # Get all the manufacturer's errata.
        ########################################

        errata_details_allgens = dict()
        for cpu_name in intel_cpu_names:
            with open(self.input()[cpu_name].path, "r") as infile:
                errata_details_allgens[cpu_name] = json.load(infile)

        ########################################
        # Process the errata data
        ########################################

        # Create a title set for each cpu.
        title_sets = dict()
        for cpu_name in errata_details_allgens:
            title_sets[cpu_name] = set()
            for _, erratum in errata_details_allgens[cpu_name].items():
                title_sets[cpu_name].add(plainify_str(erratum['title']))
            # for cpu_name, erratum in errata_dict.items():
            #     title_sets[cpu_name].add(plainify_str(erratum['title']))

        # For each erratum title, count how many generations have it.
        generations_per_title = defaultdict(set)
        generations_per_title_nomobile = defaultdict(set)
        for cpu_name in intel_cpu_names:
            for title in title_sets[cpu_name]:
                generations_per_title[title].add(cpu_name)
                if not "mobile" in cpu_name:
                    generations_per_title_nomobile[title].add(cpu_name)

        num_titles = len(generations_per_title)
        num_titles_nomobile = len(generations_per_title_nomobile)

        num_generations_per_title = dict()
        num_generations_per_title_nomobile = dict()
        for title, generations in generations_per_title.items():
            num_generations_per_title[title] = len(generations)
        for title, generations in generations_per_title_nomobile.items():
            num_generations_per_title_nomobile[title] = len(generations)

        # Count the titles having 1, 2, 3, ... generations.
        num_titles_per_generation = Counter(num_generations_per_title.values())
        num_titles_per_generation_nomobile = Counter(num_generations_per_title_nomobile.values())
        
        ########################################
        # Plot.
        ########################################
        
        num_titles_per_generation_normalized = {k: 100*v/num_titles for k, v in num_titles_per_generation.items()}
        num_titles_per_generation_nomobile_normalized = {k: 100*v/num_titles_nomobile for k, v in num_titles_per_generation_nomobile.items()}
        
        # Plot the bar chart.
        fig, ax = plt.subplots(figsize=(7, 2.2))
        
        # Plot the number of titles having 1, 2, 3, ... generations.
        # Determine all generation numbers (x axis positions).
        generations = sorted(set(num_titles_per_generation_normalized.keys()) | set(num_titles_per_generation_nomobile_normalized.keys()))
        x = np.array(generations)
        width = 0.35  # the width of the bars

        # Get values for each generation, defaulting to 0 if missing.
        values_all = [num_titles_per_generation_normalized.get(gen, 0) for gen in generations]
        values_nomobile = [num_titles_per_generation_nomobile_normalized.get(gen, 0) for gen in generations]

        # Create grouped bar plot.
        ax.bar(x - width/2, values_all, width, label="Split Desktop/Mobile", color='darkblue')
        ax.bar(x + width/2, values_nomobile, width, label="Desktop Only", color='lightblue')
        
        # Ticks
        ax.set_xticks(np.arange(1, max(num_titles_per_generation_normalized.keys())+1, step=1))
        ax.set_xlabel('Number of generations affected by an erratum')
        ax.set_ylabel('Proportion of errata (\%)')
        ax.set_axisbelow(True)
        ax.grid(axis='y')
        ax.set_yticks([0, 20, 40])
        ax.set_yticklabels([f'{tick}\%' for tick in [0, 20, 40]])
        ax.set_title('Errata longevity')
        ax.legend(framealpha=1)
        fig.tight_layout()
        
        plt.savefig(os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures', "hereditybars_intel.pdf"), dpi=300)
        plt.savefig(os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures', "hereditybars_intel.png"), dpi=300)

        ########################################
        # Find the most popular titles
        ########################################

        # Titles with the strictly highest number of generations.
        largest_num_generations = max(num_generations_per_title.values())
        largest_num_generations_nomobile = max(num_generations_per_title_nomobile.values())
        
        most_popular_titles = [title for title, num_generations in num_generations_per_title.items() if num_generations == largest_num_generations]
        most_popular_titles_nomobile = [title for title, num_generations in num_generations_per_title_nomobile.items() if num_generations == largest_num_generations_nomobile]
        
        print(f"Most popular titles (Desktop&Mobile) ({largest_num_generations} generations):")
        for title in most_popular_titles:
            print(f"  {title}")
        print(f"Most popular titles (Desktop only) ({largest_num_generations_nomobile} generations):")
        for title in most_popular_titles_nomobile:
            print(f"  {title}")
        
        print(f"Are the most popular titles the same? {set(most_popular_titles) == set(most_popular_titles_nomobile)}")

        ########################################
        # Find the titles in core3 m but not in core3 d
        ########################################
        
        # Find the titles in core3 m but not in core3 d.
        core3d_titles = set(title_sets["intel_core_3_desktop"])
        core3m_titles = set(title_sets["intel_core_3_mobile"])
        titles_in_core3m_not_core3d = core3m_titles - core3d_titles
        print(f"Titles in core3m but not in core3d:")
        for title in titles_in_core3m_not_core3d:
            print(f"  {title}")

        ########################################
        # Find the titles in core4 d but not in core4 m
        ########################################
        
        # Find the titles in core4 d but not in core4 m.
        core4d_titles = set(title_sets["intel_core_4_desktop"])
        core4m_titles = set(title_sets["intel_core_4_mobile"])
        titles_in_core4d_not_core4m = core4d_titles - core4m_titles
        print(f"Titles in core4d but not in core4m:")
        for title in titles_in_core4d_not_core4m:
            print(f"  {title}")
