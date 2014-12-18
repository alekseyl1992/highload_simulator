from enum import Enum
import math

import simpy

from src.util.message import Message
from src.util.simobj import SimObj


class BalanceMode(Enum):
    ROUND_ROBIN = 1
    LEAST_CONN = 2


class Balancer(SimObj):
    def __init__(self, env, logger, id, config):
        super().__init__(env, logger, id, config)

        mode = config['mode']
        if mode == BalanceMode.ROUND_ROBIN:
            self.get_next_server_id = self._round_robin
        elif mode == BalanceMode.LEAST_CONN:
            self.get_next_server_id = self._least_conn
        else:
            raise NotImplementedError("Such balance mode not implemented")

        self.current_server_id = 0
        self.clients_pipe = simpy.Store(self.env, self.config['max_clients'])
        self.requests_pipe = simpy.Store(self.env)
        self.servers_pipe = simpy.Store(self.env)

        self.requests_process = None
        self.send_processes = []
        self.recv_processes = []

        self.requests_count = 0
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
        self.logger.log(self, "Balancer started at %d" % self.env.now)

        self.requests_process = self.env.process(self.requests_handler())

        for i in range(0, self.config['sender_processes']):
            self.send_processes.append(self.env.process(self.sender()))

        for i in range(0, self.config['receiver_processes']):
            self.recv_processes.append(self.env.process(self.receiver()))

    def _render_page(self, request):
        render_time = self.config['render_time'].get()
        yield self.env.timeout(render_time)

        # put response to send queue
        response = Message(self.env, self.id, request.data)
        response.response_pipes.append(request.get_next_response_pipe())

        self.servers_pipe.put(response)

    def requests_handler(self):
        """
        Asynchronously reads requests from clients to requests pipe
        """

        while True:
            request = yield self.clients_pipe.get()

            self._acquire_connection()
            self.env.process(self.handle_request(request))

    def handle_request(self, request):
        """
        Wait some time depending on client uplink_speed and connections_count
        Copying request from clients pipe to requests pipe
        :param request:
        """

        yield self.env.timeout(
            request.data['uplink_speed'].get() * (1 + math.log(self.connections_count, 10)))

        self.requests_pipe.put(request)

    def sender(self):
        """
        Sends request asynchronously to server
        (using balancing, cache, static)
        """
        while True:
            request = yield self.requests_pipe.get()

            # handle static
            if request.data['static']:
                yield from self._render_page(request)
                continue

            # handle cache
            if request.data['guest'] and self.in_cache(request.data['page_id']):
                yield from self._render_page(request)
                continue

            # handle balancing
            server_id = self.get_next_server_id()
            server_pipe = self.config['servers'][server_id].get_pipe()

            # send request to server asynchronously
            balance_time = self.config['balance_time'].get()
            request.send_async(server_pipe, self.servers_pipe, balance_time)

    def receiver(self):
        """
        Sends data from servers back to client
        (caching)
        """
        while True:
            # wait for any response from servers
            response = yield self.servers_pipe.get()

            client_pipe = response.get_next_response_pipe()

            # handle cache
            if response.data['guest'] and not response.data['static']:
                if len(self.cache) > self.config['cache_size']:
                    self.cache.pop(0)

                self.cache.append((self.env.now, response.data['page_id']))

            # send response back to the client asynchronously
            response.send_async(client_pipe,
                                None,
                                response.data['downlink_speed'].get() * (1 + math.log(self.connections_count, 10)),
                                self._release_connection)

    def _acquire_connection(self):
        self.connections_count += 1

    def _release_connection(self):
        self.connections_count -= 1
        self.requests_count += 1

    def get_requests_count(self):
        return self.requests_count

    def in_cache(self, page_id):
        for i, entry in enumerate(self.cache):
            if entry[1] == page_id:
                if entry[0] < (self.env.now + self.config['cache_time']):
                    return True  # found and fresh
                else:
                    self.cache.pop(i)
                    return False  # found, but obsolete

        return False  # not found