# Plots the trigger classes for both vendors.

import luigi

from pipeline.classify.plottriggersbetweenvendors import PlotTriggerBetweenVendors 

if __name__ == '__main__':
    num_workers = 1

    luigi.build([PlotTriggerBetweenVendors()], workers=num_workers, local_scheduler=True, log_level='INFO')
