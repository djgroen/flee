"""Definitions for specifying model settings."""
from collections import OrderedDict
from collections.abc import MutableMapping
from copy import deepcopy
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import yatiml

from ymmsl.identity import Reference


SettingValue = Union[
        str, int, float, bool, List[int], List[float], List[List[float]],
        yatiml.bool_union_fix]


class Settings(MutableMapping):
    """Settings for doing an experiment.

    An experiment is done by running a model with particular settings,
    for the submodel scales, model parameters and any other configuration.
    """

    def __init__(
            self,
            settings: Optional[Dict[str, SettingValue]] = None
            ) -> None:
        """Create a Settings object.

        This will make a deep copy of the settings argument, if
        given.

        Args:
            settings: Setting values to initialise a model with.

        """
        self._store = OrderedDict()  # type: Dict[Reference, SettingValue]

        if settings is not None:
            for key, value in settings.items():
                self[key] = deepcopy(value)

    def __eq__(self, other: Any) -> bool:
        """Returns whether keys and values are identical.

        The comparison ignores the order of the settings.
        """
        if not isinstance(other, Settings):
            return NotImplemented
        return dict(self._store.items()) == dict(other._store.items())

    def __str__(self) -> str:
        """Represent as a string."""
        return str(self.as_ordered_dict())

    def __getitem__(self, key: Union[str, Reference]) -> SettingValue:
        """Returns an item, implements settings[name]."""
        if isinstance(key, str):
            key = Reference(key)
        return self._store[key]

    def __setitem__(self, key: Union[str, Reference], value: SettingValue
                    ) -> None:
        """Sets a value, implements settings[name] = value."""
        if isinstance(key, str):
            key = Reference(key)
        self._store[key] = value

    def __delitem__(self, key: Union[str, Reference]) -> None:
        """Deletes a value, implements del(settings[name])."""
        if isinstance(key, str):
            key = Reference(key)
        del self._store[key]

    def __iter__(self) -> Iterator[Tuple[Reference, SettingValue]]:
        """Iterate through the settings' key, value pairs."""
        return iter(self._store)  # type: ignore

    def __len__(self) -> int:
        """Returns the number of settings."""
        return len(self._store)

    def ordered_items(self) -> List[Tuple[Reference, SettingValue]]:
        """Return settings as a list of tuples."""
        result = list()
        for key, value in self._store.items():
            result.append((key, value))
        return result

    def copy(self) -> 'Settings':
        """Makes a shallow copy of these settings and returns it."""
        new_settings = Settings()
        new_settings._store = self._store.copy()
        return new_settings

    def as_ordered_dict(self) -> OrderedDict:
        """Represent as a dictionary of plain built-in types.

        Returns: A dictionary that uses only built-in types, containing
            the configuration.
        """
        odict = OrderedDict()     # type: OrderedDict[str, SettingValue]
        for key, value in self._store.items():
            odict[str(key)] = value
        return odict

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # In the YAML file, a Settings is just a mapping...
        node.require_mapping()

    def _yatiml_attributes(self) -> Dict:
        # ...so we just give YAtiML our internal mapping to serialise
        return self._store

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        # wrap the existing mapping into a new mapping with attribute settings
        setting_values = node.yaml_node
        node.make_mapping()
        node.set_attribute('settings', setting_values)

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        # format lists and arrays nicely
        for _, value_node in node.yaml_node.value:
            if value_node.tag == 'tag:yaml.org,2002:seq':
                # this attribute is a list or list-of-list
                if len(value_node.value) > 0:
                    if value_node.value[0].tag != 'tag:yaml.org,2002:seq':
                        value_node.flow_style = True
                    else:
                        value_node.flow_style = False
                        for row_node in value_node.value:
                            row_node.flow_style = True
