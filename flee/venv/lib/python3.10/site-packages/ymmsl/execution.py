"""Definitions for specifying how to start a component."""
from enum import Enum
from pathlib import Path
from typing import cast, Dict, List, Optional, Union

import yaml
import yatiml

from ymmsl.identity import Reference


class BaseEnv(Enum):
    """Describes the base shell environment for execution.

    Several options in :class:`Implementation` describe additions to the
    shell environment to make subsequently, but we need to start
    somewhere. Different starting points make sense in different
    contexts, so there's a choice:

    ``LOGIN`` starts from an environment that resembles the default
    environment of the user running the simulation. The exact
    environment you get when you log in depends on whether you're on a
    text terminal, graphical terminal, or using SSH, and also on the
    operating system and any local changes made by your system
    administrator. This cannot be reproduced exactly in all
    circumstances, but the below should get close on most systems.

    This will copy ``TERM``, ``HOME``, ``SHELL``, ``USER``, and
    ``LOGNAME`` from the manager environment, then run ``/bin/bash``
    and have it load ``/etc/environment``, ``/etc/profile``, and then
    the first of ``~/.bash_profile``, ``~/.bash_login``, and
    ``~/.profile`` that it finds. Note that on most machines, these
    files will load other files in turn, often including ``~/.bashrc``.

    ``CLEAN`` starts from the environment that ``muscle_manager`` was
    started in, and then unloads any loaded modules and deactivates any
    active Python virtual environments. Any modules specified in
    ``modules`` and any virtual environment specified in ``virtual_env``
    will be activate after that, of course.

    Note that on some HPC machines, SLURM is made available though the
    environment modules. If you use the SRUNMPI execution model, then
    you'll have to load it again explicitly to make the ``srun`` command
    available, or MUSCLE3 won't be able to start your program.

    ``MANAGER`` starts from the exact environment that
    ``muscle_manager`` was started in, including any loaded modules and
    active virtual environments. Any modules specified in ``modules``
    are then loaded on top of this, which may cause some of the existing
    modules to be unloaded if they are incompatible. If a virtual
    environment is specified in ``virtual_env``, then it will replace
    the active environment.

    """
    LOGIN = 1
    """The environment you get after logging in when using bash."""
    CLEAN = 2
    """Like MANAGER, but with any modules unloaded and venvs deactivated."""
    MANAGER = 3
    """The environment the manager was started in."""

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.is_scalar(str):
            val = cast(str, node.get_value())
            node.set_value(val.upper())

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        val = node.get_value()
        if isinstance(val, str):
            node.set_value(val.lower())


class KeepsStateForNextUse(Enum):
    """Describes whether an implementation keeps internal state between
    iterations of the reuse loop.

    See also :ref:`Keeps state for next use`.
    """

    NECESSARY = 1
    """The implementation has an internal state that is necessary for
    continuing the implementation."""
    NO = 2
    """The implementation has no internal state."""
    HELPFUL = 3
    """The implementation has an internal state, though this could be
    regenerated. Doing so may be expensive."""

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.is_scalar(str):
            val = cast(str, node.get_value())
            node.set_value(val.upper())

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        val = node.get_value()
        if isinstance(val, str):
            node.set_value(val.lower())


class ExecutionModel(Enum):
    """Describes how to start a model component."""
    DIRECT = 1
    """Start directly on the allocated core(s), without MPI."""
    OPENMPI = 2
    """Start using OpenMPI's mpirun."""
    INTELMPI = 3
    """Start using Intel MPI's mpirun."""
    SRUNMPI = 4
    """Start MPI implementation using srun."""

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.is_scalar(str):
            val = cast(str, node.get_value())
            node.set_value(val.upper())

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        val = node.get_value()
        if isinstance(val, str):
            node.set_value(val.lower())


class Implementation:
    """Describes an installed implementation.

    An Implementation normally has an ``executable`` and any other
    needed attributes, with ``script`` set to None. You should specify
    a script only as a last resort, probably after getting some help
    from the authors of this library. If a script is specified, all
    other attributes except for the name, the execution model,
    can_share_resources and keeps_state_for_next_use must be ``None``.

    If base_env is not specified then it defaults to MANAGER.

    For ``execution_model``, the following values are supported:

    direct
      The program will be executed directly. Use this for non-MPI
      programs.

    openmpi
      For MPI programs that should be started using OpenMPI's mpirun.

    intelmpi
      For MPI programs that should be started using Intel MPI's
      mpirun.

    The ``can_share_resources`` attribute describes whether this
    implementation can share resources (cores) with other components
    in a macro-micro coupling. Set this to ``False`` if the
    implementation does significant computing inside of its time
    update loop after having sent messages on its O_I port(s) but
    before receiving messages on its S port(s). In the unlikely case
    that it's doing significant computing before receiving for F_INIT
    or after sending its O_F messages, likewise set this to ``False``.

    Setting this to ``False`` unnecessarily will waste core hours,
    setting it to ``True`` incorrectly will slow down your simulation.

    Attributes:
        name: Name of the implementation
        base_env: Base environment to start from
        modules: HPC software modules to load
        virtual_env: Path to a virtual env to activate
        env: Environment variables to set
        execution_model: How to start the executable
        executable: Full path to executable to run
        args: Arguments to pass to the executable
        script: A script that starts the implementation
        can_share_resources: Whether this implementation can share
            resources (cores) with other components or not
        keeps_state_for_next_use: Does this implementation keep state
            for the next iteration of the reuse loop. See
            :class:`KeepsStateForNextUse`.
    """

    def __init__(
            self,
            name: Reference,
            base_env: Optional[BaseEnv] = None,
            modules: Union[str, List[str], None] = None,
            virtual_env: Optional[Path] = None,
            env: Optional[Dict[str, str]] = None,
            execution_model: ExecutionModel = ExecutionModel.DIRECT,
            executable: Optional[Path] = None,
            args: Union[str, List[str], None] = None,
            script: Union[str, List[str], None] = None,
            can_share_resources: bool = True,
            keeps_state_for_next_use: KeepsStateForNextUse
            = KeepsStateForNextUse.NECESSARY
            ) -> None:
        """Create an Implementation description.

        An Implementation normally has an ``executable`` and any other
        needed arguments, with ``script`` set to ``None``. You should
        specify a script only as a last resort, probably after getting
        some help from the authors of this library. If ``script`` is
        specified, all other arguments except for ``name``,
        ``execution model``, ``can_share_resources`` and
        ``keeps_state_for_next_use`` must be ``None``.

        If script is a list, each string in it is a line, and the
        lines will be concatenated into a single string to put into
        the script attribute.

        Args:
            name: Name of the implementation
            base_env: Base environment to start from, defaults to clean
            modules: HPC software modules to load
            virtual_env: Path to a virtual env to activate
            env: Environment variables to set
            execution_model: How to start the executable, see above.
            executable: Full path to executable to run
            args: Arguments to pass to the executable
            script: Script that starts the implementation
            can_share_resources: Whether this implementation can share
                    resources (cores) with other components or not.
                    See above.
            keeps_state_for_next_use: Does this implementation keep state for
                the next iteration of the reuse loop. See
                :class:`ImplementationState`.
        """
        if script is not None:
            err_arg = []
            if base_env is not None:
                err_arg.append('"base_env"')
            if modules is not None:
                err_arg.append('"modules"')
            if virtual_env is not None:
                err_arg.append('"virtual_env"')
            if env is not None:
                err_arg.append('"env"')
            if executable is not None:
                err_arg.append('"executable"')
            if args is not None:
                err_arg.append('"args"')
            if err_arg:
                raise RuntimeError(
                        'When creating an Implementation, script was specified'
                        f' together with the arguments {", ".join(err_arg)},'
                        ' which is not supported, as they are supposed to be'
                        ' inside the script if there is one. Please use either'
                        ' a script or the arguments listed above.')

        if executable is None and script is None:
            raise RuntimeError(
                    f'In {name}, neither a script nor an executable was given.'
                    ' Please specify either a script, or the other parameters.'
                    )

        self.name = name

        if isinstance(script, list):
            self.script = '\n'.join(script) + '\n'  # type: Optional[str]
        else:
            self.script = script

        self.base_env = base_env if base_env else BaseEnv.MANAGER

        if isinstance(modules, str):
            self.modules = modules.split(' ')   # type: Optional[List[str]]
        else:
            self.modules = modules
        self.virtual_env = virtual_env
        if env is None:
            env = dict()
        self.env = env
        self.execution_model = execution_model
        self.executable = executable

        if isinstance(args, str):
            self.args = [args]  # type: Optional[List[str]]
        else:
            self.args = args

        self.can_share_resources = can_share_resources
        self.keeps_state_for_next_use = keeps_state_for_next_use

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        # There's no ambiguity, and we want to allow some leeway
        # and savorize things, so only require that the node is a mapping.
        node.require_mapping()

    @classmethod
    def _yatiml_savorize(cls, node: yatiml.Node) -> None:
        if node.has_attribute('env'):
            env_node = node.get_attribute('env')
            if env_node.is_mapping():
                for _, value_node in env_node.yaml_node.value:
                    if isinstance(value_node, yaml.ScalarNode):
                        if value_node.tag == 'tag:yaml.org,2002:int':
                            value_node.tag = 'tag:yaml.org,2002:str'
                        if value_node.tag == 'tag:yaml.org,2002:float':
                            value_node.tag = 'tag:yaml.org,2002:str'
                        if value_node.tag == 'tag:yaml.org,2002:bool':
                            value_node.tag = 'tag:yaml.org,2002:str'

    _yatiml_defaults = {
        'base_env': 'manager',
        'execution_model': 'direct',
        'keeps_state_for_next_use': 'necessary'}

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        if node.has_attribute('script'):
            script_node = node.get_attribute('script')
            if script_node.is_scalar(str):
                text = cast(str, script_node.get_value())
                if '\n' in text:
                    cast(yaml.ScalarNode, script_node.yaml_node).style = '|'

        node.remove_attributes_with_default_values(cls)
        if node.has_attribute('env'):
            env_attr = node.get_attribute('env')
            if env_attr.is_mapping():
                if env_attr.is_empty():
                    node.remove_attribute('env')


class ResourceRequirements:
    """Describes resources to allocate for components.

    Attributes:
        name: Name of the component to configure.
    """
    def __init__(self, name: Reference) -> None:
        """Create a ResourceRequirements description.

        Args:
            name: Name of the component to configure.
        """
        self.name = name

    @classmethod
    def _yatiml_recognize(cls, node: yatiml.UnknownNode) -> None:
        raise yatiml.RecognitionError(
                'Please specify either "threads" or "mpi_processes".')


class ThreadedResReq(ResourceRequirements):
    """Describes resources for threaded implementations.

    This includes singlethreaded and multithreaded implementations
    that do not support MPI. As many cores as specified will be
    allocated on a single node, for each instance.

    Attributes:
        name: Name of the component to configure.
        threads: Number of threads/cores per instance.
    """

    def __init__(self, name: Reference, threads: int) -> None:
        """Create a ThreadedResourceRequirements description.

        Args:
            name: Name of the component to configure.
            threads: Number of threads (cores) per instance.
        """
        super().__init__(name)
        self.threads = threads


class MPICoresResReq(ResourceRequirements):
    """Describes resources for simple MPI implementations.

    This allocates individual cores or sets of cores on the same node
    for a given number of MPI processes per instance.

    Attributes:
        name: Name of the component to configure.
        mpi_processes: Number of MPI processes to start.
        threads_per_mpi_process: Number of threads/cores per process.
    """

    def __init__(
            self, name: Reference, mpi_processes: int,
            threads_per_mpi_process: int = 1) -> None:
        """Create a ThreadedMPIResourceRequirements description.

        Args:
            name: Name of the component to configure.
            mpi_processes: Number of MPI processes to start.
            threads_per_mpi_process: Number of threads/cores per
                    process. Defaults to 1.
        """
        super().__init__(name)
        self.mpi_processes = mpi_processes
        self.threads_per_mpi_process = threads_per_mpi_process

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.remove_attributes_with_default_values(cls)


class MPINodesResReq(ResourceRequirements):
    """Describes resources for node based MPI implementations.

    This allocates resources for an MPI process in terms of nodes and
    cores, processes and threads on them.

    Attributes:
        name: Name of the component to configure.
        nodes: Number of nodes to reserve.
        mpi_processes_per_node: Number of MPI processes to start on
                each node.
        threads_per_mpi_process: Number of threads/cores per process.
    """

    def __init__(
            self, name: Reference, nodes: int,
            mpi_processes_per_node: int, threads_per_mpi_process: int = 1
            ) -> None:
        """Create a NodeBasedMPIResourceRequirements description.

        Args:
            name: Name of the component to configure.
            nodes: Number of nodes to reserve.
            mpi_processes_per_node: Number of MPI processes to start
                    on each node.
            threads_per_mpi_process: Number of threads/cores per
                    process. Defaults to 1.
        """
        super().__init__(name)
        self.nodes = nodes
        self.mpi_processes_per_node = mpi_processes_per_node
        self.threads_per_mpi_process = threads_per_mpi_process

    @classmethod
    def _yatiml_sweeten(cls, node: yatiml.Node) -> None:
        node.remove_attributes_with_default_values(cls)
