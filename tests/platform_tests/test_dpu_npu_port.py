import logging
import pytest
from tests.common.helpers.assertions import pytest_assert

pytestmark = [
    pytest.mark.topology('any')
]


def test_dpu_npu_port(duthosts, enum_rand_one_per_hwsku_frontend_hostname, dpu_npu_port_list):
    """
    This test case is to verify when the role of port is Dpc, the type of port is  DPU-NPU Data Port
    """
    duthost = duthosts[enum_rand_one_per_hwsku_frontend_hostname]
    intf_status = duthost.show_interface(command="status")["ansible_facts"]['int_status']
    dpu_npu_port_type = 'DPU-NPU Data Port'

    logging.info("Check interface type for dpu npu port")
    if not dpu_npu_port_list[duthost.hostname]:
        pytest.skip("Skip the test due to no dpu npu ports")

    for intf in dpu_npu_port_list[duthost.hostname]:
        pytest_assert(
            intf in intf_status, f"interface {intf} is not in the output of show interface status: {intf_status}")
        pytest_assert(
            intf_status[intf].get('type') == dpu_npu_port_type,
            f"Interface {intf}: The actual type is is {intf_status[intf].get('type')}, "
            f"the expected type is {dpu_npu_port_type}")
