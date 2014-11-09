import random


class TrTime(object):
    def __init__(self, low, high, mode=None):
        self.low = low
        self.high = high
        self.mode = mode

    def get(self):
        return random.triangular(self.low, self.high, self.mode)