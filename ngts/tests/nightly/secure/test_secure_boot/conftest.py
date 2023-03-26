import pytest
import logging

from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure

logger = logging.getLogger()
allure.logger = logger


@pytest.fixture(scope='module', autouse=True)
def restore_basic_config(secure_boot_helper, topology_obj, setup_name, platform_params):
    """
    This function will restore basic configuration
    """
    yield

    secure_boot_helper.restore_basic_config(topology_obj, setup_name, platform_params)
