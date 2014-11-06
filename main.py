import simpy


class SimObj(object):
    def __init__(self, env):
        self.env = env


class Server(SimObj):
    def __init__(self, env, name, cores_count):
        super().__init__(env)
        self.name = name
        self.coresCount = cores_count

        self.processes = []

    def start(self):
        # fork
        for pid in range(0, self.coresCount):
            self.processes.append(env.process(self.work(pid)))

    def work(self, pid):
        print("Server started at %d" % env.now)

        while True:
            req_time = 10
            yield env.timeout(req_time)
            print("[Server: %d, pid: %d] Request handled at %d" % (self.name, pid, env.now))


if __name__ == "__main__":
    env = simpy.Environment()

    for i in range(0, 10):
        server = Server(env, i, 4)
        server.start()

    env.run(until=30)