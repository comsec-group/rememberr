# Plots the most common triggers, contexts and observable effects.

from collections import defaultdict
import json
import luigi
import numpy as np
import os
from pathlib import Path
import pprint
from collections import defaultdict
from itertools import combinations

import matplotlib.pyplot as plt
from common import triggers

#####
# Luigi task
#####

class CorrTrigCtxtEff(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(CorrTrigCtxtEff, self).__init__(*args, **kwargs)

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

        # Triggers
        num_triggers_true = defaultdict(int)
        errataName2triggers = defaultdict(set)

        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_intel.json')) as f:
            intel_data = json.load(f)
        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_amd.json')) as f:
            amd_data = json.load(f)

        for errid in intel_data:
            for cat in intel_data[errid]:
                if not cat in triggers:
                    continue
                if intel_data[errid][cat]['chosen']:
                    errataName2triggers[errid].add(cat)
                    num_triggers_true[cat] += 1
        for errid in amd_data:
            for cat in amd_data[errid]:
                if not cat in triggers:
                    continue
                if amd_data[errid][cat]['chosen']:
                    errataName2triggers[errid].add(cat)
                    num_triggers_true[cat] += 1


        trig2pos = dict()
        for idx, name in enumerate(sorted(triggers)):
            trig2pos[name] = idx

        num_combinations = len(trig2pos)
        data_triggerPairs = np.zeros((num_combinations, num_combinations))
        for _, trgs in errataName2triggers.items():
            # count all combinations of 2 triggers
            for comb in combinations(trgs, 2):
                idx1, idx2 = trig2pos[comb[0]], trig2pos[comb[1]]
                (idx1, idx2) = (idx2, idx1) if idx2 < idx1 else (idx1, idx2)
                data_triggerPairs[idx1][idx2] += 1

        p_v = dict()
        for i1, d1 in enumerate(data_triggerPairs):
            for i2, d2 in enumerate(d1):
                p_v[(i1,i2)] = d2
        print(dict(sorted(p_v.items(), key=lambda item: item[1], reverse=True)[:10]))



        ########################################
        # Generate the heatmap data
        ########################################

        # Use a mask to only display the upper half.
        mask = np.tri(num_combinations, num_combinations, 0)
        data_triggerPairs = np.ma.array(data_triggerPairs, mask=mask)

        ########################################
        # Plot the heatmap for pairwise correlation
        ########################################

        fig, ax = plt.subplots(figsize=(12, 8))

        ax.matshow(data_triggerPairs)
        ax.tick_params(bottom=False)

        # Print the values in boxes
        for (i, j), z in np.ndenumerate(data_triggerPairs):
            if data_triggerPairs[i][j] > 0 and i <= j:
                ax.text(j, i, '{:d}'.format(int(z)), ha='center', va='center', fontsize='small',
                    bbox=dict(boxstyle='round', facecolor='white', edgecolor='0.3'))

        ax.set_xticks(np.arange(0, len(trig2pos), step=1), minor=False)
        ax.set_yticks(np.arange(0, len(trig2pos), step=1), minor=False)

        ax.set_xticklabels(trig2pos.keys(), rotation=90)
        ax.yaxis.tick_right()
        ax.yaxis.set_label_position("right")
        ax.set_yticklabels(trig2pos.keys())

        plt.grid(True, color='#CECCCC', which='major')

        fig.tight_layout()

        # Save more figures than what luigi would.
        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        plt.savefig(os.path.join(target_dir, "corrtriggers2d.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "corrtriggers2d.png"), dpi=300)
