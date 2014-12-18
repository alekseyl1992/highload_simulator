import random
import simpy
from src.database import Database, FullScanQuery, CoveringIndexQuery, IndexQuery, RangeQuery
from src.pager import Pager
from src.time import TrTime
from src.balancer import Balancer, BalanceMode
from src.client import Client, ClientType
from src.server import Server

if __name__ == "__main__":
    env = simpy.Environment()
    start_time = env.now

    # create db
    db = Database(env, 0, dict(
        cores=4
    ))

    # create bd query pattern
    query_pattern = (
        dict(type=FullScanQuery,        count=lambda: int(random.randint(0, 99) > 90)),
        dict(type=CoveringIndexQuery,   count=lambda: random.randint(0, 10)),
        dict(type=IndexQuery,           count=lambda: random.randint(0, 2)),
        dict(type=RangeQuery,           count=lambda: random.randint(0, 2)),
    )

    # create servers
    servers = []
    for i in range(0, 4):
        server = Server(env, i, dict(
            cores=4,
            db=db,
            render_time=TrTime(10, 20),
            query_pattern=query_pattern,
            db_latency_time=TrTime(10, 22)
        ))

        servers.append(server)
        server.start()

    # create balancer
    balancer = Balancer(env, 0, dict(
        mode=BalanceMode.ROUND_ROBIN,
        servers=servers,
        cache_size=100,
        render_time=TrTime(2, 8),
        balance_time=TrTime(1, 2),
        max_clients=100000))
    balancer.start()

    # create pager
    pager = Pager(env, dict(
        dynamic_pages_count=10,
        static_files_count=50,
        static_files_per_page=10
    ))

    # create clients
    for i in range(0, 100):
        client = Client(env, i, dict(
            balancer_pipe=balancer.get_clients_pipe(),
            pager=pager,
            type=ClientType.PC,
            guest=True,
            idle_time=TrTime(1*1000, 20*1000),
            uplink_speed=TrTime(10, 30),
            downlink_speed=TrTime(10, 30)
        ))
        client.start()

    env.run(until=1*60*1000)

    # analise statistics
    print("-----------------------")
    print("Statistics")
    print("-----------------------")

    rps = float(servers[0].get_requests_count()) / (env.now - start_time)
    print("RPS: %f" % rps)

