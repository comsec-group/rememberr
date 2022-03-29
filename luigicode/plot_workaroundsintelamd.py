import luigi

from pipeline.plotworkaroundsintelamd import WorkaroundsIntelAMD

if __name__ == '__main__':
    num_workers = 1

    luigi.build([WorkaroundsIntelAMD()], workers=num_workers, local_scheduler=True, log_level='INFO')

