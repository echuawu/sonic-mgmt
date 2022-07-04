import allure
import logging
import random
import re
import time
import pytest
import json

from ngts.cli_util.cli_parsers import generic_sonic_output_parser


logger = logging.getLogger()

IFACES_HEADERS_OFSET = 0
IFACES_LEN_OFSET = 1
IFACES_DATA_OFSET_FROM_START = 2

INTERFACE_STATUS_TEMPLATE = {'Interface': 'Ethernet',
                             'Lanes': r'\d,\d,\d,\d',
                             'Speed': '100G',
                             'MTU': '9100',
                             'FEC': 'N/A',
                             'Alias': 'etp',
                             'Vlan': 'routed',
                             'Oper': 'up',
                             'Admin': 'up',
                             'Type': r'N/A|QSFP28 or later',  # TODO update when the issue 3096166 will be resolved
                             'Asym PFC': 'N/A'}

INTERFACE_COUNTERS_TEMPLATE = {'IFACE': 'Ethernet',
                               'STATE': r'\w',
                               'RX_OK': r'\d+',
                               'RX_BPS': r'\d+.\d+ B/s',
                               'RX_UTIL': r'\d+.\d+%',
                               'RX_ERR': r'\d+',
                               'RX_DRP': r'\d+',
                               'RX_OVR': r'\d+',
                               'TX_OK': r'\d+',
                               'TX_BPS': r'\d+.\d+ B/s',
                               'TX_UTIL': r'\d+.\d+%',
                               'TX_ERR': r'\d+',
                               'TX_DRP': r'\d+',
                               'TX_OVR': r'\d+'}

INTERFACE_COUNTERS_ERRORS_TEMPLATE = {'IFACE': 'Ethernet',
                                      'STATE': r'\w',
                                      'RX_ERR': r'\d+',
                                      'RX_DRP': r'\d+',
                                      'RX_OVR': r'\d+',
                                      'TX_ERR': r'\d+',
                                      'TX_DRP': r'\d+',
                                      'TX_OVR': r'\d+'}

INTERFACE_COUNTERS_RATES_TEMPLATE = {'IFACE': 'Ethernet',
                                     'STATE': r'\w',
                                     'RX_OK': r'\d+',
                                     'RX_BPS': r'\d+.\d+ B/s',
                                     'RX_PPS': r'\d+.\d+/s',
                                     'RX_UTIL': r'\d+.\d+%',
                                     'TX_OK': r'\d+',
                                     'TX_BPS': r'\d+.\d+ B/s',
                                     'TX_PPS': r'\d+.\d+/s',
                                     'TX_UTIL': r'\d+.\d+%'}

INTERFACE_COUNTERS_DETAILED_TEMPLATE = [
    r'Packets Received 64 Octets.+ \d+',
    r'Packets Received 65-127 Octets.+ \d+',
    r'Packets Received 128-255 Octets.+ \d+',
    r'Packets Received 256-511 Octets.+ \d+',
    r'Packets Received 512-1023 Octets.+ \d+',
    r'Packets Received 1024-1518 Octets.+ \d+',
    r'Packets Received 1519-2047 Octets.+ \d+',
    r'Packets Received 2048-4095 Octets.+ \d+',
    r'Packets Received 4096-9216 Octets.+ \d+',
    r'Packets Received 9217-16383 Octets.+ N/A',
    r'Total Packets Received Without Errors.+ \d+',
    r'Unicast Packets Received.+ \d+',
    r'Multicast Packets Received.+ \d+',
    r'Broadcast Packets Received.+ \d+',
    r'Jabbers Received.+ \d+',
    r'Fragments Received.+ \d+',
    r'Undersize Received.+ \d+',
    r'Overruns Received.+ N/A',
    r'Packets Transmitted 64 Octets.+ \d+',
    r'Packets Transmitted 65-127 Octets.+ \d+',
    r'Packets Transmitted 128-255 Octets.+ \d+',
    r'Packets Transmitted 256-511 Octets.+ \d+',
    r'Packets Transmitted 512-1023 Octets.+ \d+',
    r'Packets Transmitted 1024-1518 Octets.+ \d+',
    r'Packets Transmitted 1519-2047 Octets.+ \d+',
    r'Packets Transmitted 2048-4095 Octets.+ \d+',
    r'Packets Transmitted 4096-9216 Octets.+ \d+',
    r'Packets Transmitted 9217-16383 Octets.+ N/A',
    r'Total Packets Transmitted Successfully.+ \d+',
    r'Unicast Packets Transmitted.+ \d+',
    r'Multicast Packets Transmitted.+ \d+',
    r'Broadcast Packets Transmitted.+ \d+',
    r'Time Since Counters Last Cleared.+ None'
]

INTERFACE_DESCRIPTION_TEMPLATE = {'Interface': 'Ethernet',
                                  'Oper': 'up',
                                  'Admin': 'up',
                                  'Alias': 'eth',
                                  'Description': 'N/A'}

INTERFACE_ALIAS_TEMPLATE = {'Name': 'Ethernet',
                            'Alias': 'etp'}


class TestBfSanity:

    @pytest.fixture(autouse=True)
    def setup(self, engines, cli_objects, topology_obj, platform_params, dut_mac):
        self.dut = engines.dut
        self.cli_objects = cli_objects
        self.dut_mac = dut_mac
        self.ports_list = topology_obj.players_all_ports['dut']
        self.random_iface = random.choice(self.ports_list)
        self.platform_params = platform_params

    def test_check_config_db_json(self):
        """
        This test will check generation of config_db.json file by sonic-cfggen
        :return: raise assertion error in case when test failed
        """
        generated_config = json.loads(self.dut.run_cmd('sudo sonic-cfggen -H --print-data'))

        with allure.step('Checking generated DUT mac'):
            generated_mac = generated_config['DEVICE_METADATA']['localhost']['mac']
            assert self.dut_mac == generated_mac, \
                f'Incorrect MAC address: {generated_mac} generated by sonic-cfggen, expected: {self.dut_mac}'

        with allure.step('Checking generated DUT platform'):
            generated_platform = generated_config['DEVICE_METADATA']['localhost']['platform']
            assert self.platform_params.platform == generated_platform, \
                f'Incorrect platform: {generated_platform} generated by sonic-cfggen'

        # TODO: uncomment validation below once DPU will support all values
        # with allure.step('Checking generated DUT subtype'):
        #     generated_subtype = generated_config['DEVICE_METADATA']['localhost']['subtype']
        #     assert 'appliance' == generated_subtype, \
        #         f'Incorrect subtype: {generated_subtype} generated by sonic-cfggen'
        #
        # with allure.step('Checking generated DUT type'):
        #     generated_type = generated_config['DEVICE_METADATA']['localhost']['type']
        #     assert 'sonichost' == generated_type, f'Incorrect type: {generated_type} generated by sonic-cfggen'
        #
        # with allure.step('Checking generated DUT switch_type'):
        #     generated_switch_type = generated_config['DEVICE_METADATA']['localhost']['switch_type']
        #     assert 'dpu' == generated_switch_type, \
        #         f'Incorrect switch_type: {generated_switch_type} generated by sonic-cfggen'
        #
        # with allure.step('Checking generated DUT sub_role'):
        #     generated_sub_role = generated_config['DEVICE_METADATA']['localhost']['sub_role']
        #     assert 'None' == generated_sub_role, \
        #         f'Incorrect sub_role: {generated_sub_role} generated by sonic-cfggen'
        #
        # with allure.step('Checking generated DUT HwSKU'):
        #     generated_hwsku = generated_config['DEVICE_METADATA']['localhost']['hwsku']
        #     assert 'Nvidia-MBF2H536C' == generated_hwsku, \
        #         f'Incorrect hwsku: {generated_sub_role} generated by sonic-cfggen'

    def test_pmon_processes(self):
        """
        pmon docker processes test for Sonic on BlueField :
        """
        self.cli_objects.dut.general.verify_processes_of_dockers(['pmon'], self.platform_params['hwsku'])

    def test_show_commands(self):
        """
        Show commands test for Sonic on BlueField validates the commands:
            - show interfaces counters [ \n, detailed, errors, rates]
            - show interfaces description
            - show interfaces naming_mode
            - show interfaces status
            - show interfaces alias
            - show interfaces autoneg status
            - show interfaces neighbor expected
        """
        with allure.step("Verify error message in not supported commands"):
            exp_msg = "This functionality is currently not implemented for this platform"
            self.validate_expected_msg(self.cli_objects.dut.sfputil.get_sfputil_lpmode(), exp_msg)
            self.validate_expected_msg(self.cli_objects.dut.interface.get_interfaces_transceiver_lpmode(), exp_msg)
            self.validate_expected_msg(self.cli_objects.dut.interface.get_interfaces_transceiver_lpmode(self.random_iface), exp_msg)

        with allure.step("Verify platform summaty output"):
            self.validate_platform_summary()

        with allure.step('Check the list and values of ports in output of commands "show interfaces ..."'):
            self.check_interfaces_status_output()
            self.check_interfaces_counters_output()
            self.check_interfaces_counters_errors_output()
            self.check_interfaces_counters_rates_output()
            self.check_interfaces_alias_output()
            self.check_interfaces_counters_detailed_output()

        with allure.step("Verify output 'show interfaces naming_mode'"):
            self.validate_expected_msg(self.cli_objects.dut.interface.show_interfaces_naming_mode(validate=True), 'default')

        with allure.step('Verify no traceback in show interfaces cmds'):
            self.cli_objects.dut.interface.show_interfaces_auto_negotiation_status(validate=True)
            self.cli_objects.dut.interface.show_interfaces_neighbor_expected(validate=True)

    def test_config_commands(self):
        """
        Config commands test for Sonic on BlueField validates the commands:
            - config interfaces shutdown
            - config interfaces startup
            - config interfaces mtu
            - config interfaces speed
            - config interfaces type
            - config interfaces advertised-types
        """
        tested_mtu = '8000'
        tested_type = 'CR4'
        tested_speed = '10G'

        with allure.step("Verify the command 'config interface shutdown/startup'"):
            self.cli_objects.dut.interface.disable_interface(self.random_iface)
            iface_status = self.cli_objects.dut.interface.parse_interfaces_status()[self.random_iface]
            assert iface_status['Oper'] == 'down',\
                f'config shutdown failed, expected Oper state: down, actual: {iface_status["Oper"]}'
            assert iface_status['Admin'] == 'down',\
                f'config shutdown failed, expected Admin state: down, actual: {iface_status["Admin"]}'
            self.cli_objects.dut.interface.enable_interfaces([self.random_iface])
            time.sleep(2)
            iface_status = self.cli_objects.dut.interface.parse_interfaces_status()[self.random_iface]
            assert iface_status['Oper'] == 'up',\
                f'config shutdown failed, expected Oper state: up, actual: {iface_status["Oper"]}'
            assert iface_status['Admin'] == 'up',\
                f'config shutdown failed, expected Admin state: up, actual: {iface_status["Admin"]}'

        with allure.step("Verify the command 'config interface mtu'"):
            self.cli_objects.dut.interface.set_interface_mtu(self.random_iface, tested_mtu)
            current_mtu = self.cli_objects.dut.interface.parse_interfaces_status()[self.random_iface]['MTU']
            assert current_mtu == tested_mtu, f'config MTU failed, expected: {tested_mtu}, actual: {current_mtu}'
            self.cli_objects.dut.interface.set_interface_mtu(self.random_iface, '9100')

        # TODO need to check again the flow with Sash
        # with allure.step("Verify the command 'config interface speed'"):
        #     self.cli_objects.dut.interface.set_interface_speed(self.random_iface, tested_speed)
        #     iface_speed = self.cli_objects.dut.interface.parse_interfaces_status()[self.random_iface]['Speed']
        #     assert iface_speed == tested_speed, f'config speed failed, expected: {tested_speed}, actual: {iface_speed}'
        #     self.cli_objects.dut.interface.set_interface_speed(self.random_iface, '100G')

        with allure.step("Verify the command 'config interface type'"):
            self.cli_objects.dut.interface.config_interface_type(self.random_iface, tested_type)
            current_type = self.cli_objects.dut.interface.parse_show_interfaces_auto_negotiation_status()[self.random_iface]['Type']
            assert current_type == tested_type, f'config type failed, expected: {tested_type}, actual: {current_type}'
            self.cli_objects.dut.interface.config_interface_type(self.random_iface, 'none')

        with allure.step("Verify the command 'config interface advertised-types'"):
            self.cli_objects.dut.interface.config_advertised_interface_types(self.random_iface, tested_type)
            current_type = self.cli_objects.dut.interface.parse_show_interfaces_auto_negotiation_status()[self.random_iface]['Adv Types']
            assert current_type == tested_type, f'config advertised-types failed, expected: {tested_type}, actual: {current_type}'
            self.cli_objects.dut.interface.config_advertised_interface_types(self.random_iface, 'none')

    def validate_platform_summary(self):
        platform_keys_validate_content = ['Platform',
                                          'HwSKU',
                                          'ASIC Count']
        platform_keys_validate_existence = ['Serial Number',
                                            'Model Number',
                                            'Hardware Revision',
                                            'ASIC',
                                            'Switch Type']
        dut_output = self.cli_objects.dut.chassis.parse_platform_summary()

        missing_keys = list(set(platform_keys_validate_content + platform_keys_validate_existence) -
                            set(dut_output.keys()))
        assert not missing_keys, f'Some keys are missing in "show platform summary" output: {missing_keys}  '

        for key, value in dut_output.items():
            key = key.lower()
            if key in platform_keys_validate_content:
                assert (value == self.platform_params[key], f'Unexpected value for key {key}.\n'
                                                            f'Expected: {self.platform_params[key]}\n'
                                                            f'Current:{value}')

    @staticmethod
    def validate_expected_msg(output, exp_msg):
        assert exp_msg in output, f"Expected message:\n{exp_msg}\n not found in the output:\n{output}"

    @staticmethod
    def check_interfaces_output(ports_list, output, expected_template):
        logger.info(f'Checking the parameters of interfaces: {ports_list}')
        if isinstance(output, str):
            parsed_output = generic_sonic_output_parser(output, headers_ofset=IFACES_HEADERS_OFSET,
                                                        len_ofset=IFACES_LEN_OFSET,
                                                        data_ofset_from_start=IFACES_DATA_OFSET_FROM_START,
                                                        data_ofset_from_end=None, column_ofset=2, output_key='IFACE')
        else:
            parsed_output = output

        assert all(port in ports_list for port in parsed_output.keys()), \
            f'Not all expected interfaces:{ports_list} in the output'

        for port, port_details in parsed_output.items():
            for templ_key, templ_regex in expected_template.items():
                assert re.search(templ_regex, port_details[templ_key]) is not None, \
                    f"The current value: {port_details[templ_key]} can't be matched by regex(str): {templ_regex}"

    def check_interfaces_status_output(self):
        ports_status = self.cli_objects.dut.interface.parse_interfaces_status()
        self.check_interfaces_output(self.ports_list, ports_status, INTERFACE_STATUS_TEMPLATE)

    def check_interfaces_counters_output(self):
        output = self.cli_objects.dut.interface.show_interfaces_counters()
        self.check_interfaces_output(self.ports_list, output, INTERFACE_COUNTERS_TEMPLATE)

    def check_interfaces_counters_errors_output(self):
        output = self.cli_objects.dut.interface.show_interfaces_counters_errors()
        self.check_interfaces_output(self.ports_list, output, INTERFACE_COUNTERS_ERRORS_TEMPLATE)

    def check_interfaces_counters_rates_output(self):
        output = self.cli_objects.dut.interface.show_interfaces_counters_rates()
        self.check_interfaces_output(self.ports_list, output, INTERFACE_COUNTERS_RATES_TEMPLATE)

    def check_interfaces_counters_detailed_output(self):
        output = self.cli_objects.dut.interface.show_interfaces_counters_detailed(self.random_iface)
        for templ_regex in INTERFACE_COUNTERS_DETAILED_TEMPLATE:
            assert re.search(templ_regex, output) is not None, \
                f"Not found the regex {templ_regex} in the output of" \
                f" 'show interfaces counters detailed {self.random_iface}'"

    def check_interfaces_alias_output(self):
        output = self.cli_objects.dut.interface.show_interfaces_alias()
        parsed_output = generic_sonic_output_parser(output, headers_ofset=IFACES_HEADERS_OFSET,
                                                    len_ofset=IFACES_LEN_OFSET,
                                                    data_ofset_from_start=IFACES_DATA_OFSET_FROM_START,
                                                    data_ofset_from_end=None, column_ofset=2, output_key='Name')
        self.check_interfaces_output(self.ports_list, parsed_output, INTERFACE_ALIAS_TEMPLATE)
