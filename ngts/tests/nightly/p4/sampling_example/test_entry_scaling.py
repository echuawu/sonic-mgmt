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
import yaml
import os
import time

logger = logging.getLogger()
CHKSUM_MASK = '0xffff'


@pytest.mark.usefixtures('skipping_p4_sampling_test_case_for_spc1')
class TestEntryScaling:
    @pytest.fixture
    def expected_cpu_usage_dict(self, testdir, platform_params):

        current_folder = testdir.request.fspath.dirname
        yaml_file_folder = os.path.dirname(os.path.dirname(os.path.dirname(current_folder)))
        expected_cpu_usage_file = "push_build_tests/system/expected_cpu_usage.yaml"
        expected_cpu_usage_file_path = os.path.join(yaml_file_folder, expected_cpu_usage_file)
        platform_index = 1
        platform = platform_params.hwsku.split('-')[platform_index]
        with open(expected_cpu_usage_file_path) as raw_cpu_data:
            expected_cpu_usage_dict = yaml.load(raw_cpu_data, Loader=yaml.FullLoader)
        expected_cpu_usage_dict = expected_cpu_usage_dict[platform]
        return expected_cpu_usage_dict

    @pytest.fixture
    def expected_ram_usage_dict(self, testdir, platform_params):

        current_folder = testdir.request.fspath.dirname
        yaml_file_folder = os.path.dirname(os.path.dirname(os.path.dirname(current_folder)))
        expected_ram_usage_file = "push_build_tests/system/expected_ram_usage.yaml"
        expected_ram_usage_file_path = os.path.join(yaml_file_folder, expected_ram_usage_file)
        platform_index = 1
        platform = platform_params.hwsku.split('-')[platform_index]
        with open(expected_ram_usage_file_path) as raw_cpu_data:
            expected_ram_usage_dict = yaml.load(raw_cpu_data, Loader=yaml.FullLoader)
            expected_ram_usage_dict = expected_ram_usage_dict[platform]
        return expected_ram_usage_dict

    @allure.title('Test 500 entries added for each table')
    def test_scaling_entries(self, topology_obj, interfaces, engines, hb_dut_1_mac, expected_cpu_usage_dict, expected_ram_usage_dict):
        """
        configure 500 entries for each table, and send traffic for some entry, verify the cpu and memory usage,
        verify the the execution time for the add, show and delete cli command, verify it is added correctly with p4nspect,
        verify the reboot time
        """
        count = 127
        cli_object = topology_obj.players['dut']['cli']
        duthb1_mac = cli_object.mac.get_mac_address_for_interface(
            engines.dut, topology_obj.ports['dut-hb-1'])
        port_params = self.generate_port_entries_params(count, interfaces, duthb1_mac, hb_dut_1_mac)
        flow_params = self.generate_flow_entries_params(count, interfaces, duthb1_mac, hb_dut_1_mac)

        with allure.step("Verify cpu and ram usage before the entries added"):
            self.verify_cpu_ram_usage(engines.dut, expected_cpu_usage_dict, expected_ram_usage_dict)
        with allure.step("Add {} entries for port table and {} entries for flow table with cli command and "
                         "check execution time".format(count, count)):
            self.add_multiple_entries(engines.dut, port_params, flow_params)
        time.sleep(10)

        with allure.step("Verify cpu and ram usage after the entries added"):
            self.verify_cpu_ram_usage(engines.dut, expected_cpu_usage_dict, expected_ram_usage_dict)

        with allure.step("Check entries are added correctly and traffic can be mirrored correctly"):
            self.verify_entries_and_traffic(topology_obj, interfaces, engines.dut, port_params, flow_params)

        with allure.step("Save configuration before reboot"):
            self.save_config(engines.dut)
        with allure.step("Do cold reboot and verify the execution time"):
            self.do_cold_reboot(engines.dut)
        with allure.step("Check entries are still there and traffic can be mirrored correctly after reboot"):
            self.verify_entries_and_traffic(topology_obj, interfaces, engines.dut, port_params, flow_params)

        with allure.step("Remove all entries and verify the execution time"):
            self.remove_all_entries(engines.dut, port_params, flow_params)
        time.sleep(10)
        with allure.step("Check entries are removed "):
            P4SamplingUtils.verify_table_entry(engines.dut, P4SamplingConsts.PORT_TABLE_NAME, port_params, False)
            P4SamplingUtils.verify_table_entry(engines.dut, P4SamplingConsts.FLOW_TABLE_NAME, flow_params, False)

        with allure.step("Check cpu and memory usage after the entries are removed"):
            self.verify_cpu_ram_usage(engines.dut, expected_cpu_usage_dict, expected_ram_usage_dict)

        with allure.step("Save configuration before reboot"):
            self.save_config(engines.dut)
        with allure.step("Do cold reboot and verify the execution time after the entries are cleared"):
            self.do_cold_reboot(engines.dut)

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
            key = '{} {}/{}'.format(ingress_port, P4SamplingUtils.convert_int_to_hex((i+1)*4), CHKSUM_MASK)
            action_params = '{} {} {} {} {} {} {} {}'.format(interfaces.dut_hb_1, duthb1_mac, hb_dut_1_mac,
                                                             P4SamplingEntryConsts.duthb1_ip,
                                                             P4SamplingEntryConsts.hbdut1_ip, l3_mirror_vlan,
                                                             l3_mirror_is_truc, l3_mirror_truc_size)
            entry_params = DottedDict()
            entry_params.action = action_params
            entry_params.priority = random.randint(0, 20)
            entry_params.match_chksum = P4SamplingUtils.convert_int_to_hex((i+1)*4)
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
            entry_params.priority = random.randint(0, 20)
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
            pkt_count = 100
            with allure.step("Clear counters before send traffic"):
                P4SamplingUtils.clear_statistics(engine)
            with allure.step("Send traffic for some of port table entries and verify"):
                # define which entry will be used to verify the traffic, currently use the first and the last one
                indices = list(set([0, len(port_entries) -1]))
                P4SamplingUtils.verify_port_table_send_recv_traffic(topology_obj, engine, interfaces, port_entries,
                                                                    indices, pkt_count, pkt_count, 'match')
            with allure.step("Send traffic for some of flow table entries and verify"):
                indices = list(set([0, len(port_entries) - 1]))
                P4SamplingUtils.verify_flow_table_send_recv_traffic(topology_obj, engine, interfaces, flow_entries,
                                                                    indices, pkt_count, pkt_count, 'match')

    @staticmethod
    def do_cold_reboot(engine):
        start_time = datetime.now()
        engine.reload(['sudo reboot'])
        end_time = datetime.now()
        time_take = (end_time - start_time).total_seconds()
        logger.info('Time takes for the cold reboot is {} seconds'.format(time_take))
        # TODO: this is a bug for the image, after the reboot, need to wait for 180 sec to p4-sampling is up
        time.sleep(180)

    @staticmethod
    def save_config(engine):
        engine.run_cmd('sudo config save -y')

    @staticmethod
    def verify_cpu_ram_usage(engine,  expected_cpu_usage_dict, expected_ram_usage_dict):
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
