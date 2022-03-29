import luigi

from pipeline.plotheredityintel import HeredityIntel

if __name__ == '__main__':
    num_workers = 1

    luigi.build([HeredityIntel()], workers=num_workers, local_scheduler=True, log_level='INFO')
