import random
import simpy
from src.simobj import SimObj
from src.time import Time


class CoveringIndexQuery(Time):
    def __init__(self):
        super().__init__(2, 1)


class IndexQuery(Time):
    def __init__(self):
        super().__init__(20, 10)


class RangeQuery(Time):
    def __init__(self):
        super().__init__(80, 30)


class FullScanQuery(Time):
    def __init__(self):
        super().__init__(200, 100)


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
