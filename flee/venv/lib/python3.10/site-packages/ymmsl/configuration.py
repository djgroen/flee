"""This module contains all the definitions for yMMSL."""
from collections import OrderedDict
import collections.abc as abc
import logging
from pathlib import Path
from typing import (
        Dict, List, MutableMapping, Optional, Sequence, Union, cast)

import yatiml
import yaml

from ymmsl.checkpoint import Checkpoints
from ymmsl.document import Document
from ymmsl.identity import Reference
from ymmsl.execution import (
        ExecutionModel, Implementation,
        ResourceRequirements, ThreadedResReq)
from ymmsl.settings import Settings
from ymmsl.model import Model, ModelReference


_logger = logging.getLogger(__name__)

# This should be a local definition, but that triggers a mypy issue:
# https://github.com/python/mypy/issues/7281
_ImplType = Dict[Reference, Implementation]


_ResType = MutableMapping[Reference, ResourceRequirements]


class PartialConfiguration(Document):
    """Top-level class for all information in a yMMSL file.

    Attributes:
        model: A model to run.
        settings: Settings to run the model with.
        implementations: Implementations to use to run the model.
            Dictionary mapping implementation names (as References) to
            Implementation objects.
        resources: Resources to allocate for the model components.
            Dictionary mapping component names to ResourceRequirements
            objects.
        description: A human-readable description of the configuration.
        checkpoints: Defines when each model component should create a snapshot
        resume: Defines what snapshot each model component should resume from
    """
    def __init__(self,
                 model: Optional[ModelReference] = None,
                 settings: Optional[Settings] = None,
                 implementations: Optional[Union[
                     List[Implementation],
                     Dict[Reference, Implementation]]] = None,
                 resources: Optional[Union[
                     Sequence[ResourceRequirements],
                     MutableMapping[Reference, ResourceRequirements]]] = None,
                 description: Optional[str] = None,
                 checkpoints: Optional[Checkpoints] = None,
                 resume: Optional[Dict[Reference, Path]] = None
                 ) -> None:
        """Create a Configuration.

        Implementations and resources may be either a list of such
        objects, or a dictionary matching the attribute format (see
        above).

        Args:
            model: A description of the model to run.
            settings: Settings to run the model with.
            implementations: Implementations to choose from.
            resources: Resources to allocate for the model components.
            description: Human-readable description
            checkpoints: When each component should create a snapshot
            resume: What snapshot each component should resume from

        """
        self.model = model

        if settings is None:
            self.settings = Settings()
        else:
            self.settings = settings

        if implementations is None:
            self.implementations = dict()   # type: _ImplType
        elif isinstance(implementations, list):
            self.implementations = OrderedDict([
                (impl.name, impl) for impl in implementations])
        else:
            self.implementations = implementations

        if resources is None:
            self.resources = dict()     # type: _ResType
        elif isinstance(resources, abc.Sequence):
            self.resources = OrderedDict([
                (res.name, res) for res in resources])
        else:
            self.resources = resources

        if description is None:
            self.description = ''
        else:
            self.description = description

        if checkpoints is None:
            self.checkpoints = Checkpoints()
        else:
            self.checkpoints = checkpoints

        if resume is None:
            self.resume = dict()    # type: Dict[Reference, Path]
        else:
            self.resume = resume

    def update(self, overlay: 'PartialConfiguration') -> None:
        """Update this configuration with the given overlay.

        This will update the model according to :meth:`Model.update`, copy
        settings from overlay on top of the current settings, overwrite
        implementations with the same name and add implementations with a new
        name, and likewise for resources and resume. The description of the
        overlay is appended to the current description. Checkpoints are updated
        according to :meth:`Checkpoints.update`.

        Args:
            overlay: A configuration to overlay onto this one.
        """
        # beware of isinstance matching parent classes...
        if self.model is None:
            self.model = overlay.model
        elif isinstance(overlay.model, Model):
            if isinstance(self.model, Model):
                self.model.update(overlay.model)
            else:
                # self.model is a ModelReference
                self.model = overlay.model
        elif isinstance(overlay.model, ModelReference):
            self.model.name = overlay.model.name

        self.settings.update(overlay.settings)
        self.implementations.update(overlay.implementations)
        self.resources.update(overlay.resources)

        if not self.description:
            self.description = overlay.description
        elif overlay.description:
            self.description += '\n\n' + overlay.description

        self.checkpoints.update(overlay.checkpoints)
        self.resume.update(overlay.resume)

    def as_configuration(self) -> 'Configuration':
        """Converts to a full Configuration object.

        This checks that this PartialConfiguration has all the pieces
        needed to run a simulation, and if so converts it to a
        Configuration object.

        Note that this doesn't check references, just that there is
        a model, implementations and resources. For the more extensive
        check, see :meth:`Configuration.check_consistent`.

        Returns:
            A corresponding Configuration.

        Raises:
            ValueError: If this configuration isn't complete.
        """
        if (
                self.model is not None and isinstance(self.model, Model) and
                self.implementations and self.resources):
            return Configuration(
                    self.model, self.settings, self.implementations,
                    self.resources, self.description, self.checkpoints,
                    self.resume)
        raise ValueError(
                'Model, implementations or resources are missing from the'
                ' configuration.')

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # Because of the syntactic sugar below, the YAML doesn't match
        # the types declared above. So we override recognition, and
        # since the attributes are all optional, we have nothing to
        # check except that it's a valid Document (with a version tag).
        Document._yatiml_recognize(node)

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if not node.has_attribute('settings'):
            node.set_attribute('settings', None)
        node.map_attribute_to_index('implementations', 'name', 'script')
        node.map_attribute_to_index('resources', 'name')

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.get_attribute('model').is_scalar(type(None)):
            node.remove_attribute('model')

        if node.get_attribute('settings').is_scalar(type(None)):
            node.remove_attribute('settings')
        if len(node.get_attribute('settings').yaml_node.value) == 0:
            node.remove_attribute('settings')

        impl = node.get_attribute('implementations')
        if (
                impl.is_scalar(type(None)) or
                impl.is_mapping() and impl.is_empty()):
            node.remove_attribute('implementations')
        node.index_attribute_to_map('implementations', 'name', 'script')

        res = node.get_attribute('resources')
        if (
                res.is_scalar(type(None)) or
                res.is_mapping() and res.is_empty()):
            node.remove_attribute('resources')
        node.index_attribute_to_map('resources', 'name')

        descr = node.get_attribute('description')
        if descr.is_scalar(type(None)) or descr.get_value() == '':
            node.remove_attribute('description')
        if descr.is_scalar(str) and '\n' in cast(str, descr.get_value()):
            # output multi-line string in literal mode
            cast(yaml.ScalarNode, descr.yaml_node).style = '|'

        cp = node.get_attribute('checkpoints')
        if (
                cp.is_scalar(type(None)) or
                cp.is_mapping() and cp.is_empty()):
            node.remove_attribute('checkpoints')

        resu = node.get_attribute('resume')
        if (
                resu.is_scalar(type(None)) or
                resu.is_mapping() and resu.is_empty()):
            node.remove_attribute('resume')


class Configuration(PartialConfiguration):
    """Configuration that includes all information for a simulation.

    PartialConfiguration has some optional attributes, because we want
    to allow configuration files which only contain some of the
    information needed to run a simulation. At some point however,
    you need all the bits, and this class requires them.

    When loading a yMMSL file, you will automatically get an object
    of this class if all the required components are there; if the
    file is incomplete, you'll get a PartialConfiguration instead.

    Attributes:
        model: A model to run.
        settings: Settings to run the model with.
        implementations: Implementations to use to run the model.
            Dictionary mapping implementation names (as References) to
            Implementation objects.
        resources: Resources to allocate for the model components.
            Dictionary mapping component names to Resources objects.
        description: A human-readable description of the configuration.
        checkpoints: Defines when each model component should create a snapshot
        resume: Defines what snapshot each model component should resume from
    """
    def __init__(self,
                 model: Model,
                 settings: Optional[Settings] = None,
                 implementations: Union[
                     List[Implementation],
                     Dict[Reference, Implementation]] = [],
                 resources: Union[
                     Sequence[ResourceRequirements],
                     MutableMapping[Reference, ResourceRequirements]] = [],
                 description: Optional[str] = None,
                 checkpoints: Optional[Checkpoints] = None,
                 resume: Optional[Dict[Reference, Path]] = None
                 ) -> None:
        """Create a Configuration.

        Implementations and resources may be either a list of such
        objects, or a dictionary matching the attribute format (see
        above).

        Args:
            model: A description of the model to run.
            settings: Settings to run the model with.
            implementations: Implementations to choose from.
            resources: Resources to allocate for the model components.
            description: Human-readable description
            checkpoints: When each component should create a snapshot
            resume: What snapshot each component should resume from

        """
        # Make mypy recognize that, unlike PartialConfiguration.model,
        # Configuration.model always has type Model
        self.model: Model
        super().__init__(
                model, settings, implementations, resources, description,
                checkpoints, resume)

    def check_consistent(self) -> None:
        """Checks that the configuration is internally consistent.

        This checks whether all conduits are connected to existing
        components, that there's an implementation for every component,
        and that resources have been requested for each component.

        If any of these requirements is false, this function will
        raise a RuntimeError with an explanation of the problem.

        """
        self.model.check_consistent()

        for comp in self.model.components:
            if comp.implementation not in self.implementations:
                raise RuntimeError((
                        'Model component {} is missing an'
                        ' implementation').format(comp))
            if comp.name not in self.resources:
                raise RuntimeError((
                        'Model component {} is missing a resource'
                        ' allocation.').format(comp))

            impl = self.implementations[comp.implementation]
            res = self.resources[comp.name]
            if impl.execution_model == ExecutionModel.DIRECT:
                if not isinstance(res, ThreadedResReq) and impl.script is None:
                    # Assume that people know what they're doing if they use
                    # script for specifying an implementation.
                    raise RuntimeError((
                        'Model component {}\'s implementation does not'
                        ' specify MPI, but mpi_processes are specified in its'
                        ' resources. Please either set "execution_model" to'
                        ' an MPI model, or specify a number of threads.'
                        ).format(comp))
            else:
                if isinstance(res, ThreadedResReq):
                    raise RuntimeError((
                        'Model component {}\'s implementation specifies MPI,'
                        ' but threads are specified in its resources. Please'
                        ' either set "execution_model" to "direct", or'
                        ' specify a number of mpi processes.').format(comp))

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        node.require_attribute('model', Model)
        node.require_attribute('implementations')
        node.require_attribute('resources')
