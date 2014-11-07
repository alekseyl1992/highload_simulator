import random
import simpy
from src.message import Message
from src.simobj import SimObj


class Client(SimObj):
    def __init__(self, env, balancer_pipe, uplink_speed, downlink_speed, id):
        super().__init__(env)

        self.client_pipe = simpy.Store(self.env)
        self.balancer_pipe = balancer_pipe
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
            request = Message(self.env, self.id, "Hello, Server!", 10)
            request.send(self.balancer_pipe, self.client_pipe, random.uniform(1, 10))
            # yield self.env.timeout(random.uniform(1, 10))
            # self.balancer_pipe.put(request)
            print("[Client %d] Request sent" % self.id)

            # wait for response
            response = yield self.client_pipe.get()
            print("[Client %d] Response: %s" % (self.id, response.text))
