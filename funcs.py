from itertools import combinations  # noqa: F401
from operator import add, sub  # noqa: F401


def divide_by_zero(x):
    return x / 0


def hello_world():
    import __hello__  # noqa: F401


def antigravity():
    import antigravity  # noqa: F401


def this():
    import this  # noqa: F401


def return_314159():
    return hash(float("inf"))
