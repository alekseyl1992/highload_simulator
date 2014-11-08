import random
import simpy
from src.message import Message
from src.simobj import SimObj


class Server(SimObj):
    def __init__(self, env, id, cores_count):
        super().__init__(env)
        self.id = id
        self.coresCount = cores_count
        self.server_pipe = simpy.Store(self.env)
        self.requests_count = 0

        self.processes = []

    def get_pipe(self):
        return self.server_pipe

    def start(self):
        print("Server started at %d" % self.env.now)

        # fork
        for pid in range(0, self.coresCount):
            self.processes.append(self.env.process(self.work(pid)))

    def work(self, pid):
        while True:
            # wait for request
            request = yield self.server_pipe.get()

            req_time = random.uniform(10, 20)
            yield self.env.timeout(req_time)
            print("[Server: %d, pid: %d] Request from %d: \"%s\" handled at %d"
                  % (self.id, pid, request.source_id, request.text, self.env.now))

            # send response
            response = Message(self.env, self.id, "Hello, Client! from %d to %d!" % (self.id, request.source_id), 20)
            balancer_pipe = request.get_next_response_pipe()
            client_pipe = request.get_next_response_pipe()
            yield from response.send(balancer_pipe, client_pipe, random.uniform(1, 2))

            self.requests_count += 1

    def get_requests_count(self):
        return self.requests_count
