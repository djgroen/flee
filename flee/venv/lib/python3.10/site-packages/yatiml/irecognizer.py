import abc
from textwrap import indent
from typing import Any, List, Set, Tuple
from typing_extensions import Type

import yaml


RecError = Tuple[str, List[Any]]
"""A recognition error.

The string is an error message, the list contains possible causes, which
are RecErrors themselves. We're not allowed recursive types in Python,
so we have to make do with Any.
"""


def format_rec_error(rec_error: RecError) -> str:
    """Formats a recognition error.

    This turns the error into a human-readable string.
    """
    def find_leaves(rec_error: RecError) -> List[str]:
        """Find errors with no causes by walking the tree."""
        message, causes = rec_error
        if not causes:
            return [message]

        return [m for c in causes for m in find_leaves(c)]

    leaves = find_leaves(rec_error)

    unique_leaves = list()
    for leaf in leaves:
        if leaf not in unique_leaves:
            unique_leaves.append(leaf)

    if len(unique_leaves) == 1:
        return 'An error occurred:\n{}'.format(unique_leaves[0])
    else:
        return (
                'Multiple things are allowed here, but none of them were'
                ' recognised correctly. At least one of these errors should'
                ' apply to what you want to do; please solve that one and'
                ' ignore the others.\n{}').format('\n\n'.join(unique_leaves))


REC_OK = ('', [])       # type: RecError
"""No error empty object.

This can be passed wherever a RecError is returned and no error
occurred. Having this constant keeps us from making a zillion
objects, and it makes the code a bit more readable.
"""


RecResult = Tuple[Set[Type], RecError]
"""A recognition result.

The set is a set of recognised types, the RecError an error to display
if no type was recognised or more than one type was recognised.
"""


class IRecognizer(abc.ABC):
    """An interface for Recognizer.

    I don't like interfaces that have only one implementation, but
    needed one here to break an import cycle.
    """

    def recognize(self, node: yaml.Node, expected_type: Type) -> RecResult:
        """Figure out how to interpret this node.

        This is not quite a type check. This function makes a list of
        all types that match the expected type and also the node, and
        returns that list. The goal here is not to test validity, but
        to determine how to process this node further.

        That said, it will recognize built-in types only in case of
        an exact match.

        Args:
            node: The YAML node to recognize.
            expected_type: The type we expect this node to be, based
                    on the context provided by our type definitions.

        Returns:
            A list of matching types.
        """
        raise NotImplementedError()  # pragma: no cover
