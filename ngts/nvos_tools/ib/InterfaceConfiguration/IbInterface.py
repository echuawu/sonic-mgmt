from .Description import Description
from .Type import Type
from .Pluggable import Pluggable
from .Link import Link
from ngts.nvos_tools.infra.ResultObj import ResultObj
from .nvos_consts import InternalNvosConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from .SignalDegrade import SignalDegrade
import time
import logging
import allure

logger = logging.getLogger()


class IbInterface:
    port_obj = None
    description = None
    type = None
    pluggable = None
    link = None
    signal_degrade = None

    def __init__(self, port_obj):
        self.port_obj = port_obj
        self.description = Description(self.port_obj)
        self.type = Type(self.port_obj)
        self.pluggable = Pluggable(self.port_obj)
        self.link = Link(self.port_obj)
        self.signal_degrade = SignalDegrade(port_obj=self.port_obj)

    def wait_for_port_state(self, state, engine=None, timeout=InternalNvosConsts.DEFAULT_TIMEOUT, logical_state=None):
        with allure.step("Wait for '{port}' to reach state '{state}' (timeout: {timeout})".format(
                port=self.port_obj.name, state=state, timeout=timeout)):
            logger.info("Wait for '{port}' to reach state '{state}' (timeout: {timeout})".format(
                port=self.port_obj.name, state=state, timeout=timeout))
            if not engine:
                engine = TestToolkit.engines.dut

            result_obj = ResultObj(True, "")
            timer = timeout
            while self.port_obj.ib_interface.link.state.get_operational(engine) != state and timer > 0:
                time.sleep(2)
                timer -= 2

            if self.port_obj.ib_interface.link.state.get_operational(engine) == state:
                logger.info("'{port}' successfully reached state '{state}'".format(
                    port=self.port_obj.name, state=state))
                result_obj.info = "'{port}' successfully reached state '{state}'".format(port=self.port_obj.name,
                                                                                         state=state)

            if timer <= 0:
                result_obj.info = "Timeout occurred while waiting for '{port}' to reach state 'state'".format(
                    port=self.port_obj.name, state=state)
                result_obj.result = False
                return result_obj

            if logical_state:
                while self.port_obj.ib_interface.link.logical_port_state.get_operational(engine) != logical_state \
                        and timer > 0:
                    time.sleep(2)
                    timer -= 2
                if self.port_obj.ib_interface.link.logical_port_state.get_operational(engine) == logical_state:
                    logger.info("'{port}' successfully reached logical_state '{state}'".format(
                        port=self.port_obj.name, state=logical_state))
                    result_obj.info += "\n'{port}' successfully reached logical_state '{state}'".format(
                        port=self.port_obj.name, state=logical_state)

                if timer <= 0:
                    result_obj.info += "Timeout occurred while waiting for '{port}' to reach logical_state " \
                        "'state'".format(port=self.port_obj.name, state=logical_state)
                    result_obj.result = False

            return result_obj
