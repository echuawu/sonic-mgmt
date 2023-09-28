import pytest
import copy
import abc
import ipaddress
import logging
import random

from constants import *  # noqa: F403
from dash_utils import render_template_to_host, apply_swssconfig_file
from tests.common.errors import RunAnsibleModuleFail

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


def apply_acl_config(duthost, template_name, acl_config_info, op):
    template_file = "{}.j2".format(template_name)
    dest_path = "/tmp/{}.json".format(template_name)
    render_template_to_host(template_file, duthost, dest_path, acl_config_info, op=op)
    apply_swssconfig_file(duthost, dest_path)


class AclGroup(object):
    def __init__(self, duthost, acl_group, eni, ip_version="ipv4"):
        self.duthost = duthost
        self.acl_group = acl_group
        self.eni = eni
        self.ip_version = ip_version
        self.group_conf = {
            ACL_GROUP: self.acl_group,
            IP_VERSION: self.ip_version
        }
        apply_acl_config(self.duthost, ACL_GROUP_TEMPLATE, self.group_conf, op="SET")

    def __del__(self):
        apply_acl_config(self.duthost, ACL_GROUP_TEMPLATE, self.group_conf, op="DEL")

    def bind(self, stage):
        self.stage = stage
        self.bind_conf = {
            ENI: self.eni,
            ACL_GROUP: self.acl_group,
            ACL_STAGE: self.stage,
        }
        apply_acl_config(self.duthost, BIND_ACL_OUT, self.bind_conf, op="SET")
        apply_acl_config(self.duthost, BIND_ACL_IN, self.bind_conf, op="SET")

    def unbind(self):
        apply_acl_config(self.duthost, BIND_ACL_OUT, self.bind_conf, op="DEL")
        apply_acl_config(self.duthost, BIND_ACL_IN, self.bind_conf, op="DEL")


class AclTag(object):
    def __init__(self, duthost, acl_tag, acl_prefix_list, ip_version="ipv4"):
        self.duthost = duthost
        self.tag_conf = {
            ACL_TAG: acl_tag,
            IP_VERSION: ip_version,
            ACL_PREFIX_LIST: acl_prefix_list
        }
        apply_acl_config(self.duthost, ACL_TAG_TEMPLATE, self.tag_conf, op="SET")

    def __del__(self):
        apply_acl_config(self.duthost, ACL_TAG_TEMPLATE, self.tag_conf, op="DEL")


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
    def __init__(self, duthost, dash_config_info):
        __metaclass__ = abc.ABCMeta  # noqa: F841
        self.duthost = duthost
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


class DefaultAclGroupTest(AclTestCase):
    def __init__(self, duthost, dash_config_info):
        super(DefaultAclGroupTest, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.group = AclGroup(self.duthost, self.acl_group, self.dash_config_info[ENI])

    def config(self):
        self.group.bind(DEFAULT_ACL_STAGE)

    def teardown(self):
        self.group.unbind()
        del self.group


class AclRuleTest(AclTestCase):
    def __init__(self, duthost, dash_config_info):
        super(AclRuleTest, self).__init__(duthost, dash_config_info)
        self.rule_confs = []
        self.acl_tag = None

    def add_rule(self, rule_conf):
        rule_conf[ACL_RULE] = self.__class__.__name__ + "_" + rule_conf[ACL_RULE]
        apply_acl_config(self.duthost, ACL_RULE_TEMPLATE, rule_conf, op="SET")
        self.rule_confs.append(rule_conf)

    def add_test_pkt(self, test_pkt):
        test_pkt.description = self.__class__.__name__ + "_" + str(len(self.test_pkts) + 1) + "_" + test_pkt.description
        self.test_pkts.append(test_pkt)

    def teardown(self):
        for rule_conf in self.rule_confs:
            apply_acl_config(self.duthost, ACL_RULE_TEMPLATE, rule_conf, op="DEL")
        self.rule_confs = []


class DefaultAclRule(AclRuleTest):
    def __init__(self, duthost, dash_config_info):
        super(DefaultAclRule, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow",
            ACL_PRIORITY: 1,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: "0.0.0.0/0",
            ACL_SRC_PORT: "1234"
        })


class AclPriorityTest(AclRuleTest):
    def __init__(self, duthost, dash_config_info):
        super(AclPriorityTest, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip = self.get_random_ip()
        self.src_ip_prefix = self.src_ip + "/32"

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "deny_10",
            ACL_PRIORITY: 10,
            ACL_ACTION: "deny",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "1"
        })
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_20",
            ACL_PRIORITY: 20,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: 17,
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
            ACL_RULE: "allow_30",
            ACL_PRIORITY: 30,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: 17,
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "2"
        })
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "deny_40",
            ACL_PRIORITY: 40,
            ACL_ACTION: "deny",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: 17,
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "2"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 2},
                                        expected_receiving=True))


class AclActionTest(AclRuleTest):
    def __init__(self, duthost, dash_config_info):
        super(AclActionTest, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip = self.get_random_ip()
        self.src_ip_prefix = self.src_ip + "/32"

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow_10",
            ACL_PRIORITY: 10,
            ACL_ACTION: "allow",
            ACL_TERMINATING: "false",
            ACL_PROTOCOL: "17",
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "3"
        })
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "deny_20",
            ACL_PRIORITY: 20,
            ACL_ACTION: "deny",
            ACL_TERMINATING: "true",
            ACL_PROTOCOL: 17,
            ACL_SRC_ADDR: self.src_ip_prefix,
            ACL_SRC_PORT: "3"
        })
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(self.dash_config_info,
                                        inner_extra_conf={"udp_sport": 3},
                                        expected_receiving=False))


class AclProtocolTest(AclRuleTest):
    def __init__(self, duthost, dash_config_info):
        super(AclProtocolTest, self).__init__(duthost, dash_config_info)
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
    def __init__(self, duthost, dash_config_info):
        super(AclAddressTest, self).__init__(duthost, dash_config_info)
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
            ACL_RULE: "allow",
            ACL_PRIORITY: 1,
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
            ACL_RULE: "allow",
            ACL_PRIORITY: 1,
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
    def __init__(self, duthost, dash_config_info):
        super(AclPortTest, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip = self.get_random_ip()
        self.src_ip_prefix = self.src_ip + "/32"

    def config(self):
        self.add_rule({
            ACL_GROUP: self.acl_group,
            ACL_RULE: "allow",
            ACL_PRIORITY: 1,
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
    def __init__(self, duthost, dash_config_info):
        super(AclTagTest, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"

    def config(self):
        self.acl_tag = AclTag(self.duthost, "AclTag",
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
    def __init__(self, duthost, dash_config_info):
        super(AclMultiTagTest, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"

    def config(self):
        self.acl_tag = AclTag(self.duthost, "AclMultiTag",
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
    def __init__(self, duthost, dash_config_info):
        super(AclTagOrderTest, self).__init__(duthost, dash_config_info)
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
        self.acl_tag = AclTag(self.duthost, "AclTagOrder", [self.src_ip_prefix])
        dash_config_info = copy.deepcopy(self.dash_config_info)
        dash_config_info[LOCAL_CA_IP] = self.src_ip
        self.add_test_pkt(AclTestPacket(dash_config_info,
                                        inner_extra_conf={"udp_sport": 17},
                                        expected_receiving=True))

    def teardown(self):
        del self.acl_tag
        super(AclTagOrderTest, self).teardown()


class AclMultiTagOrderTest(AclRuleTest):
    def __init__(self, duthost, dash_config_info):
        super(AclMultiTagOrderTest, self).__init__(duthost, dash_config_info)
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
        self.acl_tag = AclTag(self.duthost, "AclMultiTagOrder", [self.src_ip_prefix1, self.src_ip_prefix2])
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
    def __init__(self, duthost, dash_config_info):
        super(AclTagUpdateIpTest, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"

    def config(self):
        self.acl_tag1 = AclTag(self.duthost, "AclTagUpdateIp", [self.src_ip_prefix1])
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
        self.acl_tag2 = AclTag(self.duthost, "AclTagUpdateIp", [self.src_ip_prefix2])
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
    def __init__(self, duthost, dash_config_info):
        super(AclTagRemoveIpTest, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.src_ip1 = self.get_random_ip()
        self.src_ip2 = self.get_random_ip()
        self.src_ip_prefix1 = self.src_ip1 + "/32"
        self.src_ip_prefix2 = self.src_ip2 + "/32"

    def config(self):
        self.acl_tag1 = AclTag(self.duthost, "AclTagRemoveIp",
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
        self.acl_tag2 = AclTag(self.duthost, "AclTagRemoveIp", [self.src_ip_prefix1])
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
    def __init__(self, duthost, dash_config_info):
        super(AclTagScaleTest, self).__init__(duthost, dash_config_info)
        self.acl_group = DEFAULT_ACL_GROUP
        self.ip_list = self.random_scale_ip_list()
        self.src_ip = self.ip_list[0]
        self.src_ip_prefix_list = self.get_scale_prefixes_list()
        self.tag_names_list = ",".join(["AclTagScale{}".format(tag_num) for tag_num in range(1, SCALE_TAGS+1)])

    def config(self):
        self.acl_tag = AclTag(self.duthost, "AclTagScale", self.src_ip_prefix_list)
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
    def random_scale_ip_list(ip_type = 'ipv4'):
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


class AclTagNegativeTest(AclRuleTest):
    def __init__(self, duthost, dash_config_info):
        super(AclTagNegativeTest, self).__init__(duthost, dash_config_info)
        self.config_only = True
        self.acl_group = DEFAULT_ACL_GROUP
        self.incorrect_src_ip_prefix = self.get_incorrect_ip() + "/32"
        self.src_ip_prefix = self.get_random_ip() + "/32"

    def config(self):
        self.acl_tag = AclTag(self.duthost, "AclTagNegativeIP", [self.incorrect_src_ip_prefix])
        err_msg = "Negative test with empty tag name did not failed"
        try:
            AclTag(self.duthost, "AclTagNegativeName", [self.src_ip_prefix])
            raise Exception(err_msg)
        except Exception as err:
            if isinstance(err, RunAnsibleModuleFail):
                logger.info("Negative configuration with empty tag name failed as expected")
            else:
                raise Exception(err)

    def teardown(self):
        super(AclTagNegativeTest, self).teardown()
        del self.acl_tag

    def get_incorrect_ip(self):
        ip = self.get_random_ip()
        zero_start_ip = "0" + ip[ip.find('.'):]
        above_255_ip = "{}.{}".format(ip[:ip.rfind('.')], random.randint(256, 1000))
        rand_place = random.randint(0, len(ip))
        extra_dot_ip = "{}.{}".format(ip[:rand_place], ip[rand_place:])
        incorrect_ip = random.choice([zero_start_ip, above_255_ip, extra_dot_ip])
        logger.info("Incorrect IP, which will be used by test: {}".format(incorrect_ip))
        return incorrect_ip


@pytest.fixture(scope="module")
def acl_test_conf(duthost, dash_config_info):
    # Feature limitation: the group  can't be changed
    # after ENI configuration(dash_basic_config.j2).
    # All tests rules should be configured before.
    testcases = []
    testcases.append(DefaultAclGroupTest(duthost, dash_config_info))
    testcases.append(DefaultAclRule(duthost, dash_config_info))
    testcases.append(AclPriorityTest(duthost, dash_config_info))
    testcases.append(AclActionTest(duthost, dash_config_info))
    testcases.append(AclPortTest(duthost, dash_config_info))

    # Still not supported on last image
    # testcases.append(AclTagTest(duthost, dash_config_info))
    # testcases.append(AclMultiTagTest(duthost, dash_config_info))
    # testcases.append(AclTagOrderTest(duthost, dash_config_info))
    # testcases.append(AclMultiTagOrderTest(duthost, dash_config_info))
    # testcases.append(AclTagUpdateIpTest(duthost, dash_config_info))
    # testcases.append(AclTagRemoveIpTest(duthost, dash_config_info))
    # testcases.append(AclTagScaleTest(duthost, dash_config_info))
    # testcases.append(AclTagNegativeTest(duthost, dash_config_info))

    # Cannot passed testcases
    # testcases.append(AclProtocolTest(duthost, dash_config_info))
    # testcases.append(AclAddressTest(duthost, dash_config_info))

    for t in testcases:
        t.config()

    yield testcases

    for t in reversed(testcases):
        t.teardown()
