import pytest
import random
from tests.common.helpers.assertions import pytest_assert
from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from tests.common.utilities import wait_until


pytestmark = [
    pytest.mark.topology('any')
]

DPU_LIST = ["dpu1", "dpu2", "dpu3", "dpu4"]

SKU_SUPPORT_DPU_CTL_LIST = ["Mellanox-SN4700-O28", "ACS-SN4280"]


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
    2. Check return msg:
       When force_option is False,
       it includes 'Power Off complete' and 'Power off forced=False' for the corresponding dpu
       When force_option is True, it includes 'Power off forced=True' for the corresponding dpu

        e.g. sudo dpuctl dpu-power-off dpu1  --force
            dpu1: Power off forced=True

        e.g. sudo dpuctl dpu-power-off dpu1
            dpu1: Power off forced=False
            dpu1: Power Off complete

    3. Check the corresponding dpu npu port is down
    4. Select several dpus or all to power on, Check return msg and the correct dpu npu port is up
    5. Check return msg includes 'Power on Successful!' and the force value is equal to force_option

       e.g. sudo dpuctl dpu-power-on dpu1 --force
            dpu1: Power on forced=True
            dpu1: Power on Successful!

    6. Check the corresponding dpu npu port is up
    7. Check dpu dockers are up
    """
    duthost = duthosts[rand_one_dut_hostname]
    dpu_list_arg = ",".join(random.sample(DPU_LIST, k=random.randint(1, len(DPU_LIST))))\
        if dpu_num == "random" else f" --{dpu_num}"
    force_option_arg = " --force" if force_option else ""

    with allure.step(f"Power off {dpu_list_arg} {force_option_arg}"):
        cmd_dpu_power_off = f"sudo dpuctl dpu-power-off {dpu_list_arg} {force_option_arg}"
        power_off_res = duthost.shell(cmd_dpu_power_off)["stdout"]
        verify_power_off_return_msg(power_off_res, dpu_list_arg, force_option)
        verify_dpu_npu_port_down(duthost, dpu_npu_port_list)

    with allure.step(f"Power on {dpu_list_arg} {force_option_arg}"):
        cmd_dpu_power_on = f"sudo dpuctl dpu-power-on {dpu_list_arg} {force_option_arg}"
        power_on_res = duthost.shell(cmd_dpu_power_on)["stdout"]
        verify_power_on_return_msg(power_on_res, dpu_list_arg, force_option)
        verify_dpu_npu_port_up(duthost, dpu_npu_port_list)


def test_dpu_dpu_reset(duthosts, dpu_npu_port_list, rand_one_dut_hostname, dpu_num):
    """
    This test case is to verify the behavior of switch and dpu after dpu reset
    1. dpu reset
    2. Verify the dpu npu port is up
    """
    duthost = duthosts[rand_one_dut_hostname]
    dpu_list_str = ",".join(random.sample(DPU_LIST, k=random.randint(1, len(DPU_LIST)))) \
        if dpu_num == "random" else f" --{dpu_num}"

    with allure.step(f"Reset {dpu_list_str}"):
        cmd_dpu_reset = f"sudo dpuctl dpu-reset {dpu_list_str} "
        duthost.shell(cmd_dpu_reset)

    with allure.step(f"Check dpu has been reset"):
        verify_dpu_npu_port_down(duthost, dpu_npu_port_list)
        verify_dpu_npu_port_up(duthost, dpu_npu_port_list)


def get_test_dpu_list(dpu_list_arg):
    dpu_list = DPU_LIST if "all" in dpu_list_arg else dpu_list_arg.split(",")
    allure.step(f"get test dpu list:{dpu_list}")
    return dpu_list


def verify_power_off_return_msg(power_off_res, dpu_list_arg, force_option):
    with allure.step(f"Verify power off return msg"):
        for dpu_name in get_test_dpu_list(dpu_list_arg):
            pytest_assert(f"{dpu_name}: Power off forced={str(force_option)}",
                          f"For {dpu_name} after power off, "
                          f"not find Power off forced={str(force_option)} in return msg")
            if not force_option:
                pytest_assert(f"{dpu_name}: Power Off complete" in power_off_res,
                              f"For {dpu_name} after power off, not find Power Off complete in return msg")


def verify_power_on_return_msg(power_on_res, dpu_list_arg, force_option):
    with allure.step(f"Verify power on return msg"):
        for dpu_name in get_test_dpu_list(dpu_list_arg):
            pytest_assert(f"{dpu_name}: Power on forced={str(force_option)}",
                          f"For {dpu_name} after power off, not find Power on forced={str(force_option)} in return msg")
            pytest_assert(f"{dpu_name}: Power on Successful!" in power_on_res,
                          f"For {dpu_name} after power off, not find Power on Successful! in return msg")


def verify_dpu_npu_port_down(duthost, dpu_npu_port_list):
    with allure.step(f"Verify dpu npu port is down"):
        pytest_assert(wait_until(100, 5, 0, duthost.links_status_down, dpu_npu_port_list),
                      "dpu dpu port are not down")


def verify_dpu_npu_port_up(duthost, dpu_npu_port_list):
    with allure.step(f"Verify dpu npu port is up"):
        pytest_assert(wait_until(300, 5, 0, duthost.links_status_up, dpu_npu_port_list),
                      "dpu dpu port are not up")
