""" DictableObject.py
    Base class from which all database-row classes inherit.
"""


class DictableObject():

    def asDict(self):
        """Represent the instance as a dictionary field -> value."""
        return {k: getattr(self, k) for k in self.namedFields}

    def consumeKWargs(self, **kwargs):
        """ Eat up and set all kwargs appearing in the namedFields,
            returning the remaining ones for specialised handling
            by the subclass.
        """
        _kwargs = {k: v for k, v in kwargs.items()}
        delFields = []
        for k, v in _kwargs.items():
            if k in self.namedFields:
                setattr(self, k, v)
                delFields.append(k)
        for df in delFields:
            del _kwargs[df]
        return _kwargs
