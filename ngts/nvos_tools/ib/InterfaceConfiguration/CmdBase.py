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

    def set(self, dut_engine, value, apply=True, user_input=''):
        """
        Set command
        """
        raise Exception("Not implemented")

    def unset(self, dut_engine, apply=True, user_input=''):
        """
        Unset command
        """
        raise Exception("Not implemented")

    @staticmethod
    def set_interface(engine, port_name, field_name, output_hierarchy, value, apply=True, user_input=''):
        if not value:
            logging.error("{field_name} value to set is empty".format(field_name=field_name))
            return ResultObj(False, "{field_name} value is empty", None, IssueType.TestIssue)

        logging.info("setting {field_name} to: '{value}' using {api} API".format(value=value, field_name=field_name,
                                                                                 api=TestToolkit.
                                                                                 api_str[TestToolkit.api_ib]))
        with allure.step("setting {field_name} to: '{value}'".format(value=value, field_name=field_name)):
            result_obj = SendCommandTool.execute_command(engine,
                                                         ApiObject[TestToolkit.api_ib].set_interface,
                                                         user_input, engine, port_name,
                                                         output_hierarchy, value)

        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(engine,
                                                             ApiObject[TestToolkit.api_general].apply_config,
                                                             user_input, engine)

        return result_obj

    @staticmethod
    def unset_interface(engine, port_name, field_name, output_hierarchy, apply=True, user_input=''):
        logging.info("un-setting {field_name} using {api} API".format(field_name=field_name,
                                                                      api=TestToolkit.api_str[TestToolkit.api_ib]))
        with allure.step("un-setting {field_name}".format(field_name=field_name)):
            result_obj = SendCommandTool.execute_command(engine,
                                                         ApiObject[TestToolkit.api_ib].unset_interface,
                                                         user_input, engine, port_name, output_hierarchy)

        if result_obj.result and apply:
            with allure.step("Applying configuration"):
                result_obj = SendCommandTool.execute_command(engine,
                                                             ApiObject[TestToolkit.api_general].apply_config,
                                                             user_input, engine)

        return result_obj
