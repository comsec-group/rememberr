import luigi

from pipeline.classify.plotcorrtrigctxteff import CorrTrigCtxtEff 

if __name__ == '__main__':
    num_workers = 1

    luigi.build([CorrTrigCtxtEff()], workers=num_workers, local_scheduler=True, log_level='INFO')
