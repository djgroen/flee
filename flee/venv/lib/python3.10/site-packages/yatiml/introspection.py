import inspect
from typing import Any, Dict, Generator, Tuple
from typing_extensions import Type


def class_subobjects(
        class_: Type) -> Generator[Tuple[str, Type, bool], None, None]:
    """Find the aggregated subobjects of an object.

    These are the public attributes.

    Args:
        class_: The class whose subobjects to return.

    Yields:
        Tuples (name, type, required) describing subobjects.
    """
    argspec = inspect.getfullargspec(class_.__init__)
    defaults = argspec.defaults if argspec.defaults else []
    num_optional = len(defaults)
    first_optional = len(argspec.args) - num_optional

    for i, attr_name in enumerate(argspec.args):
        if attr_name == 'self':
            continue
        if attr_name == '_yatiml_extra':
            continue
        attr_type = argspec.annotations.get(attr_name, Any)
        yield attr_name, attr_type, i < first_optional


def defaulted_attributes(class_: Type) -> Dict[str, Any]:
    """Returns attributes with defaulted values.

    Args:
        class_: The class to inspect.

    Returns:
        A dictionary containing attribute names and their default
        values.
    """
    argspec = inspect.getfullargspec(class_.__init__)
    defaults = argspec.defaults if argspec.defaults else []
    num_optional = len(defaults)
    first_optional = len(argspec.args) - num_optional

    if hasattr(class_, '_yatiml_defaults'):
        user_defaults = class_._yatiml_defaults     # type: Dict[str, Any]
    else:
        user_defaults = {}

    result = dict()     # type: Dict[str, Any]
    for i, default in enumerate(defaults):
        arg_name = argspec.args[first_optional + i]
        if arg_name in user_defaults:
            default = user_defaults[arg_name]
        result[arg_name] = default
    return result
