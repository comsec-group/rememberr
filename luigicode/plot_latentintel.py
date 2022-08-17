import luigi

from pipeline.plotlatentintel import LatentIntel

if __name__ == '__main__':
    num_workers = 1

    luigi.build([LatentIntel()], workers=num_workers, local_scheduler=True, log_level='INFO')
