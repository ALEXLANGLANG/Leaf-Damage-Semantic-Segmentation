import yaml
from types import SimpleNamespace
from functools import singledispatch

# The singledispatch mechanism allows adding methods reotractively
# to the namespace and dict classes.
# The decorator @singledispatch makes the function under it a generic
# single-dispatch function: It is generic in that it applies to multiple
# types. It is single-dispatch in that the implementation depends on the
# type of a single argument (the first).
# Different implementations for different argument types are associated
# to the appropriate class by a .register decorator.


@singledispatch
def dict_to_namespace(item):
    return item


@dict_to_namespace.register(dict)
def _(item):
    return SimpleNamespace(**{key: dict_to_namespace(value) for key, value in item.items()})


@dict_to_namespace.register(list)
def _(item):
    return [dict_to_namespace(v) for v in item]


@singledispatch
def namespace_to_dict(item):
    return item


@namespace_to_dict.register(SimpleNamespace)
def _(item):
    return {key: namespace_to_dict(value) for key, value in vars(item).items()}


@namespace_to_dict.register(list)
def _(item):
    return [namespace_to_dict(v) for v in item]


def read_from_yaml(filename, to_namespace=True):
    with open(filename, 'r') as file:
        data = yaml.load(file, Loader=yaml.FullLoader)
    if to_namespace:
        return dict_to_namespace(data)
    else:
        return data


def write_to_yaml(data, filename, default_flow_style=False):
    if isinstance(data, SimpleNamespace):
        data = namespace_to_dict(data)
    else:
        assert isinstance(data, dict), 'Data is neither a simple namespace nor a dictionary'
    with open(filename, 'w') as file:
        yaml.dump(data, file, sort_keys=False, default_flow_style=default_flow_style)
