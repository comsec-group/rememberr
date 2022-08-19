# Plots the distribution of the number of triggers required for errata.

from collections import defaultdict, Counter
import json
import luigi
import os
from pathlib import Path
import pprint

import matplotlib.pyplot as plt
from pipeline.uniqueintel import UniqueIntel
from common import intel_cpu_names, amd_cpu_names, plainify_str, trigger_classes, triggers

from matplotlib import rc
rc('font', **{'family':'serif', 'serif':['Times']})
rc('text', usetex=True)

NUM_TRIGGER_CLASSSES = len(trigger_classes)
PLOT_ABSOLUTE = False

def cpuname_to_parseddetailspath(cpuname: str) -> str:
    if "ERRATA_BUILDDIR" not in os.environ:
        raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
    return os.path.join(os.environ['ERRATA_BUILDDIR'], 'parsed', '{}_details.json'.format(cpuname))

#####
# Luigi task
#####

class NumTrigsRequired(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(NumTrigsRequired, self).__init__(*args, **kwargs)

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
        return [UniqueIntel()]

    def run(self):
        ########################################
        # Load the unique errata files. To remove some duplicates that may have been removed in a later stage.
        ########################################

        with open(self.input()[0].path, "r") as infile:
            intel_all_unique_errata = json.load(infile)
        intel_all_unique_plaintitles = list(map(lambda x: plainify_str(x['title']), intel_all_unique_errata))

        ########################################
        # Load all the classified data.
        ########################################

        # There is no name conflict so we can use the same dict for Intel and AMD
        # dict[errnum] = num_triggers
        num_triggers_per_errnum = dict()

        # Intel
        # dict[trigger_name][errnum] = dict['chosen' or 'human']
        intel_trigger_categorization_dicts = defaultdict(lambda : defaultdict(dict))
        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_intel.json')) as f:
            intel_data = json.load(f)
        for errid in intel_data:
            for cat in intel_data[errid]:
                intel_trigger_categorization_dicts[cat][errid]['human'] = intel_data[errid][cat]['human']
                intel_trigger_categorization_dicts[cat][errid]['chosen'] = intel_data[errid][cat]['chosen']

        # AMD
        amd_trigger_categorization_dicts = defaultdict(lambda : defaultdict(dict))
        with open(os.path.join(os.environ['ERRATA_ROOTDIR'], 'classification', 'generic', 'postagreement_amd.json')) as f:
            amd_data = json.load(f)
        for errid in amd_data:
            for cat in amd_data[errid]:
                amd_trigger_categorization_dicts[cat][errid]['human'] = amd_data[errid][cat]['human']
                amd_trigger_categorization_dicts[cat][errid]['chosen'] = amd_data[errid][cat]['chosen']

        # Intel
        # dict[trigger_name][errnum] = bool (True iff has this trigger)
        intel_trigger_categorization_bool = defaultdict(dict)
        for trigger_name, triggerdict in intel_trigger_categorization_dicts.items():
            for errnum, smalldict in triggerdict.items():
                if plainify_str(errnum) in intel_all_unique_plaintitles:
                    intel_trigger_categorization_bool[trigger_name][errnum] = smalldict['chosen']
        # AMD
        amd_trigger_categorization_bool = defaultdict(dict)
        for trigger_name, triggerdict in amd_trigger_categorization_dicts.items():
            for errnum, smalldict in triggerdict.items():
                amd_trigger_categorization_bool[trigger_name][errnum] = smalldict['chosen']

        ########################################
        # Load all the errnums for all Intel designs.
        ########################################

        # dict[design_name] = [list of errnums]
        intel_errnums = {}
        intel_errnum_to_errid = defaultdict(dict) # dict[cpuname][plaintitle] = AAJ001 for example
        for cpuname in intel_cpu_names:
            cpu_detailspath = cpuname_to_parseddetailspath(cpuname)
            with open(cpu_detailspath, 'r') as f:
                json_content = json.load(f)
                intel_errnums[cpuname] = list(map(lambda x: plainify_str(x['title']), json_content.values()))
                for k, v in json_content.items():
                    intel_errnum_to_errid[cpuname][plainify_str(v['title'])] = k

        ########################################
        # Load all the errnums for all AMD designs.
        ########################################

        # dict[design_name] = [list of errnums]
        amd_errnums = {}
        for cpuname in amd_cpu_names:
            cpu_detailspath = cpuname_to_parseddetailspath(cpuname)
            with open(cpu_detailspath, 'r') as f:
                amd_errnums[cpuname] = list(json.load(f).keys())

        ########################################
        # Process all data for Intel and AMD.
        ########################################

        for cpuname in intel_cpu_names:
            for errnum in intel_errnums[cpuname]:
                num_triggers_per_errnum[errnum] = 0
                for trigger in triggers:
                    if errnum in intel_trigger_categorization_bool[trigger]:
                        num_triggers_per_errnum[errnum] += int(intel_trigger_categorization_bool[trigger][errnum])

        for cpuname in amd_cpu_names:
            for errnum in amd_errnums[cpuname]:
                num_triggers_per_errnum[errnum] = 0
                for trigger in triggers:
                    num_triggers_per_errnum[errnum] += int(amd_trigger_categorization_bool[trigger][errnum])

        flattened_triggercnt_intel = []
        for cpuname in intel_cpu_names:
            # print('\n' + cpuname)
            for errnum in intel_errnums[cpuname]:
                # if not num_triggers_per_errnum[errnum]:
                    # print("\t{}".format(intel_errnum_to_errid[cpuname][errnum]))
                flattened_triggercnt_intel.append(num_triggers_per_errnum[errnum])
        flattened_triggercnt_amd = []
        for cpuname in amd_cpu_names:
            # print('\n' + cpuname)
            for errnum in amd_errnums[cpuname]:
                # if not num_triggers_per_errnum[errnum]:
                    # print("\t{}".format(errnum))
                flattened_triggercnt_amd.append(num_triggers_per_errnum[errnum])

        countdict_intel = sorted(dict(Counter(flattened_triggercnt_intel)).items(), key=lambda item: item[0], reverse=True)
        counts_intel = list(map(lambda x: x[0], countdict_intel))
        Ys_intel = list(map(lambda x: x[1], countdict_intel))
        Ys_intel = list(map(lambda x: round(100*x/2057, 1), Ys_intel))
        countdict_amd = sorted(dict(Counter(flattened_triggercnt_amd)).items(), key=lambda item: item[0], reverse=True)
        counts_amd = list(map(lambda x: x[0], countdict_amd))
        Ys_amd = list(map(lambda x: x[1], countdict_amd))
        Ys_amd = list(map(lambda x: round(100*x/506, 1), Ys_amd))

        # Do not display the zero, will disturb the reader. The zero value will be mentioned in the text.
        counts_intel = counts_intel[:-1]
        Ys_intel = list(reversed(Ys_intel[:-1]))
        counts_amd = counts_amd[:-1]
        Ys_amd = list(reversed(Ys_amd[:-1]))

        ########################################
        # Update plot
        ########################################

        width = 2.5
        spacing = 1

        left_offset = spacing

        xticks = []

        fig = plt.figure(figsize=(6, 2.5))

        for trigger_class_id in range(len(counts_intel)):
            xticks.append( left_offset + trigger_class_id*(2*width + 2*spacing))

        Xs_intel = [xticks[tick_id] - width/2 for tick_id in range(len(xticks))]
        Xs_amd   = [xticks[tick_id] + width/2 for tick_id in range(len(xticks))]

        ax = fig.gca()
        ax.grid(axis='y')

        for tick_id in range(len(Ys_intel)):
            intel_bars = ax.bar(Xs_intel[tick_id], Ys_intel[tick_id], width, alpha=1, zorder=3, color='#0071c5', label='Intel' if tick_id == 0 else '')
            amd_bars   = ax.bar(Xs_amd[tick_id], Ys_amd[tick_id], width, alpha=1, zorder=3, color='#ED1C24', label='AMD' if tick_id == 0 else '')
            ax.bar_label(intel_bars)
            ax.bar_label(amd_bars)


        ax.set_axisbelow(True)
        ax.set_ylabel('Proportion of errata (\%)')
        ax.set_xlabel('Number of involved triggers')
        ax.set_ylim(0, 48)
        ax.set_xticks(xticks, reversed(counts_intel))
        ax.legend()
        fig.tight_layout()
        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        plt.savefig(os.path.join(target_dir, "numtrigsrequired.pdf"), dpi=300)
        plt.savefig(os.path.join(target_dir, "numtrigsrequired.png"), dpi=300)
