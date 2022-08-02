import pytest
import logging
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from ngts.constants.constants import SflowConsts
from ngts.helpers.sflow_helper import verify_sflow_configuration, verify_sflow_sample_polling_interval, verify_flow_sample_received, \
    verify_sflow_interface_configuration


logger = logging.getLogger()
allure.logger = logger

POLLING_INTERVAL_LIST = [SflowConsts.POLLING_INTERVAL_1, SflowConsts.POLLING_INTERVAL_0, SflowConsts.POLLING_INTERVAL_2]
SAMPLE_RATE_LIST = [SflowConsts.SAMPLE_RATE_2, SflowConsts.SAMPLE_RATE_3]
COLLECTOR_WARNING_CONTENT = "Only 2 collectors can be configured, please delete one"


def test_basic_sflow_function(engines, cli_objects, interfaces, topology_obj, ha_dut_1_mac, dut_ha_1_mac, basic_sflow_configuration_for_function):
    """
    Test sflow funcrionality under reboot/fast reboot/warm reboot/config reload
    In order to make the execution time limited, use randomly reboot function
    :param engines: engines fixture
    :param cli_objects: cli_objects fixture
    :param interfaces: interfaces fixture
    :param topology_obj: topology_obj fixture
    :param ha_dut_1_mac: ha_dut_1_mac fixture
    :param dut_ha_1_mac: dut_ha_1_mac fixture
    """
    try:
        cli_obj = cli_objects.dut
        basic_sflow_configuration_for_function

        with allure.step(f"Configure sflow polling interval to {SflowConsts.POLLING_INTERVAL_1}"):
            cli_obj.sflow.config_sflow_polling_interval(SflowConsts.POLLING_INTERVAL_1)
        with allure.step(f"Configure sample rate of sflow interface {interfaces.dut_ha_1} and {interfaces.dut_ha_2} to {SflowConsts.SAMPLE_RATE_1}"):
            cli_obj.sflow.config_sflow_interface_sample_rate(interfaces.dut_ha_1, SflowConsts.SAMPLE_RATE_1)
            cli_obj.sflow.config_sflow_interface_sample_rate(interfaces.dut_ha_2, SflowConsts.SAMPLE_RATE_1)

        with allure.step("Validate sflow configuration correctness"):
            verify_sflow_configuration(cli_obj, status=SflowConsts.SFLOW_UP, polling_interval=SflowConsts.POLLING_INTERVAL_1)
            verify_sflow_configuration(cli_obj, status=SflowConsts.SFLOW_UP, agent_id=SflowConsts.AGENT_ID_DEFAULT)
            verify_sflow_configuration(cli_obj, status=SflowConsts.SFLOW_UP, collector=[SflowConsts.COLLECTOR_0])
        with allure.step("Validate sflow interface status"):
            verify_sflow_interface_configuration(cli_obj, interfaces.dut_ha_1, SflowConsts.SFLOW_UP, SflowConsts.SAMPLE_RATE_1)
            verify_sflow_interface_configuration(cli_obj, interfaces.dut_ha_2, SflowConsts.SFLOW_UP, SflowConsts.SAMPLE_RATE_1)
        with allure.step(f"Validate that counter samples could be received every {SflowConsts.POLLING_INTERVAL_1} seconds"):
            verify_sflow_sample_polling_interval(engines, topology_obj, SflowConsts.COLLECTOR_0, SflowConsts.POLLING_INTERVAL_1)
        with allure.step(f"Send traffic and validate that {SflowConsts.COLLECTOR_0} could receive flow sample with sample rate {SflowConsts.SAMPLE_RATE_1}"):
            verify_flow_sample_received(engines, interfaces, topology_obj, SflowConsts.COLLECTOR_0, SflowConsts.SAMPLE_RATE_1, ha_dut_1_mac, dut_ha_1_mac)
    except Exception as err:
        raise AssertionError(err)
