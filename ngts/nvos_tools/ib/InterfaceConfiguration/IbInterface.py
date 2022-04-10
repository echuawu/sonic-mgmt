from .Description import Description
from .Type import Type
from .Pluggable import Pluggable
from .Link import Link
from ngts.nvos_tools.infra.ResultObj import ResultObj
from .nvos_consts import InternalNvosConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
import time
import logging

logger = logging.getLogger()


class IbInterface:
    port_obj = None
    description = None
    type = None
    pluggable = None
    link = None

    def __init__(self, port_obj):
        self.port_obj = port_obj
        self.description = Description(port_obj)
        self.type = Type(port_obj)
        self.pluggable = Pluggable(port_obj)
        self.link = Link(port_obj)

    def wait_for_port_state(self, state, engine=None, timeout=InternalNvosConsts.DEFAULT_TIMEOUT):
        logging.info("Waiting for port '{port}' to reach state '{state}' (timeout: {timeout})".format(
                     port=self.port_obj.name, state=state, timeout=timeout))

        if not engine:
            engine = TestToolkit.engines.dut

        timer = timeout
        while self.port_obj.ib_interface.link.state.get_operational(engine) != state and timer > 0:
            time.sleep(2)
            timer -= 2

        if self.port_obj.ib_interface.link.state.get_operational(engine) == state:
            return ResultObj(True, "port '{port}' successfully reached state '{state}'".format(
                             port=self.port_obj.name, state=state))

        if timer <= 0:
            return ResultObj(False, "Timeout occurred while waiting for port '{port}' to reach state 'state'".format(
                             port=self.port_obj.name, state=state))
