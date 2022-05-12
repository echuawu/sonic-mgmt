import logging
import allure
from .nvos_consts import NvosConsts, InternalNvosConsts, ApiObject
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
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
    def set_interface(engine, port_name, field_name, output_hierarchy, value, apply=True):
        if not value:
            logging.error("{field_name} value to set is empty".format(field_name=field_name))
            return ResultObj(False, "{field_name} value is empty", None, IssueType.TestIssue)

        logging.info("setting '{field_name}' of '{port_name}' to: '{value}' using {api}".format(
            value=value, field_name=field_name, api=TestToolkit.api_str[TestToolkit.api_ib], port_name=port_name))
        with allure.step("setting '{field_name}' of '{port_name}' to: '{value}'".format(value=value,
                                                                                        field_name=field_name,
                                                                                        port_name=port_name)):
            result_obj = SendCommandTool.execute_command(ApiObject[TestToolkit.api_ib].set_interface,
                                                         engine, port_name,
                                                         output_hierarchy, value)

        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(ApiObject[TestToolkit.api_general].apply_config,
                                                             engine)

        return result_obj

    @staticmethod
    def unset_interface(engine, port_name, field_name, output_hierarchy, apply=True):
        logging.info("un-setting '{field_name}' of '{port_name}' using {api}".format(
            field_name=field_name, api=TestToolkit.api_str[TestToolkit.api_ib], port_name=port_name))
        with allure.step("un-setting '{field_name}' for '{port_name}'".format(field_name=field_name,
                                                                              port_name=port_name)):
            result_obj = SendCommandTool.execute_command(ApiObject[TestToolkit.api_ib].unset_interface,
                                                         engine, port_name, output_hierarchy)

        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(ApiObject[TestToolkit.api_general].apply_config,
                                                             engine)

        return result_obj
