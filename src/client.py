from enum import Enum
import random
import simpy
from src.message import Message
from src.simobj import SimObj


class ClientType(Enum):
    PC = "PC",
    Mobile = "Mobile"


class Client(SimObj):
    def __init__(self, env, logger, id, config):
        super().__init__(env, logger, id, config)

        self.client_pipe = simpy.Store(self.env)

        self.process = None

    def start(self):
        self.process = self.env.process(self.work())

    def work(self):
        while True:
            idle_time = self.config['idle_time']
            yield self.env.timeout(idle_time.get())

            # load next page
            requests = self.config['pager'].get_random_page_requests(self)
            for request in requests:
                yield from request.send(self.config['balancer_pipe'],
                                        self.client_pipe,
                                        self.config['uplink_speed'].get())

                self.logger.log(self, "[Client %d] Request: %d" % (self.id, request.data['page_id']))

                # wait for response
                response = yield self.client_pipe.get()
                self.logger.log(self, "[Client %d] Response: %d" % (self.id, response.data['page_id']))
