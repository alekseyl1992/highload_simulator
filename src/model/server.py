import random

import simpy

from src.util.message import Message
from src.util.simobj import SimObj


class Server(SimObj):
    def __init__(self, env, logger, id, config):
        super().__init__(env, logger, id, config)

        self.server_pipe = simpy.Store(self.env)
        self.requests_count = 0

        self.processes = []

    def get_connections_count(self):
        return len(self.server_pipe.items)

    def get_pipe(self):
        return self.server_pipe

    def start(self):
        self.logger.log(self, "Server %d started at %d" % (self.id, self.env.now))

        # fork
        for pid in range(0, self.config['cores']):
            self.processes.append(self.env.process(self.work(pid)))

    def work(self, pid):
        while True:
            # wait for request
            request = yield self.server_pipe.get()

            self.logger.log(self, "[Server: %d, pid: %d] Request from %d: page %d handled at %d"
                  % (self.id, pid, request.source_id, request.data['page_id'], self.env.now))

            # query db
            db_latency_time = self.config['db_latency_time']
            for query in self.config['query_pattern']:
                query_obj = query['type']()
                query_count = query['count']()

                for i in range(0, query_count):
                    yield self.env.timeout(db_latency_time.get())
                    yield from self.config['db'].query(query_obj)

            # render page
            yield self.env.timeout(self.config['render_time'].get())

            # send response
            response = Message(self.env, self.id, request.data)
            balancer_pipe = request.get_next_response_pipe()
            client_pipe = request.get_next_response_pipe()

            yield from response.send(balancer_pipe, client_pipe,
                                     self.config['balancer_latency_time'].get())

            self.requests_count += 1

    def get_requests_count(self):
        return self.requests_count
