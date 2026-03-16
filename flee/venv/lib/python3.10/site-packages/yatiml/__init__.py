"""The :mod:`yatiml` module is the main API for YAtiML.

This module contains all the functions you need to use YAtiML.

Below, you will also find documentation for submodules. That is
developer documentation, you do not need it to use YAtiML.
"""

__version__ = '0.11.1'

__author__ = 'Lourens Veen'
__email__ = 'l.veen@esciencecenter.nl'

from yatiml.exceptions import RecognitionError, SeasoningError
from yatiml.loader import load_function
from yatiml.dumper import (
        DumpJsonFunctionType, dump_json_function, DumpsJsonFunctionType,
        dumps_json_function, dump_function, dumps_function)
from yatiml.helpers import Node, UnknownNode
from yatiml.util import bool_union_fix, String

import logging

logger = logging.getLogger('yatiml')
"""The YAtiML root logger. Use this to set YAtiML's log level.

In particular, if something goes wrong with loading or dumping from
or to YAML, and you want more debug output from YAtiML, use::

    import logging

    yatiml.logger.setLevel(logging.INFO)

or for even more::

    yatiml.logger.setLevel(logging.DEBUG)
"""

__all__ = [
    'logger', 'RecognitionError', 'SeasoningError', 'Node', 'UnknownNode',
    'String', 'load_function', 'DumpJsonFunctionType', 'dump_json_function',
    'DumpsJsonFunctionType', 'dumps_json_function', 'dump_function',
    'dumps_function', 'bool_union_fix']
