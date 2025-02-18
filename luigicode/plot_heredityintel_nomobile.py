import luigi

from pipeline.plotheredityintelnomobile import HeredityIntelNoMobile

if __name__ == '__main__':
    num_workers = 1

    luigi.build([HeredityIntelNoMobile()], workers=num_workers, local_scheduler=True, log_level='INFO')
