import luigi

from pipeline.estimateblurtrg import EstimateBlurTrg

if __name__ == '__main__':
    num_workers = 1

    luigi.build([EstimateBlurTrg()], workers=num_workers, local_scheduler=True, log_level='INFO')
