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
            request = Message(self.env, self.id, "Hello, Server!", 10)
            yield from request.send(self.config['balancer_pipe'], self.client_pipe, random.uniform(1, 10))
            # yield self.env.timeout(random.uniform(1, 10))
            # self.balancer_pipe.put(request)
            print("[Client %d] Request sent" % self.id)

            # wait for response
            response = yield self.client_pipe.get()
            print("[Client %d] Response: %s" % (self.id, response.text))
