
class Message(object):
    def __init__(self, env, source_id, data):
        self.env = env
        self.time = env.now
        self.source_id = source_id
        self.response_pipes = []
        self.data = data

    def send(self, pipe, response_pipe, send_time, callback=None):
        if response_pipe is not None:
            self.response_pipes.append(response_pipe)

        yield self.env.timeout(send_time)
        pipe.put(self)

        if callback is not None:
            callback()

    def send_async(self, pipe, response_pipe, send_time, callback=None):
        return self.env.process(self.send(pipe, response_pipe, send_time, callback))

    def get_next_response_pipe(self):
        return self.response_pipes.pop()