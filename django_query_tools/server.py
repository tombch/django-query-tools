from django.db.models import Q
import operator
import functools


class QueryAtom:
    """
    Class for representing the most basic component of a query; a single key-value pair.
    """

    def __init__(self, key, value):
        self.key = key
        self.value = value


def make_atoms(data, to_str=True):
    """
    Traverses the provided `data` and replaces request values with `QueryAtom` objects.
    Returns a list of these `QueryAtom` objects.
    """
    if len(data.items()) != 1:
        raise Exception

    key, value = next(iter(data.items()))

    if key in {"&", "|", "^"}:
        atoms = [make_atoms(k_v) for k_v in value]
        return functools.reduce(operator.add, atoms)

    elif key == "~":
        if len(value) != 1:
            raise Exception
        return make_atoms(value[0])

    else:
        # Initialise QueryAtom object
        if to_str:
            value = str(value)
        atom = QueryAtom(key, value)

        # Replace the data value with the QueryAtom object
        data[key] = atom

        # Now return the QueryAtom object
        # This is done so that it's easy to modify the QueryAtom objects
        # While also preserving the original structure of the query
        return [atom]


def make_query(data):
    """
    Traverses the provided `data` and forms the corresponding Q object.
    """
    if len(data.items()) != 1:
        raise Exception

    key, value = next(iter(data.items()))

    # AND of multiple keyvalues
    if key == "&":
        q_objects = [make_query(k_v) for k_v in value]
        return functools.reduce(operator.and_, q_objects)

    # OR of multiple keyvalues
    elif key == "|":
        q_objects = [make_query(k_v) for k_v in value]
        return functools.reduce(operator.or_, q_objects)

    # XOR of multiple keyvalues
    elif key == "^":
        q_objects = [make_query(k_v) for k_v in value]
        return functools.reduce(operator.xor, q_objects)

    # NOT of a single keyvalue
    elif key == "~":
        if len(value) != 1:
            raise Exception
        return ~make_query(value[0])

    # Base case: a QueryAtom to filter on
    else:
        # 'value' here is a QueryAtom object
        # That by this point, should have been cleaned and corrected to work in a query
        q = Q(**{value.key: value.value})
        return q
