# `django-query-tools`
Tools for building queries in Django.

![PyPI](https://img.shields.io/pypi/v/django-query-tools?label=pypi%20package)
![PyPI - Downloads](https://img.shields.io/pypi/dm/django-query-tools)

## Setup
```
$ pip install django-query-tools
```
To use the `server` module, Django must also be installed:
```
$ pip install django
```

## Usage
```python
# script.py

from django_query_tools.client import F
from django_query_tools.server import make_atoms, make_query
from django.db.models import Q

# --- CLIENT ---

# Define x and y fields
x = F(x="hello")
print("F object for x:", x)
print("Data:", x.query)

y = F(y="goodbye")
print("F object for y:", y)
print("Data:", y.query)

# Form a query from x and y
query = x & ~y
print("Query F object:", query)
print("Client sends data:", query.query)

# --- SERVER ---

# Server receives query
data = query.query
print("Server receives data:", data)

# Modifies data in-place, creating QueryAtom keyvalue pairs
# Returns these QueryAtom objects for validation
atoms = make_atoms(data)
print("QueryAtom structure:", data)
print("QueryAtom objects:", atoms)

# Builds Django Q object from the QueryAtom objects
formed = make_query(data)
expected = Q(x="hello") & ~Q(y="goodbye")
print("Formed Q object:", formed)
print("Expected Q object:", expected)
print("These objects represent the same query:", formed == expected)
```

```
$ python script.py
F object for x: <django_query_tools.client.F object at 0x1012f1910>
Data: {'x': 'hello'}
F object for y: <django_query_tools.client.F object at 0x1012f1990>
Data: {'y': 'goodbye'}
Query F object: <django_query_tools.client.F object at 0x1012f3510>
Client sends data: {'&': [{'x': 'hello'}, {'~': {'y': 'goodbye'}}]}
Server receives data: {'&': [{'x': 'hello'}, {'~': {'y': 'goodbye'}}]}
QueryAtom structure: {'&': [{'x': <django_query_tools.server.QueryAtom object at 0x1012f1a10>}, {'~': {'y': <django_query_tools.server.QueryAtom object at 0x1023b1890>}}]}
QueryAtom objects: [<django_query_tools.server.QueryAtom object at 0x1012f1a10>, <django_query_tools.server.QueryAtom object at 0x1023b1890>]
Formed Q object: (AND: ('x', 'hello'), (NOT (AND: ('y', 'goodbye'))))
Expected Q object: (AND: ('x', 'hello'), (NOT (AND: ('y', 'goodbye'))))
These objects represent the same query: True
```