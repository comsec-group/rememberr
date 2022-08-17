# Plots the FLT triggers for both vendors.

import luigi

from pipeline.classify.plottriggersbetweenvendorsfea import PlotTriggerBetweenVendorsFEA

if __name__ == '__main__':
    num_workers = 1

    luigi.build([PlotTriggerBetweenVendorsFEA()], workers=num_workers, local_scheduler=True, log_level='INFO')
