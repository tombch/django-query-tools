def combine_on_associative(operation, field1, field2):
    """
    Combine two pre-existing queries on an ASSOCIATIVE operation (`&`, `|`, `^`), and use this to reduce nested JSON.

    E.g. take the following query:

    `((X & Y) & Z) | (W & (X & (Y | (Z | X))))`

    We can use associativity of `&` and `|` to reduce how deeply nested the JSON request body is.

    By associativity of `&` and `|`, the following is unambiguous and logically equivalent to the previous query:

    `(X & Y & Z) | (W & X & (Y | Z | X))`

    With the former corresponding to more deeply-nested JSON than the latter.

    Believe it or not this is somewhat useful!! There is normally a limit on how deeply nested a JSON request body can be.

    So by preventing unnecessary nesting, users can programatically construct and execute a broader range of queries.
    """
    field1_key, field1_value = next(iter(field1.query.items()))
    field2_key, field2_value = next(iter(field2.query.items()))

    # For each field
    # If the topmost key is equal to the current operation, we pull up the values
    # Otherwise, they stay self-contained within their existing operation
    if field1_key == operation:
        field1_query = field1_value
    else:
        field1_query = [field1.query]

    if field2_key == operation:
        field2_query = field2_value
    else:
        field2_query = [field2.query]

    return F(**{operation: field1_query + field2_query})


class F:
    def __init__(self, **kwargs):
        if len(kwargs) != 1:
            raise Exception(
                "Must provide exactly one field-value pair as keyword arguments"
            )

        # Get the field-value pair from the kwargs
        field, value = next(iter(kwargs.items()))

        # If the field is not an operation
        # And it is a multi-value lookup
        # Join the values into a comma-separated string
        if field not in ["&", "|", "^", "~"]:
            if type(value) in [list, tuple, set]:
                value = ",".join(map(str, value))

        self.query = {field: value}

    def __and__(self, field):
        validate_field(field)
        return combine_on_associative("&", self, field)

    def __or__(self, field):
        validate_field(field)
        return combine_on_associative("|", self, field)

    def __xor__(self, field):
        validate_field(field)
        return combine_on_associative("^", self, field)

    def __invert__(self):
        # Here we account for double negatives to also reduce nesting
        # Not really needed as people are (unlikely) to be putting multiple '~' one after the other
        # But hey you never know

        # Get the top-most key of the current query
        # If its also a NOT, we pull out the value and initialise that as the query
        self_key, self_value = next(iter(self.query.items()))
        if self_key == "~":
            return F(**self_value)  #  type: ignore
        else:
            return F(**{"~": self.query})


def validate_field(field: F):
    """
    Ensure the correct type has been provided.
    """
    if not isinstance(field, F):
        raise Exception("Can only combine F object with other F objects")
