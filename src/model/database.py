import simpy

from src.util.simobj import SimObj
from src.util.time import TrTime


class CoveringIndexQuery(TrTime):
    def __init__(self):
        super().__init__(1, 3)


class IndexQuery(TrTime):
    def __init__(self):
        super().__init__(10, 20)


class RangeQuery(TrTime):
    def __init__(self):
        super().__init__(30, 80)


class FullScanQuery(TrTime):
    def __init__(self):
        super().__init__(100, 300)


class Database(SimObj):
    def __init__(self, env, logger, id, config):
        super().__init__(env, logger, id, config)
        self.thread_pool = simpy.Resource(env, config['max_connections'])

    def query(self, q):
        thread_pool = self.thread_pool.request()
        yield thread_pool

        query_time = q.get()
        yield self.env.timeout(query_time)

        self.thread_pool.release(thread_pool)
