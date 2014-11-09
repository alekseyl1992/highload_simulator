from enum import Enum
import random
import simpy
from src.message import Message
from src.simobj import SimObj


class BalanceMode(Enum):
    ROUND_ROBIN = 1
    LEAST_CONN = 2


class Balancer(SimObj):
    def __init__(self, env, id, config):
        super().__init__(env, id, config)

        mode = config['mode']
        if mode == BalanceMode.ROUND_ROBIN:
            self.get_next_server_id = self._round_robin
        elif mode == BalanceMode.LEAST_CONN:
            self.get_next_server_id = self._least_conn
        else:
            raise NotImplementedError("Such balance mode not implemented")

        self.current_server_id = 0
        self.clients_pipe = simpy.Store(self.env)
        self.servers_pipe = simpy.Store(self.env)

        self.send_process = None
        self.recv_process = None

        self.connections_count = 0

        self.cache = []  # cached pages' ids circular buffer

    def get_clients_pipe(self):
        return self.clients_pipe

    def get_servers_pipe(self):
        return self.servers_pipe

    def _round_robin(self):
        self.current_server_id = (self.current_server_id + 1) % len(self.config['servers'])
        return self.current_server_id

    def _least_conn(self):
        min_conn_count = None
        server_id = None

        for i, server in enumerate(self.config['servers']):
            conn_count = server.get_connections_count()
            if min_conn_count is None or conn_count < min_conn_count:
                min_conn_count = conn_count
                server_id = i

        return server_id

    def start(self):
        print("Balancer started at %d" % self.env.now)

        self.send_process = self.env.process(self.sender())
        self.recv_process = self.env.process(self.receiver())

    def _render_page(self, request):
        render_time = self.config['render_time'].get()
        yield self.env.timeout(render_time)

        # put response to send queue
        response = Message(self.env, self.id, request.data)
        response.response_pipes.append(request.get_next_response_pipe())

        self.servers_pipe.put(response)
        self._release_connection()

    def sender(self):
        """
        Sends request asynchronously to server
        (using balancing, cache, static)
        """
        while True:
            request = yield self.clients_pipe.get()
            self.connections_count += 1

            # handle static
            if request.data['static']:
                yield from self._render_page(request)
                continue

            # handle cache
            if request.data['guest'] and request.data['page_id'] in self.cache:
                yield from self._render_page(request)
                continue

            # handle balancing
            server_id = self.get_next_server_id()
            server_pipe = self.config['servers'][server_id].get_pipe()

            # send request to server asynchronously
            # TODO: time should be affected by connections_count
            balance_time = self.config['balance_time'].get()
            request.send_async(server_pipe, self.servers_pipe, balance_time, self._release_connection)

    def receiver(self):
        """
        Sends data from servers back to client
        (caching)
        """
        while True:
            # wait for any response from servers
            response = yield self.servers_pipe.get()
            self.connections_count += 1

            client_pipe = response.get_next_response_pipe()

            # handle cache
            if response.data['guest']:
                if len(self.cache) > self.config['cache_size']:
                    self.cache.pop(0)

                self.cache.append(response.data['page_id'])

            # send response back to the client asynchronously
            # TODO: time should relate on client's type and/or speed
            response.send_async(client_pipe, None, random.uniform(10, 22), self._release_connection)

    def _release_connection(self):
        self.connections_count -= 1