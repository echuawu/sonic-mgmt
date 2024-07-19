import pytest
import logging
import random
from tests.common.helpers.assertions import pytest_assert
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from tests.common.utilities import wait_until

logger = logging.getLogger()

pytestmark = [
    pytest.mark.topology('any')
]

DPU_LIST = ["dpu1", "dpu2", "dpu3", "dpu4"]
SKU_SUPPORT_DPU_CTL_LIST = ["Mellanox-SN4280-O28"]


@pytest.fixture(scope="module", autouse=True)
def skip_sku_not_support_dpu_ctl(duthosts, rand_one_dut_hostname):
    duthost = duthosts[rand_one_dut_hostname]
    dut_hwsku = duthost.facts["hwsku"]

    if dut_hwsku not in SKU_SUPPORT_DPU_CTL_LIST:
        pytest.skip(f"Skip the test due to {dut_hwsku} not support dpu ctl")


@pytest.fixture(scope="function", params=["random", "all"])
def dpu_num(request):
    return request.param


@pytest.fixture(scope="function", params=[False, True])
def force_option(request):
    return request.param


def test_dpu_power_off_and_on(duthosts, dpu_npu_port_list, rand_one_dut_hostname, dpu_num, force_option):
    """
    This test case is to verify dpu power off and on
    1. Select several dpus or all to power off
    2. Check dpus are down
    3. Check the corresponding dpu npu port is down
    4. Select several dpus or all to power on
    5. Check dpus are up
    6. Check the corresponding dpu npu port is up
    7. Check dpu dockers are up
    """
    duthost = duthosts[rand_one_dut_hostname]
    test_dpu_list, test_dpu_npu_port_list, dpu_list_arg = get_test_dpu_and_port(
        dpu_num, dpu_npu_port_list, rand_one_dut_hostname)

    force_option_arg = " --force" if force_option else ""

    with allure.step(f"Power off {dpu_list_arg} {force_option_arg}"):
        cmd_dpu_power_off = f"sudo dpuctl dpu-power-off {dpu_list_arg} {force_option_arg}"
        duthost.shell(cmd_dpu_power_off)["stdout"]
        with allure.step(f"verify {test_dpu_list} are down"):
            verify_dpu_status(duthost, test_dpu_list, dpu_ready="False", dpu_shutdown_ready="True")
        verify_dpu_npu_port_down(duthost, test_dpu_npu_port_list)

    with allure.step(f"Power on {dpu_list_arg} {force_option_arg}"):
        cmd_dpu_power_on = f"sudo dpuctl dpu-power-on {dpu_list_arg} {force_option_arg}"
        duthost.shell(cmd_dpu_power_on)["stdout"]
        with allure.step(f"verify {test_dpu_list} are up"):
            verify_dpu_status(duthost, test_dpu_list, dpu_ready="True", dpu_shutdown_ready="False")

        verify_dpu_npu_port_up(duthost, test_dpu_npu_port_list)


def test_dpu_dpu_reset(duthosts, dpu_npu_port_list, rand_one_dut_hostname, dpu_num):
    """
    This test case is to verify the behavior of switch and dpu after dpu reset
    1. dpu reset
    2. Check dpus are up
    3. Check the dpu npu port is up
    """
    duthost = duthosts[rand_one_dut_hostname]
    test_dpu_list, test_dpu_npu_port_list, dpu_list_arg = get_test_dpu_and_port(
        dpu_num, dpu_npu_port_list, rand_one_dut_hostname)

    with allure.step(f"Reset {dpu_list_arg}"):
        cmd_dpu_reset = f"sudo dpuctl dpu-reset {dpu_list_arg} "
        duthost.shell(cmd_dpu_reset, module_ignore_errors=True, module_async=True)

    with allure.step(f"Check dpu has been reset"):
        with allure.step(f"Check {test_dpu_list} are down"):
            verify_dpu_status(duthost, test_dpu_list, dpu_ready="False", dpu_shutdown_ready="False")

        with allure.step(f"Check {test_dpu_list} are up"):
            verify_dpu_status(duthost, test_dpu_list, dpu_ready="True", dpu_shutdown_ready="False")
        verify_dpu_npu_port_up(duthost, test_dpu_npu_port_list)


def get_test_dpu_list(dpu_list_arg):
    dpu_list = DPU_LIST if "all" in dpu_list_arg else dpu_list_arg.split(",")
    allure.step(f"get test dpu list:{dpu_list}")
    return dpu_list


def verify_dpu_npu_port_down(duthost, dpu_npu_port_list):
    with allure.step(f"Verify dpu npu port is down"):
        pytest_assert(wait_until(100, 5, 0, duthost.links_status_down, dpu_npu_port_list),
                      "dpu dpu port are not down")


def verify_dpu_npu_port_up(duthost, dpu_npu_port_list):
    with allure.step(f"Verify dpu npu port is up"):
        pytest_assert(wait_until(300, 5, 0, duthost.links_status_up, dpu_npu_port_list),
                      "dpu dpu port are not up")


def verify_dpu_status(duthost, dpu_list, dpu_ready, dpu_shutdown_ready):
    def _verify_dpu_status():
        dpu_status = get_dpu_status(duthost)
        for one_dpu_status in dpu_status:
            if one_dpu_status['dpu'] in dpu_list:
                assert one_dpu_status['dpu ready'] == dpu_ready and \
                       one_dpu_status['dpu shutdown ready'] == dpu_shutdown_ready, \
                    f" Expected value: dpu ready {dpu_ready},  dpu shutdown ready {dpu_shutdown_ready}." \
                    f" Actual value: dpu ready {one_dpu_status['dpu ready']}, " \
                    f"dpu shutdown ready {one_dpu_status['dpu shutdown ready']}"
        logger.info("tested dpu status are ok")
        return True

    with allure.step(f"Verify dpu status"):
        pytest_assert(wait_until(200, 5, 0, _verify_dpu_status),
                      f"dpu ready is not {dpu_ready}, dpu shutdown ready is not {dpu_shutdown_ready}")


def get_dpu_status(duthost):
    cmd_get_dpu_status = "sudo dpuctl dpu-status"
    return duthost.show_and_parse(cmd_get_dpu_status)


def get_test_dpu_and_port(dpu_num, dpu_npu_port_list, rand_one_dut_hostname):
    test_dpu_list = random.sample(DPU_LIST, k=random.randint(1, len(DPU_LIST))) if dpu_num == "random" else DPU_LIST
    dpu_list_arg = ",".join(test_dpu_list) if dpu_num == "random" else f" --{dpu_num}"
    temp_dpu_npu_port_list = dpu_npu_port_list[rand_one_dut_hostname]
    temp_dpu_npu_port_list.sort(key=lambda port: int(port.replace("Ethernet", "")))
    test_dpu_npu_port_list = [temp_dpu_npu_port_list[int(dpu.replace('dpu', "")) - 1] for dpu in test_dpu_list]
    logger.info(f"test dpu info:\n test dpu list:{test_dpu_list}"
                f"\ntest dpu port list:{test_dpu_npu_port_list} "
                f"\ndpu list arg:{dpu_list_arg} ")
    return test_dpu_list, test_dpu_npu_port_list, dpu_list_arg
