import luigi

from pipeline.plothereditybarsintel import HeredityBarsIntel

if __name__ == '__main__':
    num_workers = 1

    luigi.build([HeredityBarsIntel()], workers=num_workers, local_scheduler=True, log_level='INFO')
