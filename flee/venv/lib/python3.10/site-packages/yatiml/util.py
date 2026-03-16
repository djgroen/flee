from abc import ABC
from collections import abc, UserString
from difflib import get_close_matches
from datetime import date
from inspect import isabstract, isclass
import typing
from typing import (
        Any, cast, Dict, Iterable, Mapping, MutableMapping, MutableSequence,
        List, Sequence, Tuple, Union)
from typing_extensions import Type

import yaml
from yaml.resolver import Resolver

from yatiml.introspection import class_subobjects


class bool_union_fix:
    pass


scalar_type_to_tag = {
    str: 'tag:yaml.org,2002:str',
    int: 'tag:yaml.org,2002:int',
    float: 'tag:yaml.org,2002:float',
    bool: 'tag:yaml.org,2002:bool',
    bool_union_fix: 'tag:yaml.org,2002:bool',
    None: 'tag:yaml.org,2002:null',
    type(None): 'tag:yaml.org,2002:null',
    date: 'tag:yaml.org,2002:timestamp'
    }


ScalarType = Union[str, int, float, bool, None]


class String:
    """Tag for classes that should be serialised to YAML as a string.

    If your class has this class as a base class, then YAtiML will:

    - expect a string on the YAML side when recognising,
    - call ``__init__`` with that string as the sole argument when loading,
    - use ``str(obj)`` to obtain the string representation on dumping.

    You can still override what's written to the YAML file by defining
    ``_yatiml_sweeten()`` in the usual way.

    Like classes derived from ``str`` and ``UserString``, classes tagged like
    this can be used as keys for dictionaries. Be sure to implement
    ``__hash__()`` and ``__eq__()`` to make that work on the Python side.
    """
    pass


def is_abstract(type_: Type) -> bool:
    """Determines whether a type is an abstract base class.

    This is the case if it derives directly from abc.ABC, and/or if
    it has @abstractmethods.

    Args:
        type_: The type to check.

    Returns:
        True iff it's an abstract base class.
    """
    if not isclass(type_):
        return False
    if isabstract(type_):
        return True
    return ABC in type_.__bases__


def is_generic_sequence(type_: Type) -> bool:
    """Determines whether a type is a sequence tag.

    How to do this varies for different Python versions, due to the
    typing library not having a stable API. This functions smooths
    over the differences, returning True if the type is a List[],
    Sequence[] or MutableSequence[].

    Args:
        type_: The type to check.

    Returns:
        True iff it's a generic sequence.
    """
    if hasattr(typing, '_GenericAlias'):
        # 3.7
        # _GenericAlias cannot be imported from typing, because it doesn't
        # exist in all versions, and it will fail the type check in those
        # versions as well, so we ignore it.
        return (isinstance(type_, typing._GenericAlias) and     # type: ignore
                (
                    type_.__origin__ is list or
                    type_.__origin__ is abc.Sequence or
                    type_.__origin__ is abc.MutableSequence))
    else:
        # 3.6 and earlier
        # GenericMeta cannot be imported from typing, because it doesn't
        # exist in all versions, and it will fail the type check in those
        # versions as well, so we ignore it.
        return (isinstance(type_, cast(Any, typing).GenericMeta) and
                (
                    cast(Any, type_).__origin__ is List or
                    cast(Any, type_).__origin__ is Sequence or
                    cast(Any, type_).__origin__ is MutableSequence))


def is_generic_mapping(type_: Type) -> bool:
    """Determines whether a type is a mapping tag.

    How to do this varies for different Python versions, due to the
    typing library not having a stable API. This functions smoothes
    over the differences, returning True if the type is a Dict[],
    Mapping[] or MutableMapping[].

    Args:
        type_: The type to check.

    Returns:
        True iff it's a generic mapping.
    """
    if hasattr(typing, '_GenericAlias'):
        # 3.7
        return (isinstance(type_, typing._GenericAlias) and     # type: ignore
                (
                    type_.__origin__ is dict or
                    type_.__origin__ is abc.Mapping or
                    type_.__origin__ is abc.MutableMapping))
    else:
        # 3.6 and earlier
        return (isinstance(type_, cast(Any, typing).GenericMeta) and
                (
                    cast(Any, type_).__origin__ is Dict or
                    cast(Any, type_).__origin__ is Mapping or
                    cast(Any, type_).__origin__ is MutableMapping))


def is_generic_union(type_: Type) -> bool:
    """Determines whether a type is a Union[...].

    How to do this varies for different Python versions, due to the
    typing library not having a stable API. This functions smooths
    over the differences.

    Args:
        type_: The type to check.

    Returns:
        True iff it's a Union[...something...].
    """
    if hasattr(typing, '_GenericAlias'):
        # 3.7
        return (isinstance(type_, typing._GenericAlias) and     # type: ignore
                type_.__origin__ is Union)
    else:
        if hasattr(typing, '_Union'):
            # 3.6
            return isinstance(type_, typing._Union)             # type: ignore
        else:
            # 3.5 and earlier (?)
            return isinstance(type_, typing.UnionMeta)          # type: ignore
    raise RuntimeError('Could not determine whether type is a Union. Is this'
                       ' a YAtiML-supported Python version?')


def generic_type_args(type_: Type) -> List[Type]:
    """Gets the type argument list for the given generic type.

    If you give this function List[int], it will return [int], and
    if you give it Union[int, str] it will give you [int, str]. Note
    that on Python < 3.7, Union[int, bool] collapses to Union[int] and
    then to int; this is already done by the time this function is
    called, so it does not help with that.

    Args:
        type_: The type to get the arguments list of.

    Returns:
        A list of Type objects.
    """
    if hasattr(type_, '__union_params__'):
        # 3.5 Union
        return list(type_.__union_params__)
    if hasattr(type_, '__args__'):
        # >3.5
        return list(type_.__args__)
    # 3.5
    return list(type_.__parameters__)


def type_to_desc(type_: Type) -> str:
    """Convert a type to a human-readable description.

    This is used for generating nice error messages. We want users
    to see a nice readable text, rather than something like
    "typing.List<~T>[str]".

    Args:
        type_: The type to represent.

    Returns:
        A human-readable description.
    """
    scalar_type_to_str = {
        str: 'a string',
        int: 'an int',
        float: 'a float',
        bool: 'a boolean',
        None: 'a null value',
        type(None): 'a null value'
    }

    if type_ in scalar_type_to_str:
        return scalar_type_to_str[type_]

    if is_generic_union(type_):
        return 'any one of {}'.format(
                [type_to_desc(t) for t in generic_type_args(type_)])

    if is_generic_sequence(type_):
        return 'a list of ({})'.format(
                type_to_desc(generic_type_args(type_)[0]))

    if is_generic_mapping(type_):
        return 'a dict of string to ({})'.format(
                type_to_desc(generic_type_args(type_)[1]))

    if type_ is Any:
        return 'a string, int, float, boolean, null value, list or dict'

    return 'a(n) {}'.format(type_.__name__)


def is_string_like(type_: Type) -> bool:
    """Returns whether the type is string-like.

    That means it takes a string as its only constructor argument, and
    is allowed to be a key in dicts. See UserStringConstructor.

    Args:
        type_: The type to check.
    """
    return issubclass(type_, (str, UserString, String))


def strip_tags(resolver: Resolver, node: yaml.Node) -> None:
    """Strips tags from mappings in the tree headed by node.

    This keeps yaml from constructing any objects in this tree.

    Args:
        resolver: Resolver to tag scalar nodes with
        node: Head of the tree to strip
    """
    if isinstance(node, yaml.ScalarNode):
        if not node.tag.startswith('tag:yaml.org,2002:'):
            node.tag = resolver.resolve(
                    yaml.ScalarNode, node.value, (True, False))
    elif isinstance(node, yaml.SequenceNode):
        node.tag = 'tag:yaml.org,2002:seq'
        for subnode in node.value:
            strip_tags(resolver, subnode)
    elif isinstance(node, yaml.MappingNode):
        node.tag = 'tag:yaml.org,2002:map'
        for key_node, value_node in node.value:
            strip_tags(resolver, key_node)
            strip_tags(resolver, value_node)


def cjoin(conjuction: str, words: Iterable[str]) -> str:
    """Joins words together into a conjuctive clause.

    This makes a nice enumeration out of the list of words. For
    example, mjoin('and', ['x', 'y', 'z']) produces the string
    'x, y and z'.
    """
    result = ''
    words_list = list(words)
    last_idx = len(words_list) - 1
    for i, w in enumerate(words_list):
        if i > 0:
            if i < last_idx:
                result += ', '
            else:
                result += ' ' + conjuction + ' '
        result += w
    return result


def _describe_allowed_present_keys(
        got: List[str], all_keys: List[Tuple[str, Type, bool]],
        missing: bool) -> str:
    """Describe allowed keys and what we got.

    Args:
        got: List of keys that were given by the user
        expected_type: A user-defined class
        missing: Whether a key was missing or extraneous
    """
    extraneous = not missing

    req_keys = ['"{}"'.format(name) for name, _, req in all_keys if req]
    opt_keys = ['"{}"'.format(name) for name, _, req in all_keys if not req]

    class_desc = list()

    req_msg = 'For reference, '
    req_msg += 'keys' if len(req_keys) > 1 else 'key'
    req_msg += ' ' + cjoin('and', req_keys)
    req_msg += ' are' if len(req_keys) > 1 else ' is'
    req_msg += ' required here'
    class_desc.append(req_msg)

    if opt_keys:
        opt_msg = '{}'.format(cjoin('and', opt_keys))
        opt_msg += ' are' if len(opt_keys) > 1 else ' is'
        opt_msg += ' optional'
        class_desc.append(opt_msg)

    if extraneous:
        # if we had _yatiml_extra then we wouldn't be here
        class_desc.append('no other keys are allowed')

    sug_msg = cjoin('and', class_desc)

    g = ['"{}"'.format(g) for g in got]
    sug_msg += ', but'
    if missing:
        if set(got).issubset({n for n, _, _ in all_keys}):
            sug_msg += ' only'
    sug_msg += ' {}'.format(cjoin('and', g))
    sug_msg += ' were given.' if len(got) > 1 else ' was given.'
    return sug_msg


def diagnose_missing_key(
        name: str, got: List[str], expected_type: Type) -> str:
    """Helper that gives a good error when a key is missing.

    Args:
        name: Name of the missing required attribute
        got: List of keys that were given by the user
        expected_type: A user-defined class we expected to get
    """
    a = '"{}"'.format(name)
    if '_' in name:
        a += ' or maybe "{}"'.format(
                name.replace('_', '-'))
    expected_msg = 'Expected a key {} but it was not found.'.format(a)

    expected_keys = [name for name, _, _ in class_subobjects(expected_type)]

    similar = get_close_matches(name, got)
    similar = [s for s in similar if s not in expected_keys]

    if similar:
        suggestions = cjoin('or', ['"{}"'.format(s) for s in similar])
        sug_msg = 'Maybe {} was intended to be {}? '.format(suggestions, a)
    else:
        all_keys = list(class_subobjects(expected_type))
        if len(all_keys) < 8:
            sug_msg = expected_msg
            sug_msg += ' Maybe it was indented incorrectly?'
            sug_msg += ' ' + _describe_allowed_present_keys(
                    got, all_keys, True)
            return sug_msg
        else:
            sug_msg = 'Maybe it was forgotten or indented incorrectly?'

    return ' '.join((expected_msg, sug_msg))


def diagnose_extraneous_key(
        name: str, got: List[str], expected_type: Type) -> str:
    """Helper that gives a good error when an extra key is present.

    Args:
        name: Name of the extraneous required attribute
        got: List of keys that were given by the user
        expected_type: A user-defined class we expected to get
    """
    expected_msg = 'Found a key "{}", which is not allowed here.'.format(name)

    opt_keys = [
            name for name, _, req in class_subobjects(expected_type)
            if not req]
    similar = get_close_matches(name, opt_keys)
    similar = [s for s in similar if s not in got]

    if similar:
        suggestions = cjoin('or', ['"{}"'.format(s) for s in similar])
        sug_msg = 'Maybe "{}" was intended to be {}? '.format(
                name, suggestions)
    else:
        all_keys = list(class_subobjects(expected_type))
        if len(all_keys) < 8:
            sug_msg = expected_msg
            sug_msg += ' Maybe it was indented incorrectly? '
            sug_msg += _describe_allowed_present_keys(got, all_keys, False)
            return sug_msg
        else:
            sug_msg = (
                    'No similar allowed keys were found either. Maybe it was'
                    ' indented incorrectly?')
    return ' '.join((expected_msg, sug_msg))
