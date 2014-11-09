import random
from src.message import Message


class Pager:
    def __init__(self, env, config):
        self.env = env
        self.config = config

    def get_random_page_requests(self, client):
        requests = []

        # main page (dynamic) request
        dynamic_page_id = random.randint(0, self.config['dynamic_pages_count'] - 1)
        request = Message(self.env, client.id,
                          dict(
                              static=False,
                              guest=client.config['guest'],
                              page_id=dynamic_page_id))
        requests.append(request)

        # static files (scripts, styles, images)
        for i in range(0, self.config['static_files_per_page']):
            static_id_min = self.config['dynamic_pages_count']
            static_files_count = self.config['static_files_count']

            static_file_id = random.randint(static_id_min, static_id_min + static_files_count - 1)

            static_request = Message(self.env, client.id, dict(
                static=True,
                guest=client.config['guest'],
                page_id=static_file_id
            ))

            requests.append(static_request)

        return requests
