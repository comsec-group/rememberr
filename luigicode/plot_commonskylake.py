import luigi

from pipeline.plotcommonskylake import CommonSkylake

if __name__ == '__main__':
    num_workers = 1

    luigi.build([CommonSkylake()], workers=num_workers, local_scheduler=True, log_level='INFO')
