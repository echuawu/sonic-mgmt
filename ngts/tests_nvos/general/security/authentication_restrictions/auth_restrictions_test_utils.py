import sys
import time
from retry import retry
from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.tests_nvos.general.security.authentication_restrictions.constants import RestrictionsConsts
from ngts.tools.test_utils import allure_utils as allure
import logging
import pexpect


def configure_resource(engines, resource_obj: BaseComponent, configuration={}):
    """
    @summary: Configure fields within the given resource
    @param engines: engines object
    @param resource_obj: A resource object (from class inherits from BaseComponent)
    @param configuration: The desired configuration for the resource.
        * Given as dictionary of: { field: value } format.
    """
    with allure.step(f'Configure resource: {resource_obj.get_resource_path()}'):
        for field, val in configuration.items():
            with allure.step(f'Set field "{field}" with value "{val}"'):
                resource_obj.set(field, val).verify_result()

        with allure.step('Apply configuration'):
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut,
                                            True).verify_result()
