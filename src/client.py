from enum import Enum
import random
import simpy
from src.message import Message
from src.simobj import SimObj


class ClientType(Enum):
    PC = "PC",
    Mobile = "Mobile"


class Client(SimObj):
    def __init__(self, env, id, config):
        super().__init__(env, id, config)

        self.client_pipe = simpy.Store(self.env)

        self.process = None

    def start(self):
        self.process = self.env.process(self.work())

    def work(self):
        while True:
            idle_time = random.uniform(1, 10)
            yield self.env.timeout(idle_time)

            # send request
            request = Message(self.env, self.id,
                              dict(
                                  static=True,
                                  guest=self.config['guest'],
                                  page_id=0))

            yield from request.send(self.config['balancer_pipe'], self.client_pipe, random.uniform(1, 10))

            print("[Client %d] Request: %d" % (self.id, request.data['page_id']))

            # wait for response
            response = yield self.client_pipe.get()
            print("[Client %d] Response: %d" % (self.id, response.data['page_id']))
