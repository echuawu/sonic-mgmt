from ngts.nvos_constants.constants_nvos import ConfState
from .IfIndex import IfIndex
from .Ip import Ip
from .Link import LinkMgmt
from .Type import Type
from ngts.nvos_tools.ib.InterfaceConfiguration.nvos_consts import InternalNvosConsts, IbInterfaceConsts
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ResultObj import ResultObj
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.openapi.openapi_ib_interface_clis import OpenApiIbInterfaceCli
from ngts.nvos_constants.constants_nvos import ApiType, IbConsts, ActionConsts
from ngts.nvos_tools.acl.acl import Acl
from retry import retry
import allure
import logging
import time
import re

logger = logging.getLogger()


class Interface(BaseComponent):
    def __init__(self, parent_obj, port_name="", path=None):
        self.mgmt_path = path if path else 'interface'
        BaseComponent.__init__(self, parent=parent_obj,
                               path='/interface' + (f'/{port_name}' if port_name else ''),
                               api={ApiType.NVUE: NvueIbInterfaceCli, ApiType.OPENAPI: OpenApiIbInterfaceCli})
        self.port_obj = parent_obj
        self.type = Type(self.port_obj)
        self.ifindex = IfIndex(self.port_obj)
        self.ip = Ip(self)
        self.link = LinkMgmt(self)
        self.plan_ports = self.plan_ports = BaseComponent(self, path='/plan-ports')
        self.acl = Acl(self)

    def wait_for_port_state(self, state, timeout=InternalNvosConsts.DEFAULT_TIMEOUT, logical_state=None, sleep_time=2,
                            dut_engine=None):
        with allure.step("Wait for '{port}' to reach state '{state}' (timeout: {timeout})".format(
                port=self.port_obj.name, state=state, timeout=timeout)):
            logger.info("Wait for '{port}' to reach state '{state}' (timeout: {timeout})".format(
                port=self.port_obj.name, state=state, timeout=timeout))

            result_obj = ResultObj(True, "")
            timer = timeout
            while OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                    self.link.show(dut_engine=dut_engine)).\
                    get_returned_value()[IbInterfaceConsts.LINK_STATE] != state and timer > 0:
                time.sleep(sleep_time)
                timer -= sleep_time

            if OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                    self.link.show(dut_engine=dut_engine)).get_returned_value()[IbInterfaceConsts.LINK_STATE] == state:
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
                while OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                        self.port_obj.ib_interface.link.show(dut_engine=dut_engine)). \
                        get_returned_value()[IbInterfaceConsts.LINK_LOGICAL_PORT_STATE] != logical_state and timer > 0:
                    time.sleep(sleep_time)
                    timer -= sleep_time
                if OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                        self.link.show(dut_engine=dut_engine)). \
                        get_returned_value()[IbInterfaceConsts.LINK_LOGICAL_PORT_STATE] == logical_state:
                    logger.info("'{port}' successfully reached logical_state '{state}'".format(
                        port=self.port_obj.name, state=logical_state))
                    result_obj.info += "\n'{port}' successfully reached logical_state '{state}'".format(
                        port=self.port_obj.name, state=logical_state)

                if timer <= 0:
                    result_obj.info += "\nTimeout occurred while waiting for '{port}' to reach logical_state " \
                        "'{state}'".format(port=self.port_obj.name, state=logical_state)
                    result_obj.result = False

            return result_obj

    @retry(Exception, tries=10, delay=2)
    def wait_for_mtu_changed(self, mtu_to_verify):
        with allure.step("Waiting for ib0 port mtu changed to {}".format(mtu_to_verify)):
            output_dictionary = OutputParsingTool.parse_show_interface_link_output_to_dictionary(
                self.link.show(rev=ConfState.APPLIED)).get_returned_value()
            current_mtu = output_dictionary[IbInterfaceConsts.LINK_MTU]
            assert current_mtu == mtu_to_verify, "Current mtu {} is not as expected {}".\
                format(current_mtu, mtu_to_verify)

    def action_clear_counter_for_all_interfaces(self, engine=None, fae_param=""):
        with allure.step("Clear counters for all interfaces"):
            logging.info("Clear counters for all interfaces")

            if not engine:
                engine = TestToolkit.engines.dut
            result_obj = SendCommandTool.execute_command(self.port_obj.api_obj[TestToolkit.tested_api].action_clear_counters, engine, self.mgmt_path, fae_param)

            return result_obj

    def action_clear_counter_for_interface(self, engine=None, interface_name="", fae_param=""):
        with allure.step("Clear counters for interface {}".format(interface_name)):
            if not engine:
                engine = TestToolkit.engines.dut
            return self.action(dut_engine=engine, action=ActionConsts.CLEAR, suffix=interface_name + ' link counters')

    def get_sorted_interfaces_list(self):
        with allure.step("get sorted interfaces list"):
            output_list = list(OutputParsingTool.parse_show_output_to_dict(self.show()).get_returned_value().keys())
            return sorted(output_list, key=divide_interface_name)[3:]

    def get_ipv6_address(self):
        output = OutputParsingTool.parse_show_interface_output_to_dictionary(self.show()).get_returned_value()
        assert output, "show mgmt interface output is empty"
        addresses = output['ip']['address'].keys()
        for address in addresses:
            if ":" in address and len(address) >= 32:
                return address.split("/")[0]


def divide_interface_name(string):
    reg = IbConsts.IB_INTERFACE_NAME_REGEX
    match = re.match(reg, string)
    if match:
        prefix = match.group(1)
        numeric_part = match.group(2)
        suffix = match.group(3)
        return prefix, int(numeric_part), suffix
    else:
        return "", "", ""
