from django.core.exceptions import FieldDoesNotExist, ValidationError
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

    key, value = next(iter(data.items()))  #  type: ignore

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


def validate_atoms(
    atoms, filterset, filterset_args=None, filterset_kwargs=None, filterset_model=None
):
    """
    Use the provided `filterset` to validate and clean the provided list of `atoms`.
    """
    # Construct a list of dictionaries from the atoms
    # Each of these dictionaries will be passed to a filterset
    # The filterset is being used to clean and validate the input filters
    # Until we construct the query, it doesn't matter how fields are related in the query (i.e. AND, OR, etc)
    # All that matters is if the individual filters and their values are valid
    layers = [{}]

    for atom in atoms:
        # Place the QueryAtom in the first dictionary where the key is not present
        # If we reach the end with no placement, create a new dictionary and add it in there
        for layer in layers:
            if atom.key not in layer:
                layer[atom.key] = atom
                break
        else:
            layers.append({atom.key: atom})

    if not filterset_args:
        filterset_args = ()

    if not filterset_kwargs:
        filterset_kwargs = {}

    if not filterset_model:
        filterset_model = filterset.Meta.model

    # Use a filterset, applied to each dict in layers, to validate the data
    for i, layer in enumerate(layers):
        # Slightly cursed, but it works
        fs = filterset(
            *filterset_args,
            data={k: v.value for k, v in layer.items()},
            queryset=filterset_model.objects.none(),
            **filterset_kwargs,
        )

        # If unknown field lookups were provided, raise an exception
        if i == 0:
            unknown = []

            for field in layer:
                if field not in fs.filters:
                    unknown.append(field)

            if unknown:
                raise FieldDoesNotExist(unknown)

        # If not valid, return errors
        if not fs.is_valid():
            raise ValidationError(fs.errors)

        # Add the cleaned values to the QueryAtom objects
        for k, atom in layer.items():
            atom.value = fs.form.cleaned_data[k]


def make_query(data):
    """
    Traverses the provided `data` and forms the corresponding Q object.
    """
    if len(data.items()) != 1:
        raise Exception

    key, value = next(iter(data.items()))  #  type: ignore

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
