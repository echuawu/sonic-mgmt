from ngts.tools.test_utils import allure_utils as allure
import logging
import pytest
from ngts.nvos_constants.constants_nvos import NvosConst, DiskConsts
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.tools.test_utils.nvos_general_utils import check_partitions_capacity

logger = logging.getLogger()


@pytest.mark.init_flow
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
@pytest.mark.nvos_ci
def test_system_services(engines, devices):
    """
    Verifying the NVOS system services are in active state
    Run sudo systemctl status and validate systemctl state is active and no jobs or failures"
    Run sudo systemctl is-active hw-management and validate hw_management is active"
    :return: None, raise error in case one or more services are inactive
    """
    with allure.step("Validate services are active"):
        res_obj = devices.dut.verify_services(engines.dut)
        assert res_obj.result, res_obj.info


@pytest.mark.init_flow
def test_partitions_capacity():
    check_partitions_capacity(partition_name=DiskConsts.DEFAULT_PARTITION_NAME,
                              allowed_limit=DiskConsts.PARTITION_CAPACITY_LIMIT)


@pytest.mark.init_flow
@pytest.mark.simx
@pytest.mark.nvos_chipsim_ci
@pytest.mark.nvos_ci
def test_system_dockers(engines, devices):
    """
    Verifying the NVOS system dockers are up
    Run "docker ps" and validate the expected dockers appears
    :return: None, raise error in case one or more dockers are down
    """
    with allure.step("Validate docker are up"):
        res_obj = devices.dut.verify_dockers(engines.dut)
        assert res_obj.result, res_obj.info


@pytest.mark.init_flow
@pytest.mark.nvos_ci
def test_existence_of_tables_in_databases(engines, devices):
    """
    Verifying the NVOS Databases created the correct tables in redis
    :return: None, raise error in case one or more tables are missed
    """
    with allure.step("Validate no missing database default tables"):
        res_obj = devices.dut.verify_databases(engines.dut)
        assert res_obj.result, res_obj.info


@pytest.mark.init_flow
@pytest.mark.nvos_ci
def test_ports_are_up(engines, devices):
    """
    Verifying the NVOS ports are up
    :return: None, raise error in case one or more ports are down
    """
    with allure.step("Validate all ports status is up"):
        res_obj = devices.dut.verify_ib_ports_state(engines.dut, NvosConst.PORT_STATUS_UP)
        assert res_obj.result, res_obj.info


@pytest.mark.init_flow
@pytest.mark.nvos_ci
def test_check_firmware(engines):
    """
    Verify installed firmware is equal to actual firmware
    """
    with allure.step("Verify installed firmware is equal to actual firmware"):
        system = System()
        asic_output = OutputParsingTool.parse_json_str_to_dictionary(system.firmware.asic.show()).get_returned_value()
        installed_fw = asic_output['installed-firmware']
        actual_fw = asic_output['actual-firmware']
        assert installed_fw == actual_fw, f"installed firmware is NOT equal to actual firmware. \n" \
                                          "installed firmware: {installed_fw}, actual firmware: {actual_fw}"