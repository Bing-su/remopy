from itertools import combinations  # noqa: F401
from operator import add, sub  # noqa: F401

MY_TOKEN = "MY_TOKEN"


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


def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def is_prime(n):
    return n > 1 and all(n % i for i in range(2, int(n**0.5) + 1))
