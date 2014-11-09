import random
import simpy
from src.simobj import SimObj
from src.time import TrTime


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
    def __init__(self, env, id, config):
        super().__init__(env, id, config)
        self.cpu = simpy.Resource(env, config['cores'])
        self.disk = simpy.Resource(env, 1)

    def query(self, q):
        cpu = self.cpu.request()
        yield cpu

        # request disk if needed
        disk = None
        if isinstance(q, RangeQuery) or isinstance(q, FullScanQuery):
            disk = self.disk.request()
            yield disk

        query_time = random.normalvariate(q.m, q.s)
        yield self.env.timeout(query_time)

        if disk is not None:
            self.disk.release(disk)

        self.cpu.release(cpu)
