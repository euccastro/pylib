import sys


class obj(dict):

    def __init__(self, *args, **kw):
        dict.__init__(self, *args)
        self.update(kw)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, val):
        self[name] = val

    def copy(self):
        return obj(**self)


def parse_input(*args):
    if len(args) != len(sys.argv[1:]):
        raise ValueError
    return obj((name, type_(arg))
               for (name, type_), arg
                    in zip(args, sys.argv[1:]))

def memoized(fn):
    cache = {}
    def deco(*args):
        if args not in cache:
            cache[args] = fn(*args)
        return cache[args]
    return deco
