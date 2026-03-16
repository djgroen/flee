from collections import OrderedDict
import enum
import json
import logging
from pathlib import Path, PosixPath, WindowsPath
from typing import Any, AnyStr, Callable, IO, List, Optional, Union, cast
from typing_extensions import Protocol, Type

import yaml
from yaml.events import (
        AliasEvent, DocumentEndEvent, MappingEndEvent, MappingStartEvent,
        ScalarEvent, SequenceEndEvent, SequenceStartEvent)

from yatiml.representers import (EnumRepresenter, Representer,
                                 PathRepresenter, UserStringRepresenter)
from yatiml.util import is_string_like


logger = logging.getLogger(__name__)


class JsonDumperState(enum.Enum):
    NONE = 0,
    SEQUENCE = 1,
    SEQUENCE_FIRST = 2,
    MAPPING_KEY = 3,
    MAPPING_KEY_FIRST = 4,
    MAPPING_VALUE = 5


class Dumper(yaml.SafeDumper):
    """The YAtiML Dumper class.

    Derive your own Dumper class from this one, then add classes to it
    using :meth:`add_to_dumper`. Set ``output_format = "json"`` to
    output JSON.

    .. warning::

        This class is **deprecated**, and will be removed in a future
        version. You should use :meth:`dump_function` or
        :meth:`dumps_function` instead.
    """
    output_format = 'yaml'

    def __init__(
            self, stream: Any, default_style: Any,
            default_flow_style: Optional[bool], canonical: Optional[bool],
            indent: Optional[int], width: Optional[int],
            allow_unicode: Optional[bool], line_break: Any, encoding: Any,
            explicit_start: Optional[bool], explicit_end: Optional[bool],
            version: Any, tags: Any, sort_keys: bool
            ) -> None:
        """Create a Dumper, called by PyYAML"""
        yaml.SafeDumper.__init__(
                self, stream, default_style, default_flow_style, canonical,
                indent, width, allow_unicode, line_break, encoding,
                explicit_start, explicit_end, version, tags, False)

        self._json_state = [JsonDumperState.NONE]
        self._cur_indent = 0
        self._requested_indent = indent

        if indent is not None:
            self._kv_sep = ': '
        else:
            self._kv_sep = ':'

    def emit(self, event: yaml.events.Event) -> None:
        """Emit an event.

        This is called by PyYAML, and we dispatch to the original
        implementation (which emits YAML) or our emit_json() below if
        the user selected JSON output.

        Args:
            event: The event to output.
        """
        if self.output_format == 'json':
            self.emit_json(event)
        else:
            yaml.SafeDumper.emit(self, event)

    def emit_json(self, event: yaml.events.Event) -> None:
        """Emit a YAML event to the JSON output.

        Args:
            event: The event to output.
        """
        if isinstance(event, AliasEvent):
            raise RuntimeError('Aliases are not supported by JSON')
        elif isinstance(event, SequenceEndEvent):
            self._cur_indent -= self.best_indent
            self._do_endline()
            self.stream.write(']')
            self._json_state.pop()
        elif isinstance(event, MappingEndEvent):
            self._cur_indent -= self.best_indent
            self._do_endline()
            self.stream.write('}')
            self._json_state.pop()
        elif isinstance(event, DocumentEndEvent):
            self._do_endline()
        else:
            # top-level scalar, or continuing a sequence or mapping
            cur_level = len(self._json_state) - 1
            cur_state = self._json_state[cur_level]

            # write separator if necessary
            if cur_state == JsonDumperState.SEQUENCE:
                self.stream.write(',')
                self._do_endline()
            elif cur_state == JsonDumperState.MAPPING_KEY:
                self.stream.write(',')
                self._do_endline()
            elif cur_state == JsonDumperState.MAPPING_VALUE:
                self.stream.write(self._kv_sep)

            # output value
            if isinstance(event, SequenceStartEvent):
                self.stream.write('[')
                self._cur_indent += self.best_indent
                self._do_endline()
                self._json_state.append(JsonDumperState.SEQUENCE_FIRST)
            elif isinstance(event, MappingStartEvent):
                self.stream.write('{')
                self._cur_indent += self.best_indent
                self._do_endline()
                self._json_state.append(JsonDumperState.MAPPING_KEY_FIRST)
            elif isinstance(event, ScalarEvent):
                if event.tag == 'tag:yaml.org,2002:str':
                    self.stream.write(json.dumps(
                        event.value, ensure_ascii=not self.allow_unicode))
                elif event.tag == 'tag:yaml.org,2002:null':
                    self.stream.write('null')
                elif event.tag == 'tag:yaml.org,2002:bool':
                    self.stream.write(event.value.lower())
                elif event.tag == 'tag:yaml.org,2002:timestamp':
                    self.stream.write(json.dumps(
                        event.value, ensure_ascii=not self.allow_unicode))
                else:
                    self.stream.write(event.value)

            # set next state
            if cur_state == JsonDumperState.SEQUENCE_FIRST:
                self._json_state[cur_level] = JsonDumperState.SEQUENCE
            elif cur_state == JsonDumperState.MAPPING_KEY_FIRST:
                self._json_state[cur_level] = JsonDumperState.MAPPING_VALUE
            elif cur_state == JsonDumperState.MAPPING_KEY:
                self._json_state[cur_level] = JsonDumperState.MAPPING_VALUE
            elif cur_state == JsonDumperState.MAPPING_VALUE:
                self._json_state[cur_level] = JsonDumperState.MAPPING_KEY

    def represent_ordereddict(self, data: Any) -> Any:
        # Override PyYAML to produce a plain dict.
        return self.represent_dict(data)

    def _do_endline(self) -> None:
        """Write EOL and subsequent indent if enabled."""
        if self._requested_indent is not None:
            self.stream.write(self.best_line_break)
            self.stream.write(' ' * self._cur_indent)


Dumper.add_representer(OrderedDict, Dumper.represent_ordereddict)
Dumper.add_representer(PosixPath, PathRepresenter())
Dumper.add_representer(WindowsPath, PathRepresenter())


# Python errors if we define classes as Union[List[Type], Type]
# So List[Type] it is, and if the user ignores that and passes
# a single class, it'll work anyway, with a little mypy override.
def add_to_dumper(dumper: Type, classes: List[Type]) -> None:
    """Register user-defined classes with the Dumper.

    This enables the Dumper to write objects of your classes to a
    YAML file. Note that all the arguments are types, not instances!

    Args:
        dumper: Your dumper class(!), derived from yatiml.Dumper
        classes: One or more classes to add.

    .. warning::

        This function is **deprecated**, and will be removed in a
        future version. You should use :meth:`dump_function` or
        :meth:`dumps_function` instead.
    """
    if not isinstance(classes, list):
        classes = [classes]  # type: ignore
    for class_ in classes:
        if issubclass(class_, enum.Enum):
            dumper.add_representer(class_, EnumRepresenter(class_))
        elif is_string_like(class_):
            dumper.add_representer(class_, UserStringRepresenter(class_))
        else:
            dumper.add_representer(class_, Representer(class_))


def dumps_function(*args: Type) -> Callable[[Any], str]:
    """Create a dumps function for the given types.

    This function returns a callable object which takes an object
    and returns a string containing the YAML serialisation of that
    object. The type of the object, and any other custom types
    needed, must have been passed to :meth:`dumps_function`.

    Note that only custom classes need to be passed, the built-in
    types are, well, built in.

    Examples:

        .. code-block:: python

          dumps = yatiml.dumps_function()
          yaml_text = dumps({'x': 1})
          assert yaml_text == 'x: 1\\n'

        .. code-block:: python

          dumps_config = yatiml.dumps_function(Config, Setting)
          yaml_text = dumps_config(my_config)

        Here, ``Config`` is the top-level class, and ``Setting`` is
        another class that is used by ``Config`` somewhere. Note that
        any object can be passed to the resulting dumps function, as
        long as it is of a built-in type or its type and any types
        needed to represent it have been passed to
        :meth:`dumps_function`.

    Args:
        *args: Any custom types needed.

    Returns:
        A function that takes an object and produces a YAML string
        representing it.
    """
    class UserDumper(Dumper):
        pass

    add_to_dumper(UserDumper, list(args))

    class DumpsFunction:
        """Dumps objects to a YAML string."""
        def __init__(self, dumper: Type[Dumper]) -> None:
            """Create a dumps function."""
            self.dumper = dumper

        def __call__(self, obj: Any) -> str:
            """Dump the object to a YAML string.

            Args:
                obj: An object to dump.

            Returns:
                A string containing its YAML representation.
            """
            return cast(str, yaml.dump(obj, Dumper=self.dumper))

    return DumpsFunction(UserDumper)


def dump_function(
        *args: Type) -> Callable[[Any, Union[str, Path, IO[AnyStr]]], None]:
    """Create a dump function for the given types.

    This function returns a callable object which takes an object
    and a stream, Path or file name, and writes the YAML serialisation
    of that object to the target. The type of the object, and any other
    custom types needed, must have been passed to
    :meth:`dump_function`.

    Note that only custom classes should be passed, the built-in
    types are, well, built in.

    Examples:

        .. code-block:: python

          dump = yatiml.dump_function()
          with open('test.yaml', 'w') as f:
              dump({'x': 1}, f)
          # will write 'x: 1\\n' to test.yaml

        .. code-block:: python

          my_config = Config(...)
          dump_config = yatiml.dump_function(Config, Setting)
          dump_config(my_config, 'config.yaml')

        Here, ``Config`` is the top-level class, and ``Setting`` is
        another class that is used by ``Config`` somewhere. Note that
        any object can be passed to the resulting dump function, as long
        as it is of a built-in type or its type and any types needed
        to represent it have been passed to :meth:`dump_function`.

    Args:
        *args: Any custom types needed.

    Returns:
        A function that takes an object and a stream, file name or Path,
        and writes a YAML string representing the object to the file.
    """
    class UserDumper(Dumper):
        pass

    add_to_dumper(UserDumper, list(args))

    class DumpFunction:
        """Dumps objects to a stream."""
        def __init__(self, dumper: Type[Dumper]) -> None:
            """Create a dumps function."""
            self.dumper = dumper

        def __call__(
                self, obj: Any, sink: Union[str, Path, IO[AnyStr]]) -> None:
            """Dump the object to a file or stream.

            The sink argument may be a string containing a path, a
            pathlib.Path object containing a path, or a stream to write
            to directly (e.g. an open file).

            Args:
                obj: An object to dump.
                sink: A place to save it to.
            """
            if isinstance(sink, str):
                sink = Path(sink)

            if isinstance(sink, Path):
                with sink.open('w') as f:
                    yaml.dump(obj, f, Dumper=UserDumper)
            else:
                yaml.dump(obj, sink, Dumper=UserDumper)

    return DumpFunction(UserDumper)


class DumpsJsonFunctionType(Protocol):
    def __call__(
            self, obj: Any, *, indent: Optional[int] = None,
            ensure_ascii: bool = True) -> str:
        ...


def dumps_json_function(*args: Type) -> DumpsJsonFunctionType:
    """Create a dumps function for the given types that writes JSON.

    This function returns a callable object which takes an object
    and returns a string containing the JSON serialisation of that
    object. The type of the object, and any other custom types
    needed, must have been passed to :meth:`dumps_json_function`.

    By default, the produced JSON is in ASCII and in a compact format
    without newlines or spaces. To make it more readable, you can
    pass an ``indent`` keyword argument to the returned function, which
    causes the output to be formatted with the given indent.

    To output unicode characters as-is, pass ``ensure_ascii=False`` to
    the returned dumps function.

    Note that only custom classes need to be passed, the built-in
    types are, well, built in.

    Examples:

        .. code-block:: python

          dumps_json = yatiml.dumps_json_function()
          json_text = dumps_json({'x': 1})
          assert json_text == '{"x": 1}'

          json_text = dumps_json({'x': 1}, indent=2)
          assert json_text == (
              '{\\n'
              '  "x": 1\\n'
              '}\\n')


        .. code-block:: python

          dumps_config_to_json = yatiml.dumps_json_function(Config, Setting)
          json_text = dumps_config_to_json(my_config)

        Here, ``Config`` is the top-level class, and ``Setting`` is
        another class that is used by ``Config`` somewhere. Note that
        any object can be passed to the resulting dumps function, as
        long as it is of a built-in type or its type and any types
        needed to represent it have been passed to
        :meth:`dumps_json_function`.

    Args:
        *args: Any custom types needed.

    Returns:
        A function that takes an object and produces a YAML string
        representing it.
    """
    class UserDumper(Dumper):
        output_format = 'json'

    UserDumper.add_representer(PosixPath, PathRepresenter())
    UserDumper.add_representer(WindowsPath, PathRepresenter())

    add_to_dumper(UserDumper, list(args))

    class DumpsJsonFunction:
        """Dumps objects to a JSON string."""
        def __init__(self, dumper: Type[Dumper]) -> None:
            """Create a dumps function."""
            self.dumper = dumper

        def __call__(
                self, obj: Any, *,
                indent: Optional[int] = None, ensure_ascii: bool = True
                ) -> str:
            """Dump the object to a JSON string.

            Args:
                obj: An object to dump.

            Returns:
                A string containing its JSON representation.
            """
            return cast(str, yaml.dump(
                obj, Dumper=self.dumper,
                indent=indent, allow_unicode=not ensure_ascii))

    return DumpsJsonFunction(UserDumper)


class DumpJsonFunctionType(Protocol):
    def __call__(
            self, obj: Any, sink: Union[str, Path, IO[AnyStr]],
            indent: Optional[int] = None, ensure_ascii: bool = True) -> None:
        ...


def dump_json_function(
        *args: Type) -> DumpJsonFunctionType:
    """Create a dump function for the given types that writes JSON.

    This function returns a callable object which takes an object
    and a stream, Path or file name, and writes the JSON serialisation
    of that object to the target. The type of the object, and any other
    custom types needed, must have been passed to
    :meth:`dump_json_function`.

    By default, the produced JSON is in ASCII and in a compact format
    without newlines or spaces. To make it more readable, you can
    pass an ``indent`` keyword argument to the returned function, which
    causes the output to be formatted with the given indent.

    To output unicode characters as-is, pass ``ensure_ascii=False`` to
    the returned dumps function.

    Note that only custom classes need to be passed, the built-in
    types are, well, built in.

    Examples:

        .. code-block:: python

          dump_json = yatiml.dump_json_function()
          with open('test.json', 'w') as f:
              dump_json({'x': 1}, f)
          # will write '{"x": 1}' to test.json

          dump_json({'x': 1}, 'test.json', indent=2)
          # will write the same, but nicely formatted

        .. code-block:: python

          my_config = Config(...)
          dump_config_as_json = yatiml.dump_function(Config, Setting)
          dump_config_as_json(my_config, 'config.json', indent=2)

        Here, ``Config`` is the top-level class, and ``Setting`` is
        another class that is used by ``Config`` somewhere. Note that
        any object can be passed to the resulting dump function, as
        long as it is of a built-in type or its type and any types
        needed to represent it have been passed to
        :meth:`dump_json_function`.

    Args:
        *args: Any custom types needed.

    Returns:
        A function that takes an object and a stream, file name or Path,
        and writes a JSON string representing the object to the file.
    """
    class UserDumper(Dumper):
        output_format = 'json'

    UserDumper.add_representer(PosixPath, PathRepresenter())
    UserDumper.add_representer(WindowsPath, PathRepresenter())

    add_to_dumper(UserDumper, list(args))

    class DumpJsonFunction:
        """Dumps objects to a stream."""
        def __init__(self, dumper: Type[Dumper]) -> None:
            """Create a dump function."""
            self.dumper = dumper

        def __call__(
                self, obj: Any, sink: Union[str, Path, IO[AnyStr]],
                indent: Optional[int] = None, ensure_ascii: bool = True
                ) -> None:
            """Dump the object to a file or stream as JSON.

            The sink argument may be a string containing a path, a
            pathlib.Path object containing a path, or a stream to write
            to directly (e.g. an open file).

            Args:
                obj: An object to dump.
                sink: A place to save it to.
            """
            if isinstance(sink, str):
                sink = Path(sink)

            if isinstance(sink, Path):
                with sink.open('w') as f:
                    yaml.dump(
                            obj, f, Dumper=UserDumper,
                            indent=indent, allow_unicode=not ensure_ascii)
            else:
                yaml.dump(
                        obj, sink, Dumper=UserDumper,
                        indent=indent, allow_unicode=not ensure_ascii)

    return DumpJsonFunction(UserDumper)
