"""Model representing a machine."""

from logging import Logger
from logging import getLogger


logger: Logger = getLogger(__name__)


class Machine:
    """Object representing a machine and its state and configuration."""

    def __init__(self, machine_name: str):
        """Initialize a new MachineState instance."""
        logger.debug("Instantiating new Machine: %s", machine_name)
        #: The name of the machine
        self.name: str = machine_name
