import pytest
import copy
import abc
import ipaddress
import logging
import random

from constants import *  # noqa: F403
from dash_utils import render_template
from gnmi_utils import apply_gnmi_file

logger = logging.getLogger(__name__)

ACL_GROUP_TEMPLATE = "dash_acl_group"
ACL_RULE_TEMPLATE = "dash_acl_rule"
ACL_TAG_TEMPLATE = "dash_acl_tag"
BIND_ACL_IN = "dash_bind_acl_in"
BIND_ACL_OUT = "dash_bind_acl_out"
DEFAULT_ACL_GROUP = "default_acl_group"
DEFAULT_ACL_STAGE = 1
SRC_IP_RANGE = ['24.0.0.0', '24.255.255.255']
BASE_SRC_SCALE_IP = '8.0.0.0'
SCALE_TAGS = 4096
SCALE_TAG_IPS = 24576


def apply_acl_config(duthost, ptfhost, template_name, acl_config_info, op):
    template_file = "{}.j2".format(template_name)
    dest_path = "/tmp/{}.json".format(template_name)
    config_json = render_template(template_file, acl_config_info, op=op)
    # apply_swssconfig_file(duthost, dest_path)
    apply_gnmi_file(duthost, ptfhost, config_json=config_json)


class AclGroup(object):
    def __init__(self, duthost, ptfhost, acl_group, eni, ip_version="ipv4", create_group=True):
        self.duthost = duthost
        self.ptfhost = ptfhost
        self.acl_group = acl_group
        self.eni = eni
        self.ip_version = ip_version
        self.group_conf = {
            ACL_GROUP: self.acl_group,
            IP_VERSION: self.ip_version
        }
        if create_group:
            apply_acl_config(self.duthost, self.ptfhost, ACL_GROUP_TEMPLATE, self.group_conf, op="SET")

    def __del__(self):
        apply_acl_config(self.duthost, self.ptfhost, ACL_GROUP_TEMPLATE, self.group_conf, op="DEL")

    def bind(self, stage):
        self.stage = stage
        self.bind_conf = {
            ENI: self.eni,
            ACL_GROUP: self.acl_group,
            ACL_STAGE: self.stage,
        }
        apply_acl_config(self.duthost, self.ptfhost, BIND_ACL_OUT, self.bind_conf, op="SET")
        apply_acl_config(self.duthost, self.ptfhost, BIND_ACL_IN, self.bind_conf, op="SET")

    def unbind(self):
        apply_acl_config(self.duthost, self.ptfhost, BIND_ACL_OUT, self.bind_conf, op="DEL")
        apply_acl_config(self.duthost, self.ptfhost, BIND_ACL_IN, self.bind_conf, op="DEL")


class AclTag(object):
    def __init__(self, duthost, ptfhost, acl_tag, acl_prefix_list, ip_version="ipv4"):
        self.duthost = duthost
        self.ptfhost = ptfhost
        self.tag_conf = {
            ACL_TAG: acl_tag,
            IP_VERSION: ip_version,
            ACL_PREFIX_LIST: acl_prefix_list
        }
        apply_acl_config(self.duthost, self.ptfhost, ACL_TAG_TEMPLATE, self.tag_conf, op="SET")

    def __del__(self):
        apply_acl_config(self.duthost, self.ptfhost, ACL_TAG_TEMPLATE, self.tag_conf, op="DEL")


class AclTestPacket(object):
    def __init__(self,
                 dash_config_info,
                 inner_extra_conf={},
                 expected_receiving=True,
                 description=""):
        self.dash_config_info = dash_config_info
        self.inner_extra_conf = inner_extra_conf
        self.expected_receiving = expected_receiving
        self.description = description + "_" + str(self.inner_extra_conf)

    def get_description(self):
        return self.description


class AclTestCase(object):
    def __init__(self, duthost, ptfhost, dash_config_info):
        __metaclass__ = abc.ABCMeta  # noqa: F841
        self.duthost = duthost
        self.ptfhost = ptfhost
        self.dash_config_info = dash_config_info
        self.test_pkts = []
        self.config_only = False

    @abc.abstractmethod
    def config(self):
        pass

    @abc.abstractmethod
    def teardown(self):
        pass

    def get_random_ip(self):
        """
        Generate a random IP from ip range
        """
        length = int(ipaddress.ip_address(SRC_IP_RANGE[1])) - int(ipaddress.ip_address(SRC_IP_RANGE[0]))
        return str(ipaddress.ip_address(SRC_IP_RANGE[0]) + random.randint(0, length))


class DefaultAclGroupCreateTest(AclTestCase):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(DefaultAclGroupCreateTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.group = AclGroup(self.duthost, self.ptfhost, self.acl_group, self.dash_config_info[ENI])

    def teardown(self):
        del self.group


class DefaultAclGroupBindTest(AclTestCase):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(DefaultAclGroupBindTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.group = AclGroup(self.duthost, self.ptfhost, self.acl_group,
                              self.dash_config_info[ENI], create_group=False)

    def config(self):
        self.group.bind(DEFAULT_ACL_STAGE)

    def teardown(self):
        self.group.unbind()


class AclRuleTest(AclTestCase):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclRuleTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.rule_confs = []
        self.acl_tag = None

    def add_rule(self, rule_conf):
        rule_conf[ACL_RULE] = self.__class__.__name__ + "_" + rule_conf[ACL_RULE]
        apply_acl_config(self.duthost, self.ptfhost, ACL_RULE_TEMPLATE, rule_conf, op="SET")
        self.rule_confs.append(rule_conf)

    def add_test_pkt(self, test_pkt):
        test_pkt.description = self.__class__.__name__ + "_" + str(len(self.test_pkts) + 1) + "_" + test_pkt.description
        self.test_pkts.append(test_pkt)

    def teardown(self):
        for rule_conf in self.rule_confs:
            apply_acl_config(self.duthost, self.ptfhost, ACL_RULE_TEMPLATE, rule_conf, op="DEL")
        self.rule_confs = []


class DefaultAclRule(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(DefaultAclRule, self).__init__(duthost, ptfhost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_default",
            ACL_PRIORITY: 100,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
        })


class AclPriorityTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclPriorityTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip = self.get_random_ip()
        self.src_ip_prefix = self.src_ip + "/32"

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "deny_2",
            ACL_PRIORITY: 2,
            ACL_ACTION: "deny",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "1"
        })
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_10",
            ACL_PRIORITY: 10,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "1"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 1},
                                        expected_receiving=False))
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_4",
            ACL_PRIORITY: 4,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "2"
        })
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "deny_30",
            ACL_PRIORITY: 30,
            ACL_ACTION: "deny",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "2"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 2},
                                        expected_receiving=True))


class AclActionTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclActionTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip = self.get_random_ip()
        self.src_ip_prefix = self.src_ip + "/32"

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_20",
            # TODO. This priority should be lower than rule2's (2)
            ACL_PRIORITY: 20,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "false",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "3"
        })
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "deny_3",
            ACL_PRIORITY: 3,
            ACL_ACTION: "deny",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "3"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 3},
                                        expected_receiving=False))


class AclProtocolTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclProtocolTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip = self.get_random_ip()
        self.src_ip_prefix = self.src_ip + "/32"

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_1",
            ACL_PRIORITY: 1,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17,18",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "4"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"proto": 17, "udp_sport": 4},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"proto": 18, "udp_sport": 4},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"proto": 19, "udp_sport": 4},
                                        expected_receiving=False))


class AclAddressTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclAddressTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip3 = self.get_random_ip()
        self.src_ip4, self.src_ip5 = self.get_sequential_ips()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"
        self.src_ip_prefix4_5 = self.src_ip4 + "/30"
        self.acl_group = DEFAULT_ACL_GROUP

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_5",
            ACL_PRIORITY: 5,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: ",".join([self.src_ip_prefix1, self.src_ip_prefix2]),
            ACL_SRC_PORT: "6"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip1
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 6},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip2
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 6},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip3
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 6},
                                        expected_receiving=False))
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_6",
            ACL_PRIORITY: 6,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix4_5,
            ACL_SRC_PORT: "6"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip4
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 6},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip5
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 6},
                                        expected_receiving=True))

    def get_sequential_ips(self):
        """
        Get the sequential IPs like 1.1.1.0, 1.1.1.1
        :return:
        """
        base_ip = self.get_random_ip()
        ip_zero_ends = base_ip[:base_ip.rfind('.') + 1] + '0'
        ip_one_ends = base_ip[:base_ip.rfind('.') + 1] + '1'
        return ip_zero_ends, ip_one_ends


class AclPortTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclPortTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip = self.get_random_ip()
        self.src_ip_prefix = self.src_ip + "/32"

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_7",
            ACL_PRIORITY: 7,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "7-10,12"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 7},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 10},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 12},
                                        expected_receiving=True))


class AclTagTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclTagTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.ptfhost = ptfhost
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"

    def config(self):
        self.acl_tag = AclTag(self.duthost, self.ptfhost, "AclTag",
                              [",".join([self.src_ip_prefix1, self.src_ip_prefix2])])
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_tag",
            ACL_PRIORITY: 1,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_TAG: "AclTag1",
            ACL_SRC_PORT: "13"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip1
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 13},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip2
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 13},
                                        expected_receiving=True))

    def teardown(self):
        super(AclTagTest, self).teardown()
        del self.acl_tag


class AclMultiTagTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclMultiTagTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.ptfhost = ptfhost
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"

    def config(self):
        self.acl_tag = AclTag(self.duthost, self.ptfhost, "AclMultiTag",
                              [self.src_ip_prefix1, self.src_ip_prefix2])
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_multi_tag",
            ACL_PRIORITY: 1,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_TAG: "AclMultiTag1,AclMultiTag2",
            ACL_SRC_PORT: "15"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip1
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 15},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip2
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 15},
                                        expected_receiving=True))

    def teardown(self):
        super(AclMultiTagTest, self).teardown()
        del self.acl_tag


class AclTagOrderTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclTagOrderTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.ptfhost = ptfhost
        self.acl_group = DEFAULT_ACL_GROUP
        self.acl_tag = None
        self.src_ip = self.get_random_ip()
        self.src_ip_prefix = self.src_ip + "/32"

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_tag_order",
            ACL_PRIORITY: 1,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_TAG: "AclTagOrder1",
            ACL_SRC_PORT: "17"
        })
        self.acl_tag = AclTag(self.duthost, self.ptfhost, "AclTagOrder", [self.src_ip_prefix])
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 17},
                                        expected_receiving=True))

    def teardown(self):
        del self.acl_tag
        super(AclTagOrderTest, self).teardown()


class AclMultiTagOrderTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclMultiTagOrderTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.ptfhost = ptfhost
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_multi_tag_order",
            ACL_PRIORITY: 1,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_TAG: "AclMultiTagOrder1,AclMultiTagOrder2",
            ACL_SRC_PORT: "18"
        })
        self.acl_tag = AclTag(self.duthost, self.ptfhost, "AclMultiTagOrder", [self.src_ip_prefix1, self.src_ip_prefix2])
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip1
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 18},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip2
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 18},
                                        expected_receiving=True))

    def teardown(self):
        del self.acl_tag
        super(AclMultiTagOrderTest, self).teardown()


class AclTagUpdateIpTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclTagUpdateIpTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.ptfhost = ptfhost
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"

    def config(self):
        self.acl_tag1 = AclTag(self.duthost, self.ptfhost, "AclTagUpdateIp", [self.src_ip_prefix1])
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_update_ip_tag",
            ACL_PRIORITY: 1,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_TAG: "AclTagUpdateIp1",
            ACL_SRC_PORT: "19"
        })
        self.acl_tag2 = AclTag(self.duthost, self.ptfhost, "AclTagUpdateIp", [self.src_ip_prefix2])
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip1
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 19},
                                        expected_receiving=False))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip2
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 19},
                                        expected_receiving=True))

    def teardown(self):
        super(AclTagUpdateIpTest, self).teardown()
        del self.acl_tag1
        del self.acl_tag2


class AclTagRemoveIpTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclTagRemoveIpTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.ptfhost = ptfhost
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"

    def config(self):
        self.acl_tag1 = AclTag(self.duthost, self.ptfhost, "AclTagRemoveIp",
                              [",".join([self.src_ip_prefix1, self.src_ip_prefix2])])
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_remove_ip_tag",
            ACL_PRIORITY: 1,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_TAG: "AclTagRemoveIp1",
            ACL_SRC_PORT: "20"
        })
        self.acl_tag2 = AclTag(self.duthost, self.ptfhost, "AclTagRemoveIp", [self.src_ip_prefix1])
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip1
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 20},
                                        expected_receiving=True))
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip2
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 20},
                                        expected_receiving=False))

    def teardown(self):
        super(AclTagRemoveIpTest, self).teardown()
        del self.acl_tag1
        del self.acl_tag2


class AclTagScaleTest(AclRuleTest):
    def __init__(self, duthost, ptfhost, dash_config_info):
        super(AclTagScaleTest, self).__init__(duthost, ptfhost, dash_config_info)
        self.ptfhost = ptfhost
        self.acl_group = DEFAULT_ACL_GROUP
        self.ip_list = self.random_scale_ip_list()
        self.src_ip = self.ip_list[0]
        self.src_ip_prefix_list = self.get_scale_prefixes_list()
        self.tag_names_list = ",".join(["AclTagScale{}".format(tag_num) for tag_num in range(1, SCALE_TAGS+1)])

    def config(self):
        self.acl_tag = AclTag(self.duthost, self.ptfhost, "AclTagScale", self.src_ip_prefix_list)
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_scale_tag",
            ACL_PRIORITY: 1,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_TAG: self.tag_names_list,
            ACL_SRC_PORT: "21"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 21},
                                        expected_receiving=True))

    def teardown(self):
        super(AclTagScaleTest, self).teardown()
        del self.acl_tag

    @staticmethod
    def random_scale_ip_list(ip_type='ipv4'):
        ip_list = []
        if ip_type == 'ipv4':
            address_type = ipaddress.IPv4Address
        else:
            address_type = ipaddress.IPv6Address
        first_ip = address_type(BASE_SRC_SCALE_IP)
        last_ip = first_ip + (SCALE_TAGS * SCALE_TAG_IPS)
        summarized_range = ipaddress.summarize_address_range(first_ip, last_ip)
        for subnet in summarized_range:
            for ip_address in subnet:
                ip_list.append(str(ip_address))
        random.shuffle(ip_list)
        return ip_list

    def get_scale_prefixes_list(self):
        prefixes_list = []
        begin_index = 0
        for _ in range(SCALE_TAGS):
            end_index = begin_index + SCALE_TAG_IPS
            ip_list = self.ip_list[begin_index:end_index]
            prefixes_list.append("/32,".join(ip_list) + "/32")
            begin_index += SCALE_TAG_IPS
        return prefixes_list


@pytest.fixture(scope="function")
def acl_test_conf(request, duthost, ptfhost, dash_config_info):
    # Feature limitation: the group  can't be changed
    # after ENI configuration(dash_basic_config.j2).
    # All tests rules should be configured before.
    testcases = []
    pytest_testcase_name = request.node.name.split('[')[0]
    testcases.append(DefaultAclGroupCreateTest(duthost, ptfhost, dash_config_info))
    if pytest_testcase_name == "test_acl_fields":
        testcases.append(AclPriorityTest(duthost, ptfhost, dash_config_info))
        testcases.append(AclActionTest(duthost, ptfhost, dash_config_info))
        testcases.append(AclProtocolTest(duthost, ptfhost, dash_config_info))
        testcases.append(AclAddressTest(duthost, ptfhost, dash_config_info))
        testcases.append(AclPortTest(duthost, ptfhost, dash_config_info))
    elif pytest_testcase_name == "test_acl_tag":
        testcases.append(AclTagTest(duthost, ptfhost, dash_config_info))
    elif pytest_testcase_name == "test_acl_multi_tag":
        testcases.append(AclMultiTagTest(duthost, ptfhost, dash_config_info))
    elif pytest_testcase_name == "test_acl_tag_order":
        testcases.append(AclTagOrderTest(duthost, ptfhost, dash_config_info))
    elif pytest_testcase_name == "test_acl_multi_tag_order":
        testcases.append(AclMultiTagOrderTest(duthost, ptfhost, dash_config_info))
    elif pytest_testcase_name == "test_acl_tag_update_ip":
        testcases.append(AclTagUpdateIpTest(duthost, ptfhost, dash_config_info))
    elif pytest_testcase_name == "test_acl_tag_remove_ip":
        testcases.append(AclTagRemoveIpTest(duthost, ptfhost, dash_config_info))
    elif pytest_testcase_name == "test_acl_tag_scale":
        testcases.append(AclTagScaleTest(duthost, ptfhost, dash_config_info))
    testcases.append(DefaultAclGroupBindTest(duthost, ptfhost, dash_config_info))

    for t in testcases:
        t.config()

    yield testcases

    for t in reversed(testcases):
        t.teardown()


@pytest.fixture(scope="function")
def acl_test_pkts(acl_test_conf):
    test_pkts = []
    for t in acl_test_conf:
        test_pkts.extend(t.test_pkts)
    yield test_pkts
