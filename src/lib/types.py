from enum import Enum


def typename(t):
    return type(t).__name__


class Stage(Enum):
    ANY = "any"
    BOOTSTRAP = "bootstrap"
    BUILD = "build"
    TEST = "test"
    DEPLOY = "deploy"
