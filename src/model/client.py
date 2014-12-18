from enum import Enum

import simpy

from src.util.simobj import SimObj


class ClientType(Enum):
    PC = "PC",
    Mobile = "Mobile"


class Client(SimObj):
    def __init__(self, env, logger, id, config):
        super().__init__(env, logger, id, config)

        self.client_pipe = simpy.Store(self.env)

        self.requests_sent = 0
        self.requests_sent_time = 0

        self.process = None

    def start(self):
        self.process = self.env.process(self.work())

    def work(self):
        while True:
            page_idle_time = self.config['page_idle_time']
            yield self.env.timeout(page_idle_time.get())

            # load next page
            requests = self.config['pager'].get_random_page_requests(self)
            for request in requests:
                request_idle_time = self.config['request_idle_time']
                yield self.env.timeout(request_idle_time.get())

                request_time = self.env.now

                yield from request.send(self.config['balancer_pipe'],
                                        self.client_pipe,
                                        self.config['uplink_speed'].get())

                self.logger.log(self, "[Client %d] Request: %d" % (self.id, request.data['page_id']))

                # wait for response
                response = yield self.client_pipe.get()
                self.logger.log(self, "[Client %d] Response: %d" % (self.id, response.data['page_id']))

                # statistics
                self.requests_sent += 1
                self.requests_sent_time += self.env.now - request_time

    def get_average_request_time(self):
        if self.requests_sent == 0:
            return 0

        return self.requests_sent_time / self.requests_sent