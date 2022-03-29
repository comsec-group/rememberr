# Plots the timeline of trigger representations. Currently, only Intel is represented, as it contains the most chronological information.

import luigi

from pipeline.classify.plottriggertimeline import TriggerTimeline 

if __name__ == '__main__':
    num_workers = 1

    luigi.build([TriggerTimeline()], workers=num_workers, local_scheduler=True, log_level='INFO')
