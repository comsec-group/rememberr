import luigi

from pipeline.classify.plotmsrs import PlotMSRs

if __name__ == '__main__':
    num_workers = 1

    luigi.build([PlotMSRs()], workers=num_workers, local_scheduler=True, log_level='INFO')
