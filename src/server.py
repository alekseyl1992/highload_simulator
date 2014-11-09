import random
import simpy
from src.database import FullScanQuery
from src.message import Message
from src.simobj import SimObj


class Server(SimObj):
    def __init__(self, env, id, config):
        super().__init__(env, id, config)

        self.server_pipe = simpy.Store(self.env)
        self.requests_count = 0

        self.processes = []

    def get_connections_count(self):
        return len(self.server_pipe.items)

    def get_pipe(self):
        return self.server_pipe

    def start(self):
        print("Server %d started at %d" % (self.id, self.env.now))

        # fork
        for pid in range(0, self.config['cores']):
            self.processes.append(self.env.process(self.work(pid)))

    def work(self, pid):
        while True:
            # wait for request
            request = yield self.server_pipe.get()

            req_time = random.uniform(10, 20)
            yield self.env.timeout(req_time)
            print("[Server: %d, pid: %d] Request from %d: \"%s\" handled at %d"
                  % (self.id, pid, request.source_id, request.text, self.env.now))

            # query db
            yield from self.config['db'].query(FullScanQuery())

            # render page

            # send response
            response = Message(self.env, self.id, request.data)
            balancer_pipe = request.get_next_response_pipe()
            client_pipe = request.get_next_response_pipe()
            yield from response.send(balancer_pipe, client_pipe, random.uniform(1, 2))

            self.requests_count += 1

    def get_requests_count(self):
        return self.requests_count
