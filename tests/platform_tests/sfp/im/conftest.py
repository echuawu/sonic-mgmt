import pytest
import logging

from tests.common.platform.interface_utils import get_physical_port_indices
from tests.common.utilities import check_skip_release
from tests.platform_tests.sfp.im.helpers import IM_ENABLED, get_split_ports


@pytest.fixture(autouse=True, scope="module")
def check_image_version(duthost):
    """
    @summary: This fixture is for skip test in SONiC release
    @param: duthost: duthost fixture
    """
    check_skip_release(duthost, ["201911", "202012", "202205", "202305"])


@pytest.fixture(scope="class")
def get_ports_supporting_im(duthost, conn_graph_facts, enum_frontend_asic_index):
    """
    @summary: This method is for get DUT ports supporting IM
    @param: duthost: duthost fixture
    @param: conn_graph_facts: conn_graph_facts fixture
    @param: enum_frontend_asic_index: enum_frontend_asic_index fixture
    @return: list of IM ports supported
    """
    ports_with_im_support = []
    logging.info("Get all ports from DUT")
    dut_interfaces = list(conn_graph_facts["device_conn"][duthost.hostname].keys())

    logging.info("Create interface to physical port dict")
    physical_index_to_interface_dict = {}
    for interface in dut_interfaces:
        int_to_index = get_physical_port_indices(duthost, interface)
        index_to_interface = {v: k for k, v in int_to_index.items()}
        physical_index_to_interface_dict.update(index_to_interface)

    for port_number, port_name in physical_index_to_interface_dict.items():
        cmd = duthost.shell(f"sudo cat /sys/module/sx_core/asic0/module{int(port_number) - 1}/control")
        if int(cmd['stdout']) == IM_ENABLED:
            # Check if port is split
            split_ports = get_split_ports(duthost, int(port_number))
            if split_ports:
                ports_with_im_support += split_ports
            else:
                ports_with_im_support.append(port_name)

    return ports_with_im_support
