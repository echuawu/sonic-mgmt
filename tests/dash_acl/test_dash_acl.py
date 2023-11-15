import time
import logging
import pytest
import ptf.testutils as testutils

from constants import *  # noqa: F403
import packets
from dash_acl import acl_test_pkts  # noqa: F401

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.topology('dpu')
]


def run_test(ptfadapter, acl_test_pkts, skip_dataplane_checking):
    if skip_dataplane_checking:
        return
    failures = {}
    for pkt in acl_test_pkts:
        logger.info("Testing packet: {}, {}".format(pkt.get_description(), pkt.dash_config_info))
        _, vxlan_packet, expected_packet = packets.outbound_vnet_packets(pkt.dash_config_info,
                                                                         pkt.inner_extra_conf)
        logger.info("Sending packet: {}".format(vxlan_packet.show))
        testutils.send(ptfadapter,
                       pkt.dash_config_info[LOCAL_PTF_INTF],
                       vxlan_packet, 1)
        try:
            if pkt.expected_receiving:
                testutils.verify_packets_any(ptfadapter,
                                             expected_packet,
                                             ports=pkt.dash_config_info[REMOTE_PTF_INTF])
                logger.info("The packet is received as expected.")
            else:
                testutils.verify_no_packet_any(ptfadapter,
                                               expected_packet,
                                               ports=pkt.dash_config_info[REMOTE_PTF_INTF])
                logger.info("The packet is not received as expected.")
        except Exception as e:
            failures[pkt.get_description()] = e
            logger.error("The test for packet {} failed, added to the failure list.".format(pkt.get_description()))
        time.sleep(1)

    if failures:
        logger.error("Some test cases failed:")
        result = ''
        for failure in failures.items():
            result += "Test case: {} failed for {}\n".format(failure[0], failure[1])
        pytest.fail(result)


def test_acl_fields(ptfadapter, apply_vnet_configs, acl_test_pkts, skip_dataplane_checking,
                    asic_db_checker):  # noqa: F811
    run_test(ptfadapter, acl_test_pkts, skip_dataplane_checking)


def test_acl_tag(ptfadapter, apply_vnet_configs, acl_test_pkts, skip_dataplane_checking, asic_db_checker):  # noqa: F811
    run_test(ptfadapter, acl_test_pkts, skip_dataplane_checking)


def test_acl_multi_tag(ptfadapter, apply_vnet_configs, acl_test_pkts, skip_dataplane_checking,
                       asic_db_checker):  # noqa: F811
    run_test(ptfadapter, acl_test_pkts, skip_dataplane_checking)


def test_acl_tag_order(ptfadapter, apply_vnet_configs, acl_test_pkts, skip_dataplane_checking,
                       asic_db_checker):  # noqa: F811
    run_test(ptfadapter, acl_test_pkts, skip_dataplane_checking)


def test_acl_multi_tag_order(ptfadapter, apply_vnet_configs, acl_test_pkts, skip_dataplane_checking,
                       asic_db_checker):  # noqa: F811
    run_test(ptfadapter, acl_test_pkts, skip_dataplane_checking)


def test_acl_tag_update_ip(ptfadapter, apply_vnet_configs, acl_test_pkts, skip_dataplane_checking,
                       asic_db_checker):  # noqa: F811
    run_test(ptfadapter, acl_test_pkts, skip_dataplane_checking)


def test_acl_tag_remove_ip(ptfadapter, apply_vnet_configs, acl_test_pkts, skip_dataplane_checking,
                       asic_db_checker):  # noqa: F811
    run_test(ptfadapter, acl_test_pkts, skip_dataplane_checking)


def test_acl_tag_scale(ptfadapter, apply_vnet_configs, acl_test_pkts, skip_dataplane_checking,
                       asic_db_checker):  # noqa: F811
    run_test(ptfadapter, acl_test_pkts, skip_dataplane_checking)
