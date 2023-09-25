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

TESTS_CLASS_LIST = ['AclPriorityTest', 'AclActionTest']


@pytest.mark.parametrize("test_class_name", TESTS_CLASS_LIST)
def test_acl_fields(ptfadapter, apply_vnet_configs, acl_test_pkts, test_class_name):  # noqa: F811
    for pkt in acl_test_pkts:
        pkt_description = pkt.get_description()
        if test_class_name in pkt_description:
            logger.info("Testing packet: {}".format(pkt.get_description()))
            _, vxlan_packet, expected_packet = packets.outbound_vnet_packets(pkt.dash_config_info,
                                                                             pkt.inner_extra_conf)
            testutils.send(ptfadapter,
                           pkt.dash_config_info[LOCAL_PTF_INTF],
                           vxlan_packet, 1)
            if pkt.expected_receiving:
                testutils.verify_packet(ptfadapter,
                                        expected_packet,
                                        pkt.dash_config_info[REMOTE_PTF_INTF])
            else:
                testutils.verify_no_packet(ptfadapter,
                                           expected_packet,
                                           pkt.dash_config_info[REMOTE_PTF_INTF])
            time.sleep(1)
