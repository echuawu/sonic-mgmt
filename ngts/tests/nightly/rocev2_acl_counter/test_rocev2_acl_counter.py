import allure
import logging
import pytest

from ngts.helpers.rocev2_acl_counter_helper import traffic_validation, verify_acl_rule_counter, gen_pcap_file
from ngts.tests.nightly.rocev2_acl_counter.constants import V4_CONFIG, V6_CONFIG


logger = logging.getLogger()


class TestRocev2AclCounter:

    @pytest.fixture(autouse=True)
    def setup_param(self, topology_obj, interfaces, players, dut_ha_1_mac):
        self.topology_obj = topology_obj
        self.interfaces = interfaces
        self.players = players
        self.dut_ha_1_mac = dut_ha_1_mac
        self.cli_obj = topology_obj.players['dut']['cli']

    @pytest.mark.parametrize("port_type", ["physical", "lag"])
    @allure.title('test_rocev2_acl_counter')
    def test_rocev2_acl_counter(self, rocev2_acl_rule_list, apply_rocev2_acl_config, port_type):
        """
        This test verifying that rocev2 acl counter works correctly when sending rocev2 packets,
        matching the corresponding acl rule or non-rocev2 packet not matching corresponding acl rule
        1. Send packet matching acl rule
        2. Verify relevant counter counts correctly
        3. Send packets not matching acl rule
        4. Verify relevant counter counts correctly
        """
        self.verify_rocev2_counter_by_sending_packet(port_type, rocev2_acl_rule_list)

    @pytest.mark.parametrize("port_type", ["physical", "lag"])
    @allure.title('test_toggle_port_rocev2_acl_counter')
    def test_toggle_port_rocev2_acl_counter(self, toggle_tested_port, rocev2_acl_rule_list, apply_rocev2_acl_config, port_type):
        """
        This test verifying that after toggle the tested ports, rocev2 acl counter works correctly when sending rocev2
        packets, matching the corresponding acl rule or non-rocev2 packet not matching corresponding acl rule
        1. Toggle test ports, check port is up or not
        2. Send packet matching acl rule
        3. Verify relevant counter counts correctly
        4. Send packets not matching acl rule
        5. Verify relevant counter counts correctly
        """
        self.verify_rocev2_counter_by_sending_packet(port_type, rocev2_acl_rule_list)

    def verify_rocev2_counter_by_sending_packet(self, port_type, rocev2_acl_rule_list):
        send_packet_count = 3

        self.gen_pacp_file_and_send_traffic(port_type, rocev2_acl_rule_list, traffic_type="match",
                                            send_packet_count=send_packet_count)

        with allure.step(f"Verify relevant counter counts should be {send_packet_count}"):
            verify_acl_rule_counter(self.topology_obj, send_packet_count, rocev2_acl_rule_list)

        self.gen_pacp_file_and_send_traffic(port_type, rocev2_acl_rule_list, traffic_type="unmatch",
                                            send_packet_count=send_packet_count)

        with allure.step("Verify relevant counter should be 0"):
            verify_acl_rule_counter(self.topology_obj, 0, rocev2_acl_rule_list)

    def gen_pacp_file_and_send_traffic(self, port_type, rocev2_acl_rule_list, traffic_type, send_packet_count):
        with allure.step(f"Gen pcap file with packets {traffic_type} acl rule"):
            send_pcap_info_dict = {}
            self.cli_obj.acl.clear_acl_counters('')
            for acl_rule in rocev2_acl_rule_list:
                sender, sender_port, dst_mac, dst_ip = self.get_info_for_sending_packet(port_type, acl_rule)
                gen_pcap_file(sender, sender_port, acl_rule, dst_mac, dst_ip, traffic_type, port_type, send_pcap_info_dict)

        with allure.step(f"Send traffic with:{send_pcap_info_dict} "):
            traffic_validation(self.players, send_pcap_info_dict, send_packet_count)

    def get_info_for_sending_packet(self, port_type, acl_rule):
        dst_mac = self.dut_ha_1_mac
        if port_type == "physical":
            if acl_rule["table_name"] == "ROCE_ACL_INGRESS":
                sender_port = self.interfaces.ha_dut_1
                dst_ip = self.get_dst_ip(acl_rule, 'hb_dut_1')
                sender = 'ha'
            else:
                sender_port = self.interfaces.hb_dut_1
                dst_ip = self.get_dst_ip(acl_rule, 'ha_dut_1')
                sender = 'hb'
        else:
            if acl_rule["table_name"] == "ROCE_ACL_INGRESS":
                sender_port = 'bond1'
                dst_ip = self.get_dst_ip(acl_rule, 'hb_dut_1')
                sender = 'ha'
            else:
                sender_port = self.interfaces.hb_dut_1
                dst_ip = self.get_dst_ip(acl_rule, 'ha_dut_2')
                sender = 'hb'
        logging.info(f"ingress_port: {sender_port}, dst_mac: {dst_mac}, dst_ip: {dst_ip}")
        return sender, sender_port, dst_mac, dst_ip

    def get_dst_ip(self, acl_rule, dst_interface):
        return V4_CONFIG[dst_interface] if acl_rule["src_type"] == "SRC_IP" else V6_CONFIG[dst_interface]
