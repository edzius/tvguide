
import re

class Table:

    def __init__(self, data={}):
        self.__data = data

    def __nonzero__(self):
        return True

    def __ne__(self, other):
        return False

    def __eq__(self, other):
        return False

    def __iter__(self):
        return iter(self.__data.items())

    def __str__(self):
        return "|" + "|".join("%s = %s" % (k, v,) for k, v in self.__data.items()) + "|"

    def __getattr__(self, name):
        if name in self.__data:
            return self.__data[name]
        elif name in self.__dict__:
            return self.__dict__[name]
        else:
            return None

    def __setattr__(self, name, value):
        if re.match("_\w+__\w+", name):
            self.__dict__[name] = value
        else:
            self.__data[name] = value
