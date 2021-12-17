import pytest
import logging
import allure
from dotted_dict import DottedDict
from datetime import datetime
import random
from ngts.constants.constants import P4SamplingConsts
from ngts.cli_wrappers.sonic.sonic_p4_sampling_clis import P4SamplingCli
from ngts.constants.constants import P4SamplingEntryConsts
from ngts.helpers.p4_sampling_utils import P4SamplingUtils
from ngts.tests.push_build_tests.system.test_cpu_ram_hdd_usage import get_cpu_usage_and_processes
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
import yaml
import os
import time
import re
from retry import retry

logger = logging.getLogger()
CHKSUM_MASK = '0xffff'
P4_SAMPLING_ENTRY_PRIO_MAX = 126


@pytest.mark.build
@pytest.mark.usefixtures('skipping_p4_sampling_test_case_for_spc1')
class TestEntryScaling:

    @pytest.mark.reboot_reload
    @allure.title('Test 500 entries added for each table')
    @pytest.mark.usefixtures('ignore_expected_loganalyzer_exceptions')
    def test_scaling_entries(self, topology_obj, interfaces, engines, hb_dut_1_mac, expected_cpu_usage_dict, expected_ram_usage_dict):
        """
        configure 500 entries for each table, and send traffic for some entry, verify the cpu and memory usage,
        verify the the execution time for the add, show and delete cli command, verify it is added correctly with p4nspect,
        verify the reboot time
        """
        count = 12
        cli_object = topology_obj.players['dut']['cli']
        duthb1_mac = cli_object.mac.get_mac_address_for_interface(
            engines.dut, topology_obj.ports['dut-hb-1'])
        port_params = self.generate_port_entries_params(count, interfaces, duthb1_mac, hb_dut_1_mac)
        flow_params = self.generate_flow_entries_params(count, interfaces, duthb1_mac, hb_dut_1_mac)
        with allure.step("Enable p4-sampling"):
            SonicGeneralCli.set_feature_state(engines.dut, P4SamplingConsts.APP_NAME, 'enabled')
        with allure.step("Verify cpu and ram usage before the entries added"):
            self.verify_cpu_ram_usage(engines.dut, expected_cpu_usage_dict, expected_ram_usage_dict)
        with allure.step("Add {} entries for port table and {} entries for flow table with cli command and "
                         "check execution time".format(count, count)):
            self.add_multiple_entries(engines.dut, port_params, flow_params)
        try:
            with allure.step("Verify cpu and ram usage after the entries added"):
                self.verify_cpu_ram_usage(engines.dut, expected_cpu_usage_dict, expected_ram_usage_dict)

            with allure.step("Check entries are added correctly and traffic can be mirrored correctly"):
                self.verify_entries_and_traffic(topology_obj, interfaces, engines.dut, port_params, flow_params)

            with allure.step("Save configuration before reboot"):
                SonicGeneralCli.save_configuration(engines.dut)
            with allure.step("Do cold reboot and verify the execution time"):
                self.do_cold_reboot(engines.dut, topology_obj)
            with allure.step("Check entries are still there and traffic can be mirrored correctly after reboot"):
                self.verify_entries_and_traffic(topology_obj, interfaces, engines.dut, port_params, flow_params)
        finally:
            with allure.step("Remove all entries and verify the execution time"):
                self.remove_all_entries(engines.dut, port_params, flow_params)
        with allure.step("Check entries are removed "):
            P4SamplingUtils.verify_table_entry(engines.dut, P4SamplingConsts.PORT_TABLE_NAME, port_params, False)
            P4SamplingUtils.verify_table_entry(engines.dut, P4SamplingConsts.FLOW_TABLE_NAME, flow_params, False)

        with allure.step("Check cpu and memory usage after the entries are removed"):
            self.verify_cpu_ram_usage(engines.dut, expected_cpu_usage_dict, expected_ram_usage_dict)

        with allure.step("Save configuration before reboot"):
            SonicGeneralCli.save_configuration(engines.dut)
        with allure.step("Do cold reboot and verify the execution time after the entries are cleared"):
            self.do_cold_reboot(engines.dut, topology_obj)

    @staticmethod
    def generate_port_entries_params(count, interfaces, duthb1_mac, hb_dut_1_mac):
        """
        generate params for port entries
        :param count: count of entries to be added or removed
        :param interfaces: interfaces fixture object
        :param duthb1_mac: duthb1_mac fixture object
        :param hb_dut_1_mac: hb_dut_1_mac ixture object
        :return: dictionary of port entries key, action, priority.
                 example:
        """
        ret = {}
        ingress_port = interfaces.dut_ha_2
        l3_mirror_vlan = random.randint(0, 1026)
        l3_mirror_is_truc = True
        l3_mirror_truc_size = 512
        for i in range(count):
            key = '{} {}/{}'.format(ingress_port, P4SamplingUtils.convert_int_to_hex((i + 1) * 4), CHKSUM_MASK)
            action_params = '{} {} {} {} {} {} {} {}'.format(interfaces.dut_hb_1, duthb1_mac, hb_dut_1_mac,
                                                             P4SamplingEntryConsts.duthb1_ip,
                                                             P4SamplingEntryConsts.hbdut1_ip, l3_mirror_vlan,
                                                             l3_mirror_is_truc, l3_mirror_truc_size)
            entry_params = DottedDict()
            entry_params.action = action_params
            entry_params.priority = random.randint(0, P4_SAMPLING_ENTRY_PRIO_MAX)
            entry_params.match_chksum = P4SamplingUtils.convert_int_to_hex((i + 1) * 4)
            entry_params.mismatch_chksum = 0x0000
            ret[key] = entry_params
        return ret

    @staticmethod
    def generate_flow_entries_params(count, interfaces, duthb1_mac, hb_dut_1_mac):
        """
        generate the params for the flow entries
        :param count: the count of flow entry to generate
        :param interfaces: interfaces fixture object
        :param duthb1_mac: duthb1_mac fixture object
        :param hb_dut_1_mac: hb_dut_1_mac ixture object
        :return: Dictionary of params of flow entries,
                 example:
        """
        ret = {}
        l3_mirror_vlan = random.randint(0, 1026)
        l3_mirror_is_truc = True
        l3_mirror_truc_size = 512
        for i in range(count):
            protocol = 6
            src_port = 20
            dst_port = 80
            key = '{} {} {} {} {} {}/{}'.format(
                P4SamplingEntryConsts.hadut2_ip,
                P4SamplingEntryConsts.hbdut2_ip,
                protocol,
                src_port,
                dst_port,
                P4SamplingUtils.convert_int_to_hex((i + 1) * 4), CHKSUM_MASK)
            action_params = '{} {} {} {} {} {} {} {}'.format(interfaces.dut_hb_1, duthb1_mac, hb_dut_1_mac,
                                                             P4SamplingEntryConsts.duthb1_ip,
                                                             P4SamplingEntryConsts.hbdut1_ip, l3_mirror_vlan,
                                                             l3_mirror_is_truc, l3_mirror_truc_size)
            entry_params = DottedDict()
            entry_params.action = action_params
            entry_params.priority = random.randint(0, P4_SAMPLING_ENTRY_PRIO_MAX)
            entry_params.match_chksum = P4SamplingUtils.convert_int_to_hex((i + 1) * 4)
            entry_params.mismatch_chksum = '0x0000'
            ret[key] = entry_params
        return ret

    @staticmethod
    def add_multiple_entries(engine, port_entry_params, flow_entry_params):
        """
        add entries with params defined in the entry_params
        :param engine: ssh engine object
        :param port_entry_params: port entry params
        :param flow_entry_params: flow entry params
        :return: None
        """
        port_key_params_list = []
        for key in port_entry_params.keys():
            action_params = port_entry_params[key].action
            priority = port_entry_params[key].priority
            params = 'key {} action {} {} priority {}'.format(key, P4SamplingConsts.ACTION_NAME, action_params, priority)
            port_key_params_list.append(params)
        flow_key_params_list = []
        for key in flow_entry_params.keys():
            action_params = flow_entry_params[key].action
            priority = flow_entry_params[key].priority
            params = 'key {} action {} {} priority {}'.format(key, P4SamplingConsts.ACTION_NAME, action_params, priority)
            flow_key_params_list.append(params)

        start_time = datetime.now()
        P4SamplingCli.add_entries_to_table(engine, P4SamplingConsts.PORT_TABLE_NAME, port_key_params_list)
        P4SamplingCli.add_entries_to_table(engine, P4SamplingConsts.FLOW_TABLE_NAME, flow_key_params_list)
        end_time = datetime.now()
        time_take = (end_time - start_time).total_seconds()
        logger.info("Time take for add {} entries : {} seconds".format(len(port_key_params_list) + len(flow_key_params_list),
                                                                       time_take))

    @staticmethod
    def remove_all_entries(engine, port_entry_params, flow_entry_params):
        """
        Remove p4 sampling entries
        :param engine: ssh engine object
        :param port_entry_params: port entry params
        :param flow_entry_params: flow entry params
        :return: None
        """

        port_key_params_list = []
        for key in port_entry_params.keys():
            port_key_params = 'key {}'.format(key)
            port_key_params_list.append(port_key_params)
        flow_key_params_list = []
        for key in flow_entry_params.keys():
            flow_key_params = 'key {}'.format(key)
            flow_key_params_list.append(flow_key_params)

        start_time = datetime.now()
        P4SamplingCli.delete_entries_from_table(engine, P4SamplingConsts.PORT_TABLE_NAME, port_key_params_list)
        P4SamplingCli.delete_entries_from_table(engine, P4SamplingConsts.FLOW_TABLE_NAME, flow_key_params_list)
        end_time = datetime.now()
        time_take = (end_time - start_time).total_seconds()
        logger.info("Time take for remove {} entries: {} seconds".format(len(port_key_params_list) + len(flow_key_params_list),
                                                                         time_take))

    def verify_entries_and_traffic(self, topology_obj, interfaces, engine, port_entries, flow_entries):
        self.verify_entries_added(engine, port_entries, flow_entries)
        self.verify_send_recv_traffic(topology_obj, interfaces, engine, port_entries, flow_entries)

    @staticmethod
    def verify_entries_added(engine, port_entries, flow_entries):
        with allure.step("Verify entries added correctly for port table"):
            P4SamplingUtils.verify_table_entry(engine, P4SamplingConsts.PORT_TABLE_NAME, port_entries)
        with allure.step("Verify entries added correctly for flow table"):
            P4SamplingUtils.verify_table_entry(engine, P4SamplingConsts.FLOW_TABLE_NAME, flow_entries)

    @staticmethod
    def verify_send_recv_traffic(topology_obj, interfaces, engine, port_entries, flow_entries):
        with allure.step("Send traffic"):
            pkt_count = 20
            with allure.step("Clear counters before send traffic"):
                P4SamplingUtils.clear_statistics(engine)
            with allure.step("Send traffic for some of port table entries and verify"):
                # define which entry will be used to verify the traffic, currently use the first and the last one
                indices = list(set([0, len(port_entries) - 1]))
                P4SamplingUtils.verify_port_table_send_recv_traffic(topology_obj, engine, interfaces, port_entries,
                                                                    indices, pkt_count, pkt_count, 'match')
            with allure.step("Send traffic for some of flow table entries and verify"):
                indices = list(set([0, len(port_entries) - 1]))
                P4SamplingUtils.verify_flow_table_send_recv_traffic(topology_obj, engine, interfaces, flow_entries,
                                                                    indices, pkt_count, pkt_count, 'match')

    def do_cold_reboot(self, engine_dut, topology_obj):
        start_time = datetime.now()
        SonicGeneralCli.reboot_reload_flow(engine_dut, topology_obj=topology_obj)
        end_time = datetime.now()
        time_take = (end_time - start_time).total_seconds()
        logger.info('Time takes for the cold reboot is {} seconds'.format(time_take))
        self.verify_p4_sampling_up(engine_dut)

    @staticmethod
    @retry(Exception, tries=10, delay=10)
    def verify_p4_sampling_up(engine_dut):
        """
        Verifying the dockers are in up state
        :param engine: ssh engine object
        :return: None, raise error in case of unexpected result
        """
        engine_dut.run_cmd('docker ps | grep {}'.format(P4SamplingConsts.APP_NAME), validate=True)

    @staticmethod
    def get_uptime(engine_dut):
        reg = r'(.+)(up.+\d+)(\D*,)(.+)(,)(.+)(,)(.+)(,)(.+)'
        uptime_ret = engine_dut.run_cmd('uptime')
        uptime = re.match(reg, uptime_ret).group(2).split()[1]
        uptime_arr = uptime.split(':')
        if len(uptime_arr) == 2:
            return int(uptime_arr[0]) * 60 + int(uptime_arr[1])
        else:
            return int(uptime_arr[0])

    @staticmethod
    def verify_cpu_ram_usage(engine, expected_cpu_usage_dict, expected_ram_usage_dict):
        total_cpu_usage, _ = get_cpu_usage_and_processes(engine)
        free_output = engine.run_cmd('sudo free')
        total_ram_size_mb = int(free_output.splitlines()[1].split()[1]) / 1024
        used_ram_size_mb = int(free_output.splitlines()[1].split()[2]) / 1024
        logger.info('DUT total RAM size: {} Mb'.format(total_ram_size_mb))
        logger.info('DUT use: {} Mb of RAM'.format(used_ram_size_mb))
        logger.info('DUT total cpu usage is {}'.format(total_cpu_usage))

        logger.info('Acceptable cpu usage is {}'.format(expected_cpu_usage_dict['total']))
        logger.info('Acceptable ram usage is {}'.format(expected_ram_usage_dict['total']))
        assert total_cpu_usage < expected_cpu_usage_dict['total']
        assert used_ram_size_mb < expected_ram_usage_dict['total']
