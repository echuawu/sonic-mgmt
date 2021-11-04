import pytest
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.helpers.p4_sampling_utils import *
import time
import ngts.helpers.json_file_helper as json_file_helper
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
import ngts.helpers.breakout_helpers as breakout_helpers
logger = logging.getLogger()
APP_NAME = P4SamplingConsts.APP_NAME
PORT_TABLE_NAME = P4SamplingConsts.PORT_TABLE_NAME
FLOW_TABLE_NAME = P4SamplingConsts.FLOW_TABLE_NAME
ACTION_NAME = P4SamplingConsts.ACTION_NAME
P4_SAMPLING_KEY = "P4_SAMPLING"
TRAFFIC_INTERVAL = P4SamplingConsts.TRAFFIC_INTERVAL
# TODO: the err msg need to be updated after the dynamic port breakout is supported
DPB_ERR_MSG = "ERR: Can not dynamic breakout*"


@pytest.mark.build
@pytest.mark.usefixtures('p4_sampling_entries')
class TestEntryTraffic:
    @pytest.fixture(scope='class')
    def port_traffic_params_list(self, engines, interfaces, topology_obj, table_params):
        chksum_type = 'match'
        indices = [0]
        port_traffic_params_list = TrafficParams.prepare_port_table_send_receive_traffic_params(interfaces, topology_obj,
                                                                                                table_params.port_entry, indices,
                                                                                                chksum_type)
        return port_traffic_params_list

    @pytest.fixture(scope='class')
    def flow_traffic_params_list(self, engines, interfaces, topology_obj, table_params):
        chksum_type = 'match'
        indices = [0]
        _, flow_traffic_params_list = TrafficParams.prepare_flow_table_send_receive_traffic_params(interfaces, topology_obj,
                                                                                                   table_params.flow_entry, indices,
                                                                                                   chksum_type)
        return flow_traffic_params_list

    @pytest.fixture(scope='function')
    def start_stop_continuous_traffic(self, topology_obj, port_traffic_params_list, flow_traffic_params_list):
        with allure.step("Send continuous traffic"):
            port_table_scapy_senders = P4SamplingUtils.start_background_port_table_traffic(topology_obj, port_traffic_params_list)
            flow_table_scapy_senders = P4SamplingUtils.start_background_flow_table_traffic(topology_obj, flow_traffic_params_list)
        yield
        with allure.step("Stop continuous traffic"):
            P4SamplingUtils.stop_background_traffic(port_table_scapy_senders)
            P4SamplingUtils.stop_background_traffic(flow_table_scapy_senders)

    @pytest.mark.reboot_reload
    @pytest.mark.usefixtures('ignore_expected_loganalyzer_exceptions')
    @allure.title('Test disable p4-sampling, change the config db file, and re-enable it, the entries can be changed.')
    def test_enable_disable_p4_sampling(self, topology_obj, engines, interfaces, table_params):
        pkt_count = 20
        with allure.step("Verify that the entries has been added"):
            P4SamplingUtils.verify_table_entry(engines.dut, PORT_TABLE_NAME, table_params.port_entry, True)
            P4SamplingUtils.verify_table_entry(engines.dut, FLOW_TABLE_NAME, table_params.flow_entry, True)
        with allure.step("Save config"):
            engines.dut.run_cmd('sudo config save -y')
        with allure.step("Disable p4-sampling"):
            SonicGeneralCli.set_feature_state(engines.dut, P4SamplingConsts.APP_NAME, 'disabled')
        with allure.step("Remove all entries from the config db"):
            entries_config_removed = json_file_helper.remove_key_from_config_db(engines.dut, P4_SAMPLING_KEY)
        with allure.step("Reload config"):
            SonicGeneralCli.reboot_reload_flow(engines.dut, r_type='config reload -y', topology_obj=topology_obj)
        with allure.step("Enable p4-sampling"):
            SonicGeneralCli.set_feature_state(engines.dut, P4SamplingConsts.APP_NAME, 'enabled')
        with allure.step("Verify that the entries has been removed"):
            P4SamplingUtils.verify_table_entry(engines.dut, PORT_TABLE_NAME, table_params.port_entry, False)
            P4SamplingUtils.verify_table_entry(engines.dut, FLOW_TABLE_NAME, table_params.flow_entry, False)
        with allure.step("Send traffic and check traffic can not be mirrored, and the counter is as expected"):
            P4SamplingUtils.verify_traffic_hit(topology_obj, engines, interfaces, table_params, pkt_count, 0)
        with allure.step("Disable p4-sampling"):
            SonicGeneralCli.set_feature_state(engines.dut, P4SamplingConsts.APP_NAME, 'disabled')
        with allure.step("Add all entries back to config db"):
            json_file_helper.add_content_to_config_db(engines.dut, entries_config_removed, P4_SAMPLING_KEY)
        with allure.step("Reload config"):
            SonicGeneralCli.reboot_reload_flow(engines.dut, r_type='config reload -y', topology_obj=topology_obj)
        with allure.step("Enable p4-sampling"):
            SonicGeneralCli.set_feature_state(engines.dut, P4SamplingConsts.APP_NAME, 'enabled')
        with allure.step("Verify that the entries has been added back"):
            P4SamplingUtils.verify_table_entry(engines.dut, PORT_TABLE_NAME, table_params.port_entry, True)
            P4SamplingUtils.verify_table_entry(engines.dut, FLOW_TABLE_NAME, table_params.flow_entry, True)
        with allure.step("Send the traffic and the traffic can still be mirrored and the counter is as expected"):
            P4SamplingUtils.verify_traffic_hit(topology_obj, engines, interfaces, table_params, pkt_count, pkt_count)

    @pytest.mark.skip(reason="skip until all config_db.json file will be updated with breakout_cfg section")
    @allure.title('Test Dynamic port breakout on the port used in the entries..')
    def test_dpb_on_port_used_by_p4_entries(self, topology_obj, engines, interfaces, table_params, loganalyzer):
        with allure.step("Do dynamic port breakout for port used in entries added"):
            indices = list(range(len(table_params.port_entry)))
            ingress_ports = self.get_ingress_ports(indices, table_params.port_entry)
            mirror_ports = self.get_mirror_ports(indices, table_params)
            port_list = list(set(ingress_ports + mirror_ports))
            origin_break_out_conf = breakout_helpers.get_default_breakout_mode(engines.dut,
                                                                               topology_obj.players['dut']['cli'],
                                                                               port_list)
            self.config_breakout_mode_and_expect_log(engines.dut, topology_obj, port_list, loganalyzer)
        with allure.step("Remove entries"):
            self.add_entries(engines.dut, table_params)
        with allure.step("Verify entries removed"):
            P4SamplingUtils.verify_table_entry(engines.dut, PORT_TABLE_NAME, table_params.port_entry, False)
            P4SamplingUtils.verify_table_entry(engines.dut, FLOW_TABLE_NAME, table_params.flow_entry, False)
        with allure.step("Undo Dynamic port breakout"):
            SonicInterfaceCli.configure_dpb_on_ports(engines.dut, origin_break_out_conf)
        with allure.step("Add entries back"):
            self.remove_entries(engines.dut, table_params)
        with allure.step("Verify entries added"):
            P4SamplingUtils.verify_table_entry(engines.dut, PORT_TABLE_NAME, table_params.port_entry, True)
            P4SamplingUtils.verify_table_entry(engines.dut, FLOW_TABLE_NAME, table_params.flow_entry, True)
        with allure.step("Send the traffic and the traffic can still be mirrored and the counter is as expected"):
            P4SamplingUtils.verify_traffic_hit(topology_obj, engines, interfaces, table_params, 50, 50)

    @allure.title('Test disables p4-sampling or shutdown interface, and verifies that traffic can not be mirrored. '
                  'Then enable it back and verify that traffic can be mirrored again.')
    @pytest.mark.usefixtures('ignore_expected_loganalyzer_exceptions')
    @pytest.mark.usefixtures('start_stop_continuous_traffic')
    def test_p4_sampling_traffic_concussive(self, topology_obj, engines, interfaces, table_params,
                                            port_traffic_params_list, flow_traffic_params_list):
        indices = [0]
        disable_enable_times = 10
        port_entry_keys = []
        for index in indices:
            port_entry_keys.append(list(table_params.port_entry.keys())[index])
        chksum_type = 'match'
        flow_entry_keys, _ = TrafficParams.prepare_flow_table_send_receive_traffic_params(interfaces, topology_obj,
                                                                                          table_params.flow_entry,
                                                                                          indices, chksum_type)
        with allure.step("Check traffic counter will increase after the update interval"):
            self.verify_traffic_received(topology_obj, engines.dut, port_traffic_params_list, flow_traffic_params_list)
        with allure.step("Disable enable p4-sampling for {} times".format(disable_enable_times)):
            self.disable_enable_feature_state(engines.dut, P4SamplingConsts.APP_NAME, disable_enable_times)
        with allure.step("Disable p4-sampling"):
            SonicGeneralCli.set_feature_state(engines.dut, P4SamplingConsts.APP_NAME, 'disabled')
            # sleep for 1 second to wait until this is configured to HW and traffic mirror stops
            time.sleep(1)
        with allure.step("Check traffic can not be received by the mirror port"):
            self.verify_traffic_lossed(topology_obj, engines.dut, port_traffic_params_list, flow_traffic_params_list)
        with allure.step("Enable p4-sampling"):
            SonicGeneralCli.set_feature_state(engines.dut, P4SamplingConsts.APP_NAME, 'enabled')
            # sleep for 1 second to wait until this is configured to HW and traffic mirror starts
            time.sleep(1)
        with allure.step("Check traffic can be received by the mirror port"):
            self.verify_traffic_received(topology_obj, engines.dut, port_traffic_params_list, flow_traffic_params_list)
            self.verify_entries_hit(engines.dut, port_entry_keys, flow_entry_keys)

        ingress_ports = self.get_ingress_ports(indices, table_params.port_entry)
        with allure.step("Shutdown port of the ingress port in the port table"):
            self.shutdown_ports(engines.dut, ingress_ports)
        with allure.step("Check traffic can not be received by the mirror port"):
            self.verify_traffic_lossed(topology_obj, engines.dut, port_traffic_params_list, [])
            self.verify_entries_missed(engines.dut, port_entry_keys, [])
        with allure.step("Startup port of the ingress port in the port table"):
            self.startup_ports(engines.dut, ingress_ports)
        with allure.step("Check traffic can be received by the mirror port"):
            self.verify_traffic_received(topology_obj, engines.dut, port_traffic_params_list, [])
            self.verify_entries_hit(engines.dut, port_entry_keys, [])

        mirror_ports = self.get_mirror_ports(indices, table_params)
        with allure.step("Shutdown the mirror port in the port and flow table"):
            self.shutdown_ports(engines.dut, mirror_ports)
        with allure.step("Check traffic can not be received by the mirror port"):
            self.verify_traffic_lossed(topology_obj, engines.dut, port_traffic_params_list, flow_traffic_params_list)
            self.verify_entries_missed(engines.dut, port_entry_keys, flow_entry_keys)
        with allure.step("Startup the mirror port in the port and flow table"):
            self.startup_ports(engines.dut, mirror_ports)
        with allure.step("Check traffic can be received by the mirror port"):
            self.verify_traffic_received(topology_obj, engines.dut, port_traffic_params_list, flow_traffic_params_list)
            self.verify_entries_hit(engines.dut, port_entry_keys, flow_entry_keys)

    @pytest.mark.usefixtures('ignore_expected_loganalyzer_exceptions')
    @allure.title('Test upgrade and downgrade p4-sampling app')
    def test_upgrade_p4_sampling(self, engines, table_params, topology_obj, interfaces):
        current_version = SonicAppExtensionCli.get_installed_app_version(engines.dut, P4SamplingConsts.APP_NAME)
        with allure.step('Upgrade p4-sampling from version {} to version: {}'.format(current_version,
                                                                                     P4SamplingConsts.UPGRADE_TARGET_VERSION)):
            SonicAppExtensionCli.upgrade_app(engines.dut, P4SamplingConsts.APP_NAME,
                                             P4SamplingConsts.UPGRADE_TARGET_VERSION, True)
        with allure.step('Run basic test after upgrade to version {}'.format(P4SamplingConsts.UPGRADE_TARGET_VERSION)):
            self.run_p4_smapling_basic_test(engines, table_params, topology_obj, interfaces)
        with allure.step('Upgrade p4-sampling from version {} to version: {}'.format(P4SamplingConsts.UPGRADE_TARGET_VERSION,
                                                                                     current_version)):
            SonicAppExtensionCli.upgrade_app(engines.dut, P4SamplingConsts.APP_NAME, current_version, True)
        with allure.step('Run basic test after upgrade to version {}'.format(current_version)):
            self.run_p4_smapling_basic_test(engines, table_params, topology_obj, interfaces)

    @staticmethod
    def get_ingress_ports(indices, port_entries):
        """
        get the ingress port for the port entries
        :param indices: index list to indicate from which port entries to get the ingress port
        :param port_entries: port entry params
        :return: list of ingress port
        example: input: {'Ethernet124 0x0001/0xffff':
                          {'action': 'Ethernet0 1c:34:da:16:68:00 0c:42:a1:4b:0b:6c 50.0.0.1 50.0.0.2 40 True 300',
                          'priority': 1, 'match_chksum': '0x0001', 'mismatch_chksum': 0}, ...}
                 output:['Ethernet124', ...]
        """
        ingress_ports = []
        for index in indices:
            port_entry_key = list(port_entries.keys())[index]
            ingress_port = port_entry_key.split()[0]
            ingress_ports.append(ingress_port)
        return ingress_ports

    @staticmethod
    def get_mirror_ports(indices, table_params):
        """
        get mirror ports for port entries and flow entries
        :param indices: index list to indicate from which port entries and flow entries to get the mirror port
        :param table_params: table params which include the port entry params and flow entry params
        :return: list of port
        """
        mirror_ports = []
        port_entries = table_params.port_entry
        flow_entries = table_params.flow_entry
        for index in indices:
            port_entry_action = port_entries[list(port_entries.keys())[index]].action
            mirror_port = port_entry_action.split()[0]
            mirror_ports.append(mirror_port)
            flow_entry_action = flow_entries[list(flow_entries.keys())[index]].action
            mirror_port = flow_entry_action.split()[0]
            mirror_ports.append(mirror_port)
        return list(set(mirror_ports))

    @staticmethod
    def config_breakout_mode_and_expect_log(engine_dut, topology_obj, port_list, loganalyzer):
        """
        config breakout mode for port in port list
        :param engine_dut: ssh engine object
        :param topology_obj: topology object
        :param port_list: port list
        :return: None
        """
        loganalyzer.expect_regex = [DPB_ERR_MSG]
        for port in port_list:
            conf = breakout_helpers.get_breakout_mode(engine_dut, topology_obj.players['dut']['cli'], [port])
            with loganalyzer:
                SonicInterfaceCli.configure_dpb_on_ports(engine_dut, conf)

    @staticmethod
    def verify_traffic_received(topology_obj, engine_dut, port_traffic_params_list, flow_traffic_params_list):
        """
        verify the traffic can be received
        :param topology_obj: topology_obj fixture object
        :param engine_dut: dut engine ssh object
        :param port_traffic_params_list: traffic params used to send traffic for the port table
        :param flow_traffic_params_list: traffic params used to send traffic for the flow table
        :return: None
        """
        traffic_send_duration = 1
        pkt_count = int(traffic_send_duration / P4SamplingConsts.TRAFFIC_INTERVAL)
        SonicInterfaceCli.clear_counters(engine_dut)
        logger.info('sleep for {} second to wait for the the traffic can be received'.format(traffic_send_duration))
        time.sleep(traffic_send_duration)
        logger.info("Print the acl value get from the sdk for debug purpose")
        engine_dut.run_cmd("docker exec -i syncd bash -c 'sx_api_flex_acl_dump.py'")
        P4SamplingUtils.verify_port_table_recv_traffic(topology_obj, port_traffic_params_list, ">=", pkt_count)
        P4SamplingUtils.verify_flow_table_recv_traffic(topology_obj, flow_traffic_params_list, ">=", pkt_count)

    @staticmethod
    def verify_traffic_lossed(topology_obj, engine_dut, port_traffic_params_list, flow_traffic_params_list):
        """
        verify the traffic can not be received
        :param topology_obj: topology_obj fixture object
        :param engine_dut: dut engine ssh object
        :param port_traffic_params_list: traffic params used to send traffic for the port table
        :param flow_traffic_params_list: traffic params used to send traffic for the flow table
        :return: None
        """
        traffic_send_duration = 1
        logger.info("Clear the Interface counters before send traffic")
        SonicInterfaceCli.clear_counters(engine_dut)
        logger.info('sleep for {} second to wait for the the traffic can not be received'.format(traffic_send_duration))
        time.sleep(traffic_send_duration)
        logger.info("Print the acl value get from the sdk for debug purpose")
        engine_dut.run_cmd("docker exec -i syncd bash -c 'sx_api_flex_acl_dump.py'")
        P4SamplingUtils.verify_port_table_recv_traffic(topology_obj, port_traffic_params_list, "==", 0)
        P4SamplingUtils.verify_flow_table_recv_traffic(topology_obj, flow_traffic_params_list, "==", 0)

    @staticmethod
    def verify_entries_hit(engine_dut, port_entry_keys, flow_entry_keys):
        """
        verify packets can be countered
        :param engine_dut: dut engine ssh object
        :param port_entry_keys: port entry key list
        :param flow_entry_keys: flow entry key list
        :return: None
        """
        logger.info("Clear the entry counters before send traffic")
        P4SamplingCli.clear_all_table_counters(engine_dut)
        time.sleep(P4SamplingConsts.COUNTER_REFRESH_INTERVAL)
        pkt_count = int(1 / P4SamplingConsts.TRAFFIC_INTERVAL)
        P4SamplingUtils.verify_entry_counter(engine_dut, PORT_TABLE_NAME, port_entry_keys, pkt_count)
        P4SamplingUtils.verify_entry_counter(engine_dut, FLOW_TABLE_NAME, flow_entry_keys, pkt_count)

    @staticmethod
    def verify_entries_missed(engine_dut, port_entry_keys, flow_entry_keys):
        """
        verify packets can not be countered
        :param engine_dut: dut engine ssh object
        :param port_entry_keys: port entry key list
        :param flow_entry_keys: flow entry key list
        :return: None
        """
        logger.info("Clear the entry counters before send traffic")
        P4SamplingCli.clear_table_counters(engine_dut, PORT_TABLE_NAME)
        P4SamplingCli.clear_table_counters(engine_dut, FLOW_TABLE_NAME)
        time.sleep(P4SamplingConsts.COUNTER_REFRESH_INTERVAL)
        pkt_count = 0
        P4SamplingUtils.verify_entry_counter(engine_dut, PORT_TABLE_NAME, port_entry_keys, pkt_count)
        P4SamplingUtils.verify_entry_counter(engine_dut, FLOW_TABLE_NAME, flow_entry_keys, pkt_count)

    @staticmethod
    def shutdown_ports(engine_dut, ports):
        """
        shut down the ports
        :param engine_dut: dut engine ssh object
        :param ports: list of port to be shutdown
        :return:
        """
        for port in ports:
            SonicInterfaceCli.disable_interface(engine_dut, port)
        SonicGeneralCli.check_link_state(engine_dut, ports, expected_status="down")

    @staticmethod
    def startup_ports(engine_dut, ports):
        """
        startup ports
        :param engine_dut: dut engine ssh object
        :param ports: list of port to be startup
        :return: None
        """
        for port in ports:
            SonicInterfaceCli.enable_interface(engine_dut, port)
        SonicGeneralCli.check_link_state(engine_dut, ports)

    @staticmethod
    def remove_entries(engine_dut, table_params):
        for port_entry_key in table_params.port_entry.keys():
            P4SamplingCli.delete_entry_from_table(
                engine_dut, PORT_TABLE_NAME, 'key {}'.format(port_entry_key))
        for flow_entry_key in table_params.flow_entry.keys():
            P4SamplingCli.delete_entry_from_table(
                engine_dut, FLOW_TABLE_NAME, 'key {}'.format(flow_entry_key))

    @staticmethod
    def add_entries(engine_dut, table_params):
        port_entry = table_params.port_entry
        for key in port_entry.keys():
            params = port_entry[key]
            port_table_entry_params = 'key {} action {} {} priority {}'.format(key, ACTION_NAME, params.action,
                                                                               params.priority)
            P4SamplingCli.add_entry_to_table(
                engine_dut, PORT_TABLE_NAME, port_table_entry_params)
        flow_entry = table_params.flow_entry
        for key in flow_entry.keys():
            params = flow_entry[key]
            flow_table_entry_params = 'key {} action {} {} priority {}'.format(
                key, ACTION_NAME, params.action, params.priority)
            P4SamplingCli.add_entry_to_table(
                engine_dut, FLOW_TABLE_NAME, flow_table_entry_params)

    @staticmethod
    def get_port_list(topology_obj):
        ports = topology_obj.ports
        return [ports['dut-ha-1'], ports['dut-ha-2'], ports['dut-hb-1'], ports['dut-hb-2']]

    @staticmethod
    def disable_enable_feature_state(engine, feature_name, times):
        """
        This method to set feature state on the sonic switch
        :param engine: ssh engine object
        :param feature_name: the feature name
        """
        cmd_list = []
        for i in range(times):
            cmd_list.append('sudo config feature state {} disabled'.format(feature_name))
            cmd_list.append('sudo config feature state {} enabled'.format(feature_name))
        return engine.run_cmd_set(cmd_list)

    @staticmethod
    def run_p4_smapling_basic_test(engines, table_params, topology_obj, interfaces):
        """
        run basic p4_sampling test
        :param engines: engines fixture object
        :param table_params: table_params fixture object
        :param topology_obj: topology_obj fixture object
        :param interfaces: interfaces fixture object
        """

        with allure.step('Get entries in table {} and {}, verify the entries are added correctly'.format(
                P4SamplingConsts.PORT_TABLE_NAME, P4SamplingConsts.FLOW_TABLE_NAME)):
            with allure.step('Verify the entries are added for {}'.format(P4SamplingConsts.PORT_TABLE_NAME)):
                P4SamplingUtils.verify_table_entry(engines.dut, P4SamplingConsts.PORT_TABLE_NAME,
                                                   table_params.port_entry)
            with allure.step('Verify the entries are added for {}'.format(P4SamplingConsts.FLOW_TABLE_NAME)):
                P4SamplingUtils.verify_table_entry(engines.dut, P4SamplingConsts.FLOW_TABLE_NAME,
                                                   table_params.flow_entry)

        with allure.step("Verify the the packet that match entry key can be counted and mirrored"):
            with allure.step("Clear statistics and counters"):
                P4SamplingUtils.clear_statistics(engines.dut)
            with allure.step("Send packets and verify"):
                count = 5
                P4SamplingUtils.verify_traffic_hit(topology_obj, engines, interfaces, table_params, count, count)

        with allure.step("Verifying that the packet that does not match entry key will not be counted"):
            with allure.step("Clear statistics and counters"):
                P4SamplingUtils.clear_statistics(engines.dut)
            with allure.step("Send packets and verify"):
                count = 5
                expect_count = 0
                P4SamplingUtils.verify_traffic_miss(topology_obj, engines, interfaces, table_params, count,
                                                    expect_count)
