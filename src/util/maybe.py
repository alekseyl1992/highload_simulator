import random


def maybe(a, b, pa):
    if random.randint(0, 99) > (100 - pa):
        return a
    else:
        return b