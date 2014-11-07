import simpy
import random


class SimObj(object):
    def __init__(self, env):
        self.env = env


class Message(object):
    def __init__(self, env, source_id, response_pipe, text, size):
        self.time = env.now
        self.source_id = source_id
        self.response_pipe = response_pipe
        self.text = text
        self.size = size


class Client(SimObj):
    def __init__(self, env, server_pipe, uplink_speed, downlink_speed, id):
        super().__init__(env)

        self.client_pipe = simpy.Store(self.env)
        self.server_pipe = server_pipe
        self.type = "PC"
        self.id = id
        self.uplink_speed = uplink_speed
        self.downlink_speed = downlink_speed

        self.process = None

    def start(self):
        self.process = self.env.process(self.work())

    def work(self):
        while True:
            idle_time = random.uniform(1, 10)
            yield self.env.timeout(idle_time)

            # send request
            request = Message(self.env, self.id, self.client_pipe, "Hello, Server!", 10)
            self.server_pipe.put(request)
            print("[Client %d] Request sent" % self.id)

            # wait for response
            response = yield self.client_pipe.get()
            print("[Client %d] Response: %s" % (self.id, response.text))


class Server(SimObj):
    def __init__(self, env, id, cores_count):
        super().__init__(env)
        self.id = id
        self.coresCount = cores_count
        self.server_pipe = simpy.Store(self.env)

        self.processes = []

    def get_pipe(self):
        return self.server_pipe

    def start(self):
        print("Server started at %d" % env.now)

        # fork
        for pid in range(0, self.coresCount):
            self.processes.append(self.env.process(self.work(pid)))

    def work(self, pid):
        while True:
            # wait for request
            request = yield self.server_pipe.get()

            req_time = random.uniform(10, 20)
            yield env.timeout(req_time)
            print("[Server: %d, pid: %d] Request from %d: \"%s\" handled at %d"
                  % (self.id, pid, request.source_id, request.text, env.now))

            # send response
            response = Message(self.env, self.id, None, "Hello, Client! from %d to %d!" % (self.id, request.source_id), 20)
            request.response_pipe.put(response)


if __name__ == "__main__":
    env = simpy.Environment()

    server = Server(env, 1, 2)
    server.start()

    client1 = Client(env, server.get_pipe(), 10, 20, 1)
    client1.start()

    client2 = Client(env, server.get_pipe(), 10, 20, 2)
    client2.start()


    env.run(until=100)