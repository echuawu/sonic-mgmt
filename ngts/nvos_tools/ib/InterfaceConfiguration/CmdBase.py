import logging
import allure
from .nvos_consts import NvosConsts, InternalNvosConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.constants.constants_nvos import ApiType
from ngts.nvos_tools.infra.ResultObj import ResultObj, IssueType

logger = logging.getLogger()


class CmdBase:
    wait_for_required_port_state = False
    wait_for_state = NvosConsts.LINK_STATE_UP
    timeout = InternalNvosConsts.DEFAULT_TIMEOUT

    def set(self, dut_engine, value, apply=True):
        """
        Set command
        """
        raise Exception("Not implemented")

    def unset(self, dut_engine, apply=True):
        """
        Unset command
        """
        raise Exception("Not implemented")

    @staticmethod
    def set_interface(engine, port_obj, field_name, output_hierarchy, value, apply=True, ask_for_confirmation=False):
        logging.info("setting '{field_name}' of '{port_name}' to: '{value}' using {api}".format(
            value=value, field_name=field_name, api=TestToolkit.tested_api, port_name=port_obj.name))
        with allure.step("setting '{field_name}' of '{port_name}' to: '{value}'".format(value=value,
                                                                                        field_name=field_name,
                                                                                        port_name=port_obj.name)):
            result_obj = SendCommandTool.execute_command(port_obj.api_obj[TestToolkit.tested_api].set_interface,
                                                         engine, port_obj.name,
                                                         output_hierarchy, field_name, value)

        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                                             apply_config, engine, ask_for_confirmation)

        return result_obj

    @staticmethod
    def unset_interface(engine, port_obj, field_name, output_hierarchy, apply=True, ask_for_confirmation=False):
        logging.info("un-setting '{field_name}' of '{port_name}' using {api}".format(
            field_name=field_name, api=TestToolkit.tested_api, port_name=port_obj.name))
        with allure.step("un-setting '{field_name}' for '{port_name}'".format(field_name=field_name,
                                                                              port_name=port_obj.name)):
            result_obj = SendCommandTool.execute_command(port_obj.api_obj[TestToolkit.tested_api].unset_interface,
                                                         engine, port_obj.name, output_hierarchy)

        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                                             apply_config, engine, ask_for_confirmation)

        return result_obj
