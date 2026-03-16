"""Defines the YAML document and version tag."""
import yatiml


class Document:
    """Represents a yMMSL document.

    This gets mixed in with a top-level content class, and takes
    care of a special ymmsl_version attribute in the root of the
    YAML file.
    """

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_mapping()
        node.require_attribute('ymmsl_version')
        node.require_attribute_value('ymmsl_version', 'v0.1')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.set_attribute('ymmsl_version', 'v0.1')
        # The above adds the attribute to the end, but we want it at
        # the top; this moves it there.
        node.yaml_node.value.insert(0, node.yaml_node.value[-1])
        del node.yaml_node.value[-1]

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        node.remove_attribute('ymmsl_version')
