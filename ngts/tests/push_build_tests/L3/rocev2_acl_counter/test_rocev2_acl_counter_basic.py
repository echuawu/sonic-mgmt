import allure
import logging
import pytest
import os
import json
import copy

from ngts.helpers.rocev2_acl_counter_helper import traffic_validation, verify_acl_rule_counter, gen_pcap_file, is_support_rocev2_acl_counter_feature

ROCEV2_ACL_COUNTER_PATH = os.path.dirname(os.path.abspath(__file__))

logger = logging.getLogger()


class TestRocev2AclCounter:

    @pytest.fixture(autouse=True)
    def setup_param(self, topology_obj, players, dut_ha_1_mac, cli_objects, is_simx, sonic_branch, upgrade_params):
        if upgrade_params.is_upgrade_required:
            base_image, target_image = cli_objects.dut.general.get_base_and_target_images()
            if '202211' in base_image or '202205' in base_image or '202012' in base_image:
                pytest.skip(f'Rocev2 acl counter during upgrade from {base_image} image is not supported')

        if not is_support_rocev2_acl_counter_feature(cli_objects, is_simx, sonic_branch):
            pytest.skip(pytest.skip("The rocev2 acl counter feature is missing, skipping the test case"))
        self.topology_obj = topology_obj
        self.players = players
        self.cli_obj = self.topology_obj.players['dut']['cli']
        self.dut_ha_1_mac = dut_ha_1_mac
        self.rocev2_acl_rule_list = get_rocev2_acl_rule_list()

    @pytest.mark.build
    @pytest.mark.push_gate
    @allure.title('test_rocev2_acl_counter_basic')
    def test_rocev2_acl_counter_basic(self):
        """
        This test verifying that rocev2 acl counter works correctly when sending rocev2 packets,
        matching the corresponding acl rule or non-rocev2 packet not matching corresponding acl rule
        1. Send packet matching acl rule
        2. Verify relevant counter counts correctly
        3. Send packets not matching acl rule
        4. Verify relevant counter counts correctly
        """
        self.verify_rocev2_counter_by_sending_packet()

    def verify_rocev2_counter_by_sending_packet(self):
        send_packet_count = 3

        self.gen_pacp_file_and_send_traffic(self.rocev2_acl_rule_list, traffic_type="match",
                                            send_packet_count=send_packet_count)

        with allure.step(f"Verify relevant counter counts should be {send_packet_count}"):
            verify_acl_rule_counter(self.topology_obj, send_packet_count, self.rocev2_acl_rule_list)

        self.gen_pacp_file_and_send_traffic(self.rocev2_acl_rule_list, traffic_type="unmatch",
                                            send_packet_count=send_packet_count)

        with allure.step("Verify relevant counter should be 0"):
            verify_acl_rule_counter(self.topology_obj, 0, self.rocev2_acl_rule_list)

    def gen_pacp_file_and_send_traffic(self, rocev2_acl_rule_list, traffic_type, send_packet_count):
        sender = 'ha'
        sender_port = "bond0"
        dst_mac = self.dut_ha_1_mac
        port_type = "physical"
        with allure.step(f"Gen pcap file with packets {traffic_type} acl rule"):
            send_pcap_info_dict = {}
            self.cli_obj.acl.clear_acl_counters('')
            for acl_rule in rocev2_acl_rule_list:
                dst_ip = "40.0.0.3" if acl_rule["src_type"] == 'SRC_IP' else "4000::3"
                gen_pcap_file(sender, sender_port, acl_rule, dst_mac, dst_ip, traffic_type, port_type,
                              send_pcap_info_dict)

        with allure.step(f"Send traffic with:{send_pcap_info_dict} "):
            traffic_validation(self.players, send_pcap_info_dict, send_packet_count)


def get_rocev2_acl_rule_list():
    acl_config_file = os.path.join(ROCEV2_ACL_COUNTER_PATH, 'rocev2_acl.json')
    with open(acl_config_file, 'r') as acl_config_f:
        acl_config = json.load(acl_config_f)
    rocev2_acl_rule_list = []
    acl_rule_template = {'table_name': 'ROCE_ACL_INGRESS',
                         'name': 'in_forward_rule1',
                         'priority': '3301',
                         'action_type': 'PACKET_ACTION',
                         'action': 'FORWARD',
                         'src_type': 'SRC_IP',
                         'src_ip': '112.110.1.1/24',
                         'scenario': 'bth_aeth_together',
                         'bth_opcode': '0x11/0xbf',
                         'aeth_syndrome': '0x60/0x60'}
    for alc_rule_table_and_name, acl_rule in acl_config["ACL_RULE"].items():
        one_acl_rule = copy.copy(acl_rule_template)
        one_acl_rule["name"] = alc_rule_table_and_name.split("|")[1].strip()
        one_acl_rule["priority"] = acl_rule["PRIORITY"]
        one_acl_rule["action"] = acl_rule["PACKET_ACTION"]
        one_acl_rule["src_type"] = "SRC_IP" if "SRC_IP" in acl_rule else "SRC_IPV6"
        one_acl_rule["src_ip"] = acl_rule[one_acl_rule["src_type"]]
        rocev2_acl_rule_list.append(one_acl_rule)
    return rocev2_acl_rule_list
