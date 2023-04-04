from .Description import Description
from .Type import Type
from .Link import Link
from ngts.nvos_tools.infra.ResultObj import ResultObj
from .nvos_consts import InternalNvosConsts
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import OutputFormat
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from .SignalDegrade import SignalDegrade
import time
import logging
import allure
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool

logger = logging.getLogger()


class IbInterface:
    port_obj = None
    description = None
    type = None
    link = None
    signal_degrade = None

    def __init__(self, port_obj):
        self.port_obj = port_obj
        self.description = Description(self.port_obj)
        self.type = Type(self.port_obj)
        self.link = Link(self.port_obj)
        self.signal_degrade = SignalDegrade(port_obj=self.port_obj)

    def wait_for_port_state(self, state, engine=None, timeout=InternalNvosConsts.DEFAULT_TIMEOUT, logical_state=None, sleep_time=2):
        with allure.step("Wait for '{port}' to reach state '{state}' (timeout: {timeout})".format(
                port=self.port_obj.name, state=state, timeout=timeout)):
            logger.info("Wait for '{port}' to reach state '{state}' (timeout: {timeout})".format(
                port=self.port_obj.name, state=state, timeout=timeout))
            if not engine:
                engine = TestToolkit.engines.dut

            result_obj = ResultObj(True, "")
            timer = timeout
            while self.port_obj.ib_interface.link.state.get_operational(engine) != state and timer > 0:
                time.sleep(sleep_time)
                timer -= sleep_time

            if self.port_obj.ib_interface.link.state.get_operational(engine) == state:
                logger.info("'{port}' successfully reached state '{state}'".format(
                    port=self.port_obj.name, state=state))
                result_obj.info = "'{port}' successfully reached state '{state}'".format(port=self.port_obj.name,
                                                                                         state=state)

            if timer <= 0:
                result_obj.info = "Timeout occurred while waiting for '{port}' to reach state '{state}'".format(
                    port=self.port_obj.name, state=state)
                result_obj.result = False
                return result_obj

            if logical_state:
                while self.port_obj.ib_interface.link.logical_port_state.get_operational(engine) != logical_state \
                        and timer > 0:
                    time.sleep(sleep_time)
                    timer -= sleep_time
                if self.port_obj.ib_interface.link.logical_port_state.get_operational(engine) == logical_state:
                    logger.info("'{port}' successfully reached logical_state '{state}'".format(
                        port=self.port_obj.name, state=logical_state))
                    result_obj.info += "\n'{port}' successfully reached logical_state '{state}'".format(
                        port=self.port_obj.name, state=logical_state)

                if timer <= 0:
                    result_obj.info += "\nTimeout occurred while waiting for '{port}' to reach logical_state " \
                        "'{state}'".format(port=self.port_obj.name, state=logical_state)
                    result_obj.result = False

            return result_obj

    def show_interface(self, dut_engine=None, output_format=OutputFormat.json):
        """
        Executes show interface
        :param dut_engine: ssh engine
        :param output_format: OutputFormat
        :return: str output
        """
        with allure.step('Execute show interface for {port_name}'.format(port_name=self.port_obj.name)):
            if not dut_engine:
                dut_engine = TestToolkit.engines.dut

            return SendCommandTool.execute_command(self.port_obj.api_obj[TestToolkit.tested_api].show_interface,
                                                   dut_engine, self.port_obj.name, output_format).get_returned_value()

    def action_clear_counter_for_all_interfaces(self, engine=None):
        with allure.step("Clear counters for all interfaces"):
            logging.info("Clear counters for all interfaces")

            if not engine:
                engine = TestToolkit.engines.dut

            result_obj = SendCommandTool.execute_command(self.port_obj.api_obj[TestToolkit.tested_api].
                                                         action_clear_counters, engine)
            return result_obj
