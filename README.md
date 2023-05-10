# `django-query-tools`
Tools for building queries in Django.
## Setup
```
$ git clone https://github.com/tombch/django-query-tools.git
$ cd django-query-tools/
$ pip install .
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
print("Django Q object:", make_query(data))
```

```
$ python script.py
F object for x: <django_query_tools.client.F object at 0x100fc4bd0>
Data: {'x': 'hello'}
F object for y: <django_query_tools.client.F object at 0x100fc4c50>
Data: {'y': 'goodbye'}
Query F object: <django_query_tools.client.F object at 0x100fc6190>
Client sends data: {'&': [{'x': 'hello'}, {'~': [{'y': 'goodbye'}]}]}
Server receives data: {'&': [{'x': 'hello'}, {'~': [{'y': 'goodbye'}]}]}
QueryAtom structure: {'&': [{'x': <django_query_tools.server.QueryAtom object at 0x100fc5a50>}, {'~': [{'y': <django_query_tools.server.QueryAtom object at 0x100fc6210>}]}]}
QueryAtom objects: [<django_query_tools.server.QueryAtom object at 0x100fc5a50>, <django_query_tools.server.QueryAtom object at 0x100fc6210>]
Django Q object: (AND: ('x', 'hello'), (NOT (AND: ('y', 'goodbye'))))
```