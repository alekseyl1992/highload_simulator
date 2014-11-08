import simpy
from src.balancer import Balancer, BalanceMode
from src.client import Client
from src.server import Server

if __name__ == "__main__":
    env = simpy.Environment()
    start_time = env.now

    # create servers
    servers = []
    for i in range(0, 4):
        server = Server(env, i, 10)
        servers.append(server)
        server.start()

    # create balancer
    balancer = Balancer(env, BalanceMode.ROUND_ROBIN, servers)
    balancer.start()

    # create clients
    for i in range(0, 100):
        client = Client(env, balancer.get_clients_pipe(), 10, 20, i)
        client.start()

    env.run(until=1000)

    # analise statistics
    print("-----------------------")
    print("Statistics")
    print("-----------------------")

    rps = float(servers[0].get_requests_count()) / (env.now - start_time)
    print("RPS: %f" % rps)

