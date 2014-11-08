import simpy
from src.database import Database
from src.time import Time
from src.balancer import Balancer, BalanceMode
from src.client import Client, ClientType
from src.server import Server

if __name__ == "__main__":
    env = simpy.Environment()
    start_time = env.now

    # create db
    db = Database(env, 0, dict(cores=4))

    # create servers
    servers = []
    for i in range(0, 4):
        server = Server(env, i, dict(cores=4, db=db, render_time=Time(10, 20)))
        servers.append(server)
        server.start()

    # create balancer
    balancer = Balancer(env, 0, dict(
        mode=BalanceMode.ROUND_ROBIN,
        servers=servers,
        balance_time=Time(2, 1)))
    balancer.start()

    # create clients
    for i in range(0, 100):
        client = Client(env, i,
                        dict(balancer_pipe=balancer.get_clients_pipe(),
                             type=ClientType.PC,
                             uplink_speed=Time(10, 1),
                             downlink_speed=Time(20, 2)))
        client.start()

    env.run(until=1000)

    # analise statistics
    print("-----------------------")
    print("Statistics")
    print("-----------------------")

    rps = float(servers[0].get_requests_count()) / (env.now - start_time)
    print("RPS: %f" % rps)

