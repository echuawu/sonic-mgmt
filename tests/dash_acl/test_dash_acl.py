import time
import logging
import pytest
import ptf.testutils as testutils

from constants import *  # noqa: F403
import packets
from dash_acl import acl_test_conf  # noqa: F401

logger = logging.getLogger(__name__)

pytestmark = [
    pytest.mark.topology('dpu')
]

TESTS_CLASS_LIST = ['AclPriorityTest', 'AclActionTest',
                    'AclProtocolTest', 'AclAddressTest',
                    'AclPortTest', 'AclTagTest', 'AclMultiTagTest',
                    'AclTagOrderTest', 'AclMultiTagOrderTest',
                    'AclTagUpdateIpTest', 'AclTagRemoveIpTest',
                    'AclTagNegativeTest', 'AclTagScaleTest']


@pytest.mark.parametrize("test_class_name", TESTS_CLASS_LIST)
def test_acl_fields(ptfadapter, apply_vnet_configs, acl_test_conf, test_class_name):  # noqa: F811

    test_obj = get_configured_test_class(test_class_name, acl_test_conf)

    if not test_obj:
        pytest.skip("Test {} was not configured".format(test_class_name))

    if test_obj.config_only:
        return

    for pkt in test_obj.test_pkts:
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


def get_configured_test_class(class_name, defined_classes):
    test_class = None
    for defined_class in defined_classes:
        if class_name == defined_class.__class__.__name__:
            test_class = defined_class
    return test_class
