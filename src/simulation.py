import random

import simpy

from src.model.database import Database, FullScanQuery, CoveringIndexQuery, IndexQuery, RangeQuery
from src.util import maybe
from src.util.logger import Logger
from src.util.pager import Pager
from src.util.time import TrTime
from src.model.balancer import Balancer, BalanceMode
from src.model.client import Client, ClientType
from src.model.server import Server


class Simulation:
    def __init__(self):
        self.logger = Logger(self.__class__.__name__)

    def start(self, servers_count):

        env = simpy.Environment()
        start_time = env.now

        # create db
        db = Database(env, self.logger, 0, dict(
            max_connections=100
        ))

        # create bd query pattern
        query_pattern = (
            dict(type=FullScanQuery,        count=lambda: maybe.maybe(0, 1, 90)),
            dict(type=CoveringIndexQuery,   count=lambda: random.randint(0, 10)),
            dict(type=IndexQuery,           count=lambda: random.randint(0, 2)),
            dict(type=RangeQuery,           count=lambda: random.randint(0, 2)),
        )

        # create servers
        servers = []
        for i in range(0, servers_count):
            server = Server(env, self.logger, i, dict(
                cores=20,
                db=db,
                render_time=TrTime(30, 100),
                query_pattern=query_pattern,
                db_latency_time=TrTime(20, 30),
                balancer_latency_time=TrTime(10, 20)
            ))

            servers.append(server)
            server.start()

        # create balancer
        balancer = Balancer(env, self.logger, 0, dict(
            mode=BalanceMode.ROUND_ROBIN,
            servers=servers,
            cache_size=100,
            cache_time=1*30*1000,  # half of minute
            render_time=TrTime(2, 8),
            balance_time=TrTime(1, 2),
            sender_processes=4,
            receiver_processes=4,
            max_clients=100000))
        balancer.start()

        # create pager
        pager = Pager(env, dict(
            dynamic_pages_count=10,
            static_files_count=50,
            static_files_per_page=3
        ))

        # create clients
        clients = []
        for i in range(0, 1000):
            client = Client(env, self.logger, i, dict(
                balancer_pipe=balancer.get_clients_pipe(),
                pager=pager,
                type=ClientType.PC,
                guest=maybe.maybe(True, False, 50),
                page_idle_time=TrTime(1*1000, 3*1000),
                request_idle_time=TrTime(0.1*1000, 0.2*1000),
                uplink_speed=TrTime(1, 3),
                downlink_speed=TrTime(10, 30)
            ))
            clients.append(client)
            client.start()

        env.run(until=10*60*1000)  # 10 minutes

        # analise statistics
        self.logger.log(self, "-----------------------")
        self.logger.log(self, "Statistics (for %s servers)" % servers_count)
        self.logger.log(self, "-----------------------")

        rps = float(balancer.get_requests_count()) / (env.now - start_time) * 1000
        self.logger.log(self, "[Balancer] RPS: %f" % rps)

        for server in servers:
            rps = float(server.get_requests_count()) / (env.now - start_time) * 1000
            self.logger.log(self, "[Server %d] RPS: %f" % (server.id, rps))

        average_request_time = 0
        for client in clients:
            average_request_time += client.get_average_request_time()

        average_request_time /= len(clients)

        self.logger.log(self, "Average request time: %f" % average_request_time)

        return average_request_time
