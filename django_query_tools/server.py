import operator
import functools
from typing import Dict, List, Any
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models import Q


class QueryException(Exception):
    """
    Class for all query-parsing exceptions.
    """

    pass


class QueryAtom:
    """
    Class for representing the most basic component of a query; a single key-value pair.
    """

    def __init__(self, key, value):
        self.key = key
        self.value = value


def validate_data(func):
    def wrapped(data, *args, **kwargs):
        if not isinstance(data, dict):
            raise QueryException(
                f"Expected dictionary when parsing query but received type: {type(data)}"
            )

        if len(data.items()) != 1:
            raise QueryException(
                "Dictionary within query is not a single key-value pair"
            )

        return func(data, *args, **kwargs)

    return wrapped


@validate_data
def make_atoms(data: Dict[str, Any], to_str: bool = True) -> List[QueryAtom]:
    """
    Traverses the provided `data` and replaces request values with `QueryAtom` objects.
    Returns a list of these `QueryAtom` objects.
    """

    key, value = next(iter(data.items()))
    operators = {"&", "|", "^"}

    if key in operators:
        atoms = [make_atoms(k_v) for k_v in value]
        return functools.reduce(operator.add, atoms)

    elif key == "~":
        return make_atoms(value)

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


@validate_data
def make_query(data: Dict[str, Any]) -> Q:
    """
    Traverses the provided `data` and forms the corresponding Q object.
    """

    key, value = next(iter(data.items()))
    operators = {"&": operator.and_, "|": operator.or_, "^": operator.xor}

    if key in operators:
        q_objects = [make_query(k_v) for k_v in value]
        return functools.reduce(operators[key], q_objects)

    elif key == "~":
        return ~make_query(value)

    else:
        # Base case: a QueryAtom to filter on
        # 'value' here is a QueryAtom object
        # That by this point, should have been cleaned and corrected to work in a query
        q = Q(**{value.key: value.value})
        return q


def validate_atoms(
    atoms: List[QueryAtom],
    filterset,
    filterset_args=None,
    filterset_kwargs=None,
    filterset_model=None,
) -> None:
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
