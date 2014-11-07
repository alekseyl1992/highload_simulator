
class Message(object):
    def __init__(self, env, source_id, text, size):
        self.env = env
        self.time = env.now
        self.source_id = source_id
        self.response_pipes = []
        self.text = text
        self.size = size

    def send(self, pipe, response_pipe, send_time):
        if response_pipe is not None:
            self.response_pipes.append(response_pipe)

        yield self.env.timeout(send_time)
        pipe.put(self)

    def send_async(self, pipe, response_pipe, send_time):
        return self.env.process(self.send(pipe, response_pipe, send_time))

    def get_next_response_pipe(self):
        return self.response_pipes.pop()