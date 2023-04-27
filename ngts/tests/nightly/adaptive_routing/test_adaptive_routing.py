import logging

import pytest

from tests.common.plugins.allure_wrapper import allure_step_wrapper as allure
from ngts.tests.nightly.adaptive_routing.constants import ArConsts
from ngts.helpers.adaptive_routing_helper import ArHelper
from ngts.helpers.vxlan_helper import validate_dest_files_exist_in_tarball, get_tech_support_tar_file

logger = logging.getLogger()
allure.logger = logger


class TestArBasic:

    @pytest.fixture(autouse=True)
    def setup_param(self, topology_obj, engines, cli_objects, interfaces, players, dut_ha_1_mac, ha_dut_1_mac,
                    ar_base_config_default_vrf, set_config_db_split_mode):
        self.topology_obj = topology_obj
        self.engines = engines
        self.interfaces = interfaces
        self.players = players
        self.cli_objects = cli_objects
        self.ingress_port = self.interfaces.dut_ha_1
        self.dut_mac = dut_ha_1_mac
        self.ha_dut_1_mac = ha_dut_1_mac
        self.hash_tx_port = ar_base_config_default_vrf
        self.ar_helper = ArHelper()
        self.expected_tx_port = self.ar_helper.get_received_port(self.interfaces, self.hash_tx_port)
        self.tx_ports = [interfaces.dut_hb_1, interfaces.dut_hb_2]

    def test_ar_default_profile_configuration(self):
        """
        This test case will get AR configuration from CLI and compare profile0 default values with predefined
        golden" profile0 dictionary
        """
        # Get show ar config output
        show_ar_dict = self.ar_helper.get_ar_configuration(self.cli_objects, [ArConsts.GOLDEN_PROFILE0])
        # Compare output with golden profile values
        for profile_key, key_value in show_ar_dict[ArConsts.AR_PROFILE_GLOBAL][ArConsts.GOLDEN_PROFILE0].items():
            assert key_value == ArConsts.GOLDEN_PROFILE0_PARAMETERS[profile_key], "Golden profile default params did " \
                                                                                  "not match"

    def test_ar_custom_profile_configuration(self):
        """
        This test case will get AR configuration from CLI and compare custom profile values with params read from
        custom_profile.json file
        """
        # Get show ar config output
        show_ar_dict = self.ar_helper.get_ar_configuration(self.cli_objects, [ArConsts.GOLDEN_PROFILE0,
                                                                              ArConsts.CUSTOM_PROFILE_NAME])
        # Compare output with custom profile values
        for profile_key, key_value in show_ar_dict[ArConsts.AR_PROFILE_GLOBAL][ArConsts.CUSTOM_PROFILE_NAME].items():
            assert key_value == ArConsts.CUSTOM_PROFILE0_PARAMETERS[profile_key], "Custom profile default params did " \
                                                                                  "not match"

    def test_ar_buffer_grading_default_parameters(self):
        """
        This test case will send RoCEv2 packets to ports in ECMP group where ports has same link utilization and buffer
        grading parameters. Traffic must be split between all ports in ECMP group equally (some packet count deviation
        could be present in ports counters due to AR algorithms).
        """
        # Get interface counters before send RoCE v2 traffic
        iface_rx_count_before = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')
        # Send RoCE v2 traffic
        with allure.step(f'HA send {ArConsts.PACKET_NUM_1000} TC3 RoCEv2 with AR flag packets'):
            self.ar_helper.validate_roce_v2_pkts_traffic(players=self.players,
                                                         interfaces=self.interfaces,
                                                         ha_dut_1_mac=self.ha_dut_1_mac,
                                                         dut_ha_1_mac=self.dut_mac,
                                                         sender_count=ArConsts.PACKET_NUM_1000,
                                                         )
        # Get interface counters after send RoCE v2 traffic
        iface_rx_count_after = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')

        # Verify that traffic was split between ports in ecmp group
        for tx_port in self.tx_ports:
            assert iface_rx_count_after[tx_port] >= iface_rx_count_before[tx_port] + \
                ArConsts.PACKET_NUM_1000 // len(self.tx_ports) - 100 // len(self.tx_ports), \
                f"Traffic has not been split between ECMP group: {tx_port} before {iface_rx_count_before} <= " \
                f"{ArConsts.PACKET_NUM_1000 // len(self.tx_ports) - 100 // len(self.tx_ports)}"

    def test_ar_link_utilization_grading(self, config_ecmp_ports_speed_as_10G):
        """
        This test case will send RoCEv2 packets to ports in ECMP group where first port has 1% link utilization grading
        set and second has 70% configured. All traffic has to go through the port with higher link utilization set.
        """
        # Get AR port which will be set to 1% link utilization
        tx_ports_copy = self.tx_ports[:]
        tx_ports_copy.remove(self.expected_tx_port)
        # Configure AR port wit 1% link utilization
        with allure.step(f'Configure link utilization grade for port {tx_ports_copy} '
                         f'to 1 percent'):
            self.ar_helper.enable_ar_port(self.cli_objects, tx_ports_copy, port_util_percent=ArConsts.PORT_UTIL_PERCENT,
                                          restart_swss=True)
            # Check if all dockers are up
            self.cli_objects.dut.general.verify_dockers_are_up()
            show_ports_config = self.ar_helper.get_ar_configuration(
                self.cli_objects, [ArConsts.GOLDEN_PROFILE0])[ArConsts.AR_PORTS_GLOBAL]
            assert int(show_ports_config[tx_ports_copy[0]]) == ArConsts.PORT_UTIL_PERCENT, \
                f"Link utilization for port {tx_ports_copy[0]} did not change to {ArConsts.AR_PORTS_GLOBAL}"
        # Get interface counters before send RoCE v2 traffic
        iface_rx_count_before = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')
        # Send RoCE v2 traffic
        with allure.step(f'HA send {ArConsts.PACKET_NUM_1000} TC3 RoCEv2 with AR flag packets'):
            self.ar_helper.validate_roce_v2_pkts_traffic(players=self.players,
                                                         interfaces=self.interfaces,
                                                         ha_dut_1_mac=self.ha_dut_1_mac,
                                                         dut_ha_1_mac=self.dut_mac,
                                                         sender_count=ArConsts.PACKET_NUM_1000,
                                                         sendpfast=True,
                                                         mbps=100000,
                                                         loop=ArConsts.PACKET_NUM_10000000,
                                                         timeout=5
                                                         )
        # Get interface counters after send RoCE v2 traffic
        iface_rx_count_after = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')
        # Verify that traffic goes to port with higher port utilization % set to AR port

        port_with_higher_link_util_counter = \
            (iface_rx_count_after[self.expected_tx_port] - iface_rx_count_before[self.expected_tx_port] /
             ArConsts.PACKET_NUM_10000000) * 100
        port_with_lower_link_util_counter = \
            (iface_rx_count_after[tx_ports_copy[0]] - iface_rx_count_before[tx_ports_copy[0]] /
             ArConsts.PACKET_NUM_10000000) * 100
        assert port_with_higher_link_util_counter - port_with_lower_link_util_counter > 10, \
            f"Traffic has not been shift from port {tx_ports_copy[0]} with lower utilization to port " \
            f"{self.expected_tx_port} with higher utilization grading"

        with allure.step(f'Return default ar port utilization percentage'):
            self.ar_helper.enable_ar_port(self.cli_objects, tx_ports_copy,
                                          port_util_percent=ArConsts.PORT_UTIL_DEFAULT_PERCENT, restart_swss=True)
            # Check if all dockers are up
            self.cli_objects.dut.general.verify_dockers_are_up()
            show_ports_config = self.ar_helper.get_ar_configuration(
                self.cli_objects, [ArConsts.GOLDEN_PROFILE0])[ArConsts.AR_PORTS_GLOBAL]
            assert int(show_ports_config[tx_ports_copy[0]]) == ArConsts.PORT_UTIL_DEFAULT_PERCENT, \
                f"Link utilization for port {tx_ports_copy[0]} did not change to {ArConsts.PORT_UTIL_DEFAULT_PERCENT}"

    def test_ar_buffer_grading_with_shaper(self, configure_port_shaper):
        """
        This test case will send RoCEv2 packets to ports in ECMP group where first port has limited buffer grading.
        All traffic has to go through the port with higher buffer grading set.
        """
        # Get interface counters before send RoCE v2 traffic
        iface_rx_count_before = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')

        # Send RoCE v2 traffic
        with allure.step(f'HA send {ArConsts.PACKET_NUM_1000} TC3 RoCEv2 with AR flag packets'):
            self.ar_helper.validate_roce_v2_pkts_traffic(players=self.players,
                                                         interfaces=self.interfaces,
                                                         ha_dut_1_mac=self.ha_dut_1_mac,
                                                         dut_ha_1_mac=self.dut_mac,
                                                         sender_count=ArConsts.PACKET_NUM_1000,
                                                         )

        # Get interface counters after send RoCE v2 traffic
        iface_rx_count_after = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')
        # Verify that traffic goes to port with higher port utilization % set to AR port
        assert iface_rx_count_after[self.expected_tx_port] >= iface_rx_count_before[self.expected_tx_port] + \
            ArConsts.PACKET_NUM_1000 - ArConsts.LO_THRESHOLD_PROFILE0 * 1.3, \
            f"RoCEv2 with AR flags packets did not move to the port {self.expected_tx_port}"

    def test_ar_custom_profile(self, request):
        """
        This test case will enable custom profile and send RoCEv2 packets to ports in ECMP group where ports has same
        link utilization and buffer grading parameters. Traffic must be split between all ports in ECMP group equally
        (some packet count deviation could be present in ports counters due to AR algorithms).
        """
        # Enable AR custom profile
        with allure.step(f'Enable {ArConsts.CUSTOM_PROFILE_NAME} profile and return to default at the end of the test'):
            self.ar_helper.enable_ar_profile(self.cli_objects, ArConsts.CUSTOM_PROFILE_NAME, restart_swss=True,
                                             request=request)

            # Check if all dockers are up
            self.cli_objects.dut.general.verify_dockers_are_up()
            # Get show ar config output
            show_ar_dict = self.ar_helper.get_ar_configuration(self.cli_objects, [ArConsts.CUSTOM_PROFILE_NAME])
            assert show_ar_dict[ArConsts.AR_GLOBAL][ArConsts.AR_ACTIVE_PROFILE] == ArConsts.CUSTOM_PROFILE_NAME, \
                f"Active AR profile is {show_ar_dict[ArConsts.AR_GLOBAL][ArConsts.AR_ACTIVE_PROFILE]} but must be " \
                f"{ArConsts.CUSTOM_PROFILE_NAME}"

        # Get interface counters before send RoCE v2 traffic
        iface_rx_count_before = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')
        # Send RoCE v2 traffic
        with allure.step(f'HA send {ArConsts.PACKET_NUM_1000} TC3 RoCEv2 with AR flag packets'):
            self.ar_helper.validate_roce_v2_pkts_traffic(players=self.players,
                                                         interfaces=self.interfaces,
                                                         ha_dut_1_mac=self.ha_dut_1_mac,
                                                         dut_ha_1_mac=self.dut_mac,
                                                         sender_count=ArConsts.PACKET_NUM_1000,
                                                         )
        # Get interface counters after send RoCE v2 traffic
        iface_rx_count_after = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')

        # Verify that traffic was split between ports in ecmp group
        for tx_port in self.tx_ports:
            assert iface_rx_count_after[tx_port] >= iface_rx_count_before[tx_port] + \
                ArConsts.PACKET_NUM_1000 // len(self.tx_ports) - 100 // len(self.tx_ports), \
                f"Traffic has not been split between ECMP group: {tx_port} before {iface_rx_count_before} <= " \
                f"{ArConsts.PACKET_NUM_1000 // len(self.tx_ports) - 100 // len(self.tx_ports)}"

    def test_ar_show_techsupport(self):
        """
        This test will check if dump/doai.gz present after show techsupport and is not empty
        """
        with allure.step('Generate show techsupport'):
            tar_file = get_tech_support_tar_file(self.engines)
        with allure.step('Check if doai tar file available'):
            validate_dest_files_exist_in_tarball(tar_file, ArConsts.AR_DUMP_FILE_NAME)
        with allure.step(f'Check if {ArConsts.AR_DUMP_FILE_NAME} not empty'):
            pass

    def test_ar_negative(self, config_vlan_intf, config_lag):
        """
        This test case will check negative scenarios for configuring AR feature
        """
        with allure.step('Validate AR handle enable ar function before doAI service enabled'):
            self.ar_helper.verify_enable_ar_before_doai_service_start(self.cli_objects)

        with allure.step('Validate AR prevent configuring with a non exist user defined profile'):
            self.ar_helper.verify_config_non_exist_profile(self.cli_objects)

        with allure.step('Validate AR prevent configuring on a non exist port'):
            self.ar_helper.verify_config_ar_at_non_exist_port(self.cli_objects)

        with allure.step('Validate AR prevent configuring on vlan interface'):
            self.ar_helper.verify_config_ar_on_vlan_intf(self.cli_objects)

        with allure.step('Validate AR prevent configuring on lag interface'):
            self.ar_helper.verify_config_ar_on_lag_intf_and_lag_member(self.cli_objects, self.topology_obj)

        with allure.step('Validate AR prevent configuring on mgmt interface'):
            self.ar_helper.verify_config_ar_on_mgmt_port(self.cli_objects)

        with allure.step('Validate AR prevent configuring invalid link utilization value'):
            self.ar_helper.verify_config_ar_invalid_link_utilization(self.cli_objects, self.interfaces)

    def test_ar_with_reboot(self, configure_port_shaper, get_reboot_type):
        """
        This test case will send RoCEv2 packets to ports in ECMP group where first port has limited buffer grading.
        All traffic has to go through the port with higher buffer grading set. Than random reboot will be performed and
        traffic will be send one mere time after reboot.
        """

        # Get interface counters before send RoCE v2 traffic
        iface_rx_count_before = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')

        # Send RoCE v2 traffic
        with allure.step(f'HA send {ArConsts.PACKET_NUM_1000} TC3 RoCEv2 with AR flag packets'):
            self.ar_helper.validate_roce_v2_pkts_traffic(players=self.players,
                                                         interfaces=self.interfaces,
                                                         ha_dut_1_mac=self.ha_dut_1_mac,
                                                         dut_ha_1_mac=self.dut_mac,
                                                         sender_count=ArConsts.PACKET_NUM_1000,
                                                         )

        # Get interface counters after send RoCE v2 traffic
        iface_rx_count_after = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')
        # Verify that traffic goes to port with higher port utilization % set to AR port
        assert iface_rx_count_after[self.expected_tx_port] >= iface_rx_count_before[self.expected_tx_port] + \
            ArConsts.PACKET_NUM_1000 - ArConsts.LO_THRESHOLD_PROFILE0 * 1.3, \
            f"RoCEv2 with AR flags packets did not move to the port {self.expected_tx_port}"

        # Save configuration before reboot
        self.cli_objects.dut.general.save_configuration()
        with allure.step(f'Randomly choose {get_reboot_type} and do it'):
            self.cli_objects.dut.general.reboot_reload_flow(r_type=get_reboot_type, topology_obj=self.topology_obj)

        # Get interface counters before send RoCE v2 traffic after reboot
        iface_rx_count_before = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')

        # Send RoCE v2 traffic
        with allure.step(f'HA send {ArConsts.PACKET_NUM_1000} TC3 RoCEv2 with AR flag packets'):
            self.ar_helper.validate_roce_v2_pkts_traffic(players=self.players,
                                                         interfaces=self.interfaces,
                                                         ha_dut_1_mac=self.ha_dut_1_mac,
                                                         dut_ha_1_mac=self.dut_mac,
                                                         sender_count=ArConsts.PACKET_NUM_1000,
                                                         )

        # Get interface counters after send RoCE v2 traffic
        iface_rx_count_after = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')
        # Verify that traffic goes to port with higher port utilization % set to AR port
        assert iface_rx_count_after[self.expected_tx_port] >= iface_rx_count_before[self.expected_tx_port] + \
            ArConsts.PACKET_NUM_1000 - ArConsts.LO_THRESHOLD_PROFILE0 * 1.3, \
            f"RoCEv2 with AR flags packets did not move to the port {self.expected_tx_port} after " \
            f"{get_reboot_type} performed"

    def test_ar_with_remove_add_doai_app(self):
        """
        This test case will remove doAI application and installed to same version and traffic verification performed.
        Traffic verification performed.
        """

        try:
            with allure.step(f'Remove amd install doAI'):
                # Get current doAI version
                doai_version = self.cli_objects.dut.app_ext.get_installed_app_version(ArConsts.DOAI_CONTAINER_NAME)
                # Uninstall doAI
                self.cli_objects.dut.app_ext.uninstall_app(ArConsts.DOAI_CONTAINER_NAME)
                # Install doAI with the same version
                self.cli_objects.dut.app_ext.install_app(ArConsts.DOAI_CONTAINER_NAME, version=doai_version)
                # Save configuration after install doAI
                self.cli_objects.dut.general.save_configuration()

            # Get interface counters before send RoCE v2 traffic after save configuration
            iface_rx_count_before = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')

            # Send RoCE v2 traffic
            with allure.step(f'HA send {ArConsts.PACKET_NUM_1000} TC3 RoCEv2 with AR flag packets'):
                self.ar_helper.validate_roce_v2_pkts_traffic(players=self.players,
                                                             interfaces=self.interfaces,
                                                             ha_dut_1_mac=self.ha_dut_1_mac,
                                                             dut_ha_1_mac=self.dut_mac,
                                                             sender_count=ArConsts.PACKET_NUM_1000,
                                                             )

            # Get interface counters after send RoCE v2 traffic
            iface_rx_count_after = self.ar_helper.get_interfaces_counters(self.cli_objects, self.tx_ports, 'TX_OK')

            # Verify that traffic was split between ports in ecmp group
            for tx_port in self.tx_ports:
                assert iface_rx_count_after[tx_port] >= iface_rx_count_before[tx_port] + \
                    ArConsts.PACKET_NUM_1000 // len(self.tx_ports) - 100 // len(self.tx_ports), \
                    f"Traffic has not been split between ECMP group: {tx_port} before {iface_rx_count_before} <= " \
                    f"{ArConsts.PACKET_NUM_1000 // len(self.tx_ports) - 100 // len(self.tx_ports)}"

        finally:
            installed_version = self.cli_objects.dut.app_ext.get_installed_app_version(ArConsts.DOAI_CONTAINER_NAME)
            if installed_version != doai_version:
                self.cli_objects.dut.app_ext.upgrade_app(ArConsts.DOAI_CONTAINER_NAME, version=doai_version,
                                                         allow_downgrade=True)


class TestArMaxPort:

    @pytest.fixture(autouse=True)
    def setup_param(self, topology_obj, engines, cli_objects, interfaces, players, ar_max_ports_l3_config,
                    ar_config_for_max_port):
        self.topology_obj = topology_obj
        self.engines = engines
        self.interfaces = interfaces
        self.players = players
        self.cli_objects = cli_objects
        self.ar_helper = ArHelper()
        self.dut_ports = ar_config_for_max_port

    def test_ar_max_port(self, get_reboot_type):
        """
        This test will check if AR can be configured at DUT all ports and be persistent after reboot
        """
        with allure.step('Verify port configuration correctness'):
            show_ports_config = self.ar_helper.get_ar_configuration(self.cli_objects,
                                                                    [ArConsts.GOLDEN_PROFILE0])[ArConsts.
                                                                                                AR_PORTS_GLOBAL]
            for port in self.dut_ports:
                assert show_ports_config[port], f"Port {port} has not been added to AR config"
                assert int(show_ports_config[port]) == ArConsts.PORT_UTIL_DEFAULT_PERCENT, \
                    f"Port {port} has not been configured with {ArConsts.PORT_UTIL_DEFAULT_PERCENT} link util usage"

        with allure.step('Save changes'):
            self.ar_helper.config_save_reload(self.cli_objects, self.topology_obj, reload_force=True)

        with allure.step(f'Randomly choose {get_reboot_type} and do it'):
            self.cli_objects.dut.general.reboot_reload_flow(r_type=get_reboot_type, topology_obj=self.topology_obj)

        with allure.step(f'Verify profile {ArConsts.GOLDEN_PROFILE0} correctness after {get_reboot_type}'):
            # Get show ar config output
            show_ar_dict = self.ar_helper.get_ar_configuration(self.cli_objects, [ArConsts.GOLDEN_PROFILE0])
            # Compare output with golden profile values
            for profile_key, key_value in show_ar_dict[ArConsts.AR_PROFILE_GLOBAL][ArConsts.GOLDEN_PROFILE0].items():
                assert key_value == ArConsts.GOLDEN_PROFILE0_PARAMETERS[profile_key], \
                    f"Golden profile default params did not match after reboot {get_reboot_type}"

        with allure.step(f'Verify port configuration correctness after {get_reboot_type}'):
            show_ports_config = self.ar_helper.get_ar_configuration(self.cli_objects,
                                                                    [ArConsts.GOLDEN_PROFILE0])[ArConsts.
                                                                                                AR_PORTS_GLOBAL]
            for port in self.dut_ports:
                assert show_ports_config[port], f"Port {port} not in ar config after {get_reboot_type}"
                assert int(show_ports_config[port]) == ArConsts.PORT_UTIL_DEFAULT_PERCENT, \
                    f"Port {port} has not been configured with {ArConsts.PORT_UTIL_DEFAULT_PERCENT} link util usage"
