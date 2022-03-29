import luigi

from pipeline.classify.plottrigctxeff import TrigCtxEff

if __name__ == '__main__':
    num_workers = 1

    luigi.build([TrigCtxEff()], workers=num_workers, local_scheduler=True, log_level='INFO')
