import logging
import allure
from .nvos_consts import NvosConsts, InternalNvosConsts, ApiObject
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit

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
            raise Exception("{field_name} value is empty")
        logging.info("setting {field_name} to: '{value}' using {api} API".format(value=value, field_name=field_name,
                                                                                 api=TestToolkit.
                                                                                 api_str[TestToolkit.api_ib]))
        with allure.step("setting {field_name} to: '{value}'".format(value=value, field_name=field_name)):
            ret_str = ApiObject[TestToolkit.api_ib].set_interface(engine=engine, port_name=port_name,
                                                                  interface=output_hierarchy, value=value)

        if apply:
            with allure.step("Applying configuration"):
                ApiObject[TestToolkit.api_general].apply_config(engine)

        return ret_str

    @staticmethod
    def unset_interface(engine, port_name, field_name, output_hierarchy, apply=True):
        logging.info("un-setting {field_name} using {api} API".format(field_name=field_name,
                                                                      api=TestToolkit.api_str[TestToolkit.api_ib]))
        with allure.step("un-setting {field_name}".format(field_name=field_name)):
            ret_str = ApiObject[TestToolkit.api_ib].unset_interface(engine, port_name, output_hierarchy)

        if apply:
            with allure.step("Applying configuration"):
                ApiObject[TestToolkit.api_general].apply_config(engine)

        return ret_str
