# Plots the timeline of trigger representations. Currently, only Intel is represented, as it contains the most chronological information.

from collections import defaultdict
import json
import luigi
import os
from pathlib import Path
import pprint

import matplotlib.pyplot as plt
from pipeline.uniqueintel import UniqueIntel
from pipeline.uniqueamd import UniqueAMD
from common import intel_cpu_names, intel_cpu_prettynames, amd_cpu_names, plainify_str, trigger_classes_map, trigger_classes, triggers

from matplotlib import rc
rc('font', **{'family':'serif', 'serif':['Times']})
rc('text', usetex=True)

NUM_TRIGGER_CLASSSES = len(trigger_classes)
PLOT_ABSOLUTE = False

# @brief finds the parsed details, given a CPU name.
def cpuname_to_parseddetailspath(cpuname: str) -> str:
    if "ERRATA_BUILDDIR" not in os.environ:
        raise ValueError("Environment variable ERRATA_BUILDDIR must be defined. Please source env.sh.")
    return os.path.join(os.environ['ERRATA_BUILDDIR'], 'parsed', '{}_details.json'.format(cpuname))

#####
# Luigi task
#####

class TriggerTimeline(luigi.Task):
    def __init__(self, *args, **kwargs):
        super(TriggerTimeline, self).__init__(*args, **kwargs)

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
        return [UniqueIntel(), UniqueAMD()]

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
        # dict[trigger_type][design_name] = num_triggers
        num_triggers_per_design = defaultdict(lambda : defaultdict(int))

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
        for cpuname in intel_cpu_names:
            cpu_detailspath = cpuname_to_parseddetailspath(cpuname)
            with open(cpu_detailspath, 'r') as f:
                intel_errnums[cpuname] = list(map(lambda x: plainify_str(x['title']), json.load(f).values()))

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
        # Process all data for Intel.
        ########################################

        for cpuname in intel_cpu_names:
            for errnum in intel_errnums[cpuname]:
                if plainify_str(errnum) in intel_all_unique_plaintitles:
                    for trigger in triggers:
                        if errnum in intel_trigger_categorization_bool[trigger]:
                            num_triggers_per_design[trigger][cpuname] += int(intel_trigger_categorization_bool[trigger][errnum])

        ########################################
        # Process all data for AMD.
        ########################################

        for cpuname in amd_cpu_names:
            for errnum in amd_errnums[cpuname]:
                for trigger in triggers:
                    num_triggers_per_design[trigger][cpuname] += int(amd_trigger_categorization_bool[trigger][errnum])

        ########################################
        # Gen trigger classs data
        ########################################

        num_triggers_class_per_design = defaultdict(lambda : defaultdict(int))
        for trigger in num_triggers_per_design:
            for design in num_triggers_per_design[trigger]:
                num_triggers_class_per_design[trigger_classes_map[trigger]][design] += num_triggers_per_design[trigger][design]

        # Relative numbers
        num_triggers_class_per_design_baseline = defaultdict(int)
        for triggerclass in num_triggers_class_per_design:
            for cpuname in num_triggers_class_per_design[triggerclass]:
                num_triggers_class_per_design_baseline[cpuname] += num_triggers_class_per_design[triggerclass][cpuname]
        num_triggers_class_per_design_relative = defaultdict(lambda : defaultdict(int))
        for triggerclass in num_triggers_class_per_design:
            for cpuname in num_triggers_class_per_design[triggerclass]:
                assert 'amd' in cpuname or 'intel' in cpuname
                if 'intel' in cpuname:
                    num_triggers_class_per_design_relative[triggerclass][cpuname] = 100* num_triggers_class_per_design[triggerclass][cpuname] / len(intel_errnums[cpuname])
                else:
                    num_triggers_class_per_design_relative[triggerclass][cpuname] = 100* num_triggers_class_per_design[triggerclass][cpuname] / len(amd_errnums[cpuname])

        ########################################
        # Plot by class (group)
        ########################################

        width = 0.1
        spacing = 0.1

        left_offset = width * len(trigger_classes) / 2

        xticks = []
        # dict[triggerclassid]
        rects_x = defaultdict(float)
        rects_y = defaultdict(float)

        fig = plt.figure(figsize=(8, 3.8))
        ax = fig.gca()

        for i in range(len(intel_cpu_names)):
            xticks.append( left_offset + i*(width*len(trigger_classes) + 2*spacing))

        for triggerclassid, triggerclassname in enumerate(num_triggers_class_per_design):
            rects_x[triggerclassid] = [xticks[cpuid] + width*(triggerclassid - len(trigger_classes)/2) + width/2 for cpuid in range(len(intel_cpu_names))]
            if PLOT_ABSOLUTE:
                rects_y[triggerclassid] = [num_triggers_class_per_design[triggerclassname][cpuname] for cpuname in intel_cpu_names]
            else:
                rects_y[triggerclassid] = [num_triggers_class_per_design_relative[triggerclassname][cpuname] for cpuname in intel_cpu_names]

        ax.grid(axis='y')
        for triggerclassid, triggerclassname in enumerate(num_triggers_class_per_design):
            ax.bar(rects_x[triggerclassid], rects_y[triggerclassid], width, alpha=1, zorder=3, label=triggerclassname)

        if PLOT_ABSOLUTE:
            ax.set_ylabel("Number of affected errata")
            ax.legend(framealpha=1)
        else:
            ax.set_ylabel("Relative trigger representation (\%)")
            ax.legend(ncol=4, framealpha=1)

        ax.set_xticks(xticks, intel_cpu_prettynames.values(), rotation=90)
        fig.tight_layout()

        # Save more figures than what luigi would.
        target_dir = os.path.join(os.environ["ERRATA_BUILDDIR"], 'figures')
        Path(target_dir).mkdir(parents=True, exist_ok=True)
        if PLOT_ABSOLUTE:
            plt.savefig(os.path.join(target_dir, "triggertimeline_absolute.pdf"), dpi=300)
            plt.savefig(os.path.join(target_dir, "triggertimeline_absolute.png"), dpi=300)
        else:
            plt.savefig(os.path.join(target_dir, "triggertimeline_relative.pdf"), dpi=300)
            plt.savefig(os.path.join(target_dir, "triggertimeline_relative.png"), dpi=300)
