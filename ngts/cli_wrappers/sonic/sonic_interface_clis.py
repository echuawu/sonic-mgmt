import re
import logging
import ast
import allure
import time
from ngts.cli_wrappers.common.interface_clis_common import InterfaceCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser, parse_show_interfaces_transceiver_eeprom
from ngts.constants.constants import AutonegCommandConstants, SonicConst

logger = logging.getLogger()


class SonicInterfaceCli(InterfaceCliCommon):

    def __init__(self, engine):
        self.engine = engine

    def add_interface(self, interface, iface_type):
        raise NotImplementedError

    def del_interface(self, interface):
        raise NotImplementedError

    def enable_interface(self, interface):
        """
        This method enables a network interface
        :param interface: interface name which should be enabled, example: Ethernet0
        :return: command output
        """
        return self.engine.run_cmd("sudo config interface startup {}".format(interface))

    def enable_interfaces(self, interfaces_list):
        """
        This method enables a list of network interfaces
        :param interfaces_list: a list of interfaces which should be enabled, example: ["Ethernet0", "Ethernet4"]
        :return: command output
        """
        for interface in interfaces_list:
            self.enable_interface(interface)

    def disable_interface(self, interface):
        """
        This method disables network interface
        :param interface: interface name which should be disabled, example: Ethernet0
        :return: command output
        """
        return self.engine.run_cmd("sudo config interface shutdown {}".format(interface))

    def set_interface_speed(self, interface, speed):
        """
        Method which setting interface speed
        :param interface: interface name
        :param speed: speed value
        :return: command output
        """
        # TODO: Move 2 lines below to separate method in ngts/utilities
        if 'G' in speed:
            speed = int(speed.split('G')[0]) * 1000
        elif 'M' in speed:
            speed = int(speed.split('M')[0])

        return self.engine.run_cmd("sudo config interface speed {} {}".format(interface, speed))

    def set_interfaces_speed(self, interfaces_speed_dict):
        """
        Method which setting interface speed
        :param interfaces_speed_dict:  i.e, {'Ethernet0': '50G'}
        :return: command output
        """
        for interface, speed in interfaces_speed_dict.items():
            self.set_interface_speed(interface, speed)

    def set_interface_mtu(self, interface, mtu):
        """
        Method which setting interface MTU
        :param interface: interface name
        :param mtu: mtu value
        :return: command output
        """
        return self.engine.run_cmd("sudo config interface mtu {} {}".format(interface, mtu))

    def show_interfaces_status(self):
        """
        Method which getting interfaces status
        :return: parsed command output
        """
        return self.engine.run_cmd("sudo show interfaces status")

    def parse_interfaces_status(self, headers_ofset=0, len_ofset=1, data_ofset_from_start=2):
        """
        Method which getting parsed interfaces status
        :param headers_ofset: Line number in which we have headers
        :param len_ofset: Line number from which we can find len for all fields, in example above it is line 2
        :param data_ofset_from_start: Line number from which we will start parsing data and fill dictionary with results
        :return: dictionary, example: {'Ethernet0': {'Lanes': '0,1,2,3,4,5,6,7', 'Speed': '100G', 'MTU': '9100',
        'FEC': 'N/A', 'Alias': 'etp1', 'Vlan': 'routed', 'Oper': 'up', 'Admin': 'up', 'Type': 'QSFP28 or later',
        'Asym PFC': 'N/A'}, 'Ethernet8': {'Lanes'.......
        """
        ifaces_status = self.show_interfaces_status()
        return generic_sonic_output_parser(ifaces_status, headers_ofset=headers_ofset, len_ofset=len_ofset,
                                           data_ofset_from_start=data_ofset_from_start,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Interface')

    def get_interface_speed(self, interface):
        """
        Method which getting interface speed
        :param interface: interface name
        :return: interface speed, example: 200G
        """
        return self.parse_interfaces_status()[interface]['Speed']

    def get_interfaces_speed(self, interfaces_list):
        """
        Method which getting interface speed
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface speed dict, example: {'eth1': 200G, 'eth2': '100G'}
        """
        result = {}
        interfaces_data = self.parse_interfaces_status()
        for interface in interfaces_list:
            result[interface] = interfaces_data[interface]['Speed']
        return result

    def get_interfaces_transceiver_eeprom(self, interface=''):
        """
        :param interface:  interfaces name, example: 'Ethernet0'
        :return: interface transceiver eeprom,
        i.e, command output sample:
        Ethernet0: SFP EEPROM is not applicable for RJ45 port
        """
        cmd = f'show interfaces transceiver eeprom {interface}'
        return self.engine.run_cmd(cmd)

    def parse_interfaces_transceiver_eeprom(self, interface='', interfaces_transceiver_eeprom_output=None):
        """
        Parse output 'show interfaces transceiver eeprom' as dictionary
        :param interface: interfaces name, example: 'Ethernet0'
        :param interfaces_transceiver_eeprom_output: output 'show interfaces transceiver eeprom'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not interfaces_transceiver_eeprom_output:
            interfaces_transceiver_eeprom_output = self.get_interfaces_transceiver_eeprom(interface)

        return parse_show_interfaces_transceiver_eeprom(interfaces_transceiver_eeprom_output)

    def get_interfaces_transceiver_presence(self, interface=''):
        """
        :param interface:  interfaces name, example: 'Ethernet0'
        :return: interface transceiver presence,
        i.e, command output sample:
        Port       Presence
        ---------  -----------
        Ethernet0  Not present
        """
        cmd = f'show interfaces transceiver presence {interface}'
        return self.engine.run_cmd(cmd)

    def parse_interfaces_transceiver_presence(self, interface='', interfaces_transceiver_presence_output=None):
        """
        Parse output 'show interfaces transceiver presence' as dictionary
        :param interface: interfaces name, example: 'Ethernet0'
        :param interfaces_transceiver_presence_output: output 'show interfaces transceiver presence'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not interfaces_transceiver_presence_output:
            interfaces_transceiver_presence_output = self.get_interfaces_transceiver_presence(interface)

        return generic_sonic_output_parser(interfaces_transceiver_presence_output,
                                           headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Port')

    def get_interfaces_transceiver_lpmode(self, interface=''):
        """
        :param interface:  interfaces name, example: 'Ethernet0'
        :return: interface transceiver lpmode,
        i.e, command output sample:
        Port       Low-power Mode
        ---------  ----------------
        Ethernet0  N/A
        """
        cmd = f'show interfaces transceiver lpmode {interface}'
        return self.engine.run_cmd(cmd)

    def parse_interfaces_transceiver_lpmode(self, interface='', interfaces_transceiver_lpmode_output=None):
        """
        Parse output 'show interfaces transceiver lpmode' as dictionary
        :param interface: interfaces name, example: 'Ethernet0'
        :param interfaces_transceiver_lpmode_output: output 'show interfaces transceiver lpmode'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not interfaces_transceiver_lpmode_output:
            interfaces_transceiver_lpmode_output = self.get_interfaces_transceiver_lpmode(interface)

        return generic_sonic_output_parser(interfaces_transceiver_lpmode_output,
                                           headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Port')

    def get_interfaces_transceiver_error_status(self, interface=''):
        """
        :param interface:  interfaces name, example: 'Ethernet0'
        :return: interface transceiver error-status,
        i.e, command output sample:
        Port       Error Status
        ---------  --------------
        Ethernet0  N/A
        """
        cmd = f'show interfaces transceiver error-status {interface}'
        return self.engine.run_cmd(cmd)

    def parse_interfaces_transceiver_error_status(self, interface='',
                                                  interfaces_transceiver_error_status_output=None):
        """
        Parse output 'show interfaces transceiver error-status' as dictionary
        :param interface: interfaces name, example: 'Ethernet0'
        :param interfaces_transceiver_error_status_output: output 'show interfaces transceiver error-status'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not interfaces_transceiver_error_status_output:
            interfaces_transceiver_error_status_output = self.get_interfaces_transceiver_error_status(interface)

        return generic_sonic_output_parser(interfaces_transceiver_error_status_output,
                                           headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Port')

    def get_interface_mtu(self, interface):
        """
        Method which getting interface MTU
        :param interface: interface name
        :return: interface MTU, example: 9100
        """
        return self.parse_interfaces_status()[interface]['MTU']

    def get_interfaces_mtu(self, interfaces_list):
        """
        Method which getting interface MTU
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface MTU, example: interface mtu dict, example: {'eth1': 9100, 'eth2': '1500'}
        """
        result = {}
        interfaces_data = self.parse_interfaces_status()
        for interface in interfaces_list:
            result[interface] = interfaces_data[interface]['MTU']
        return result

    def show_interfaces_alias(self):
        """
        This method return output of "show interfaces alias" command
        :return: command output
        """
        return self.engine.run_cmd('show interfaces alias')

    def parse_ports_aliases_on_sonic(self):
        """
        Method which parse "show interfaces alias" command
        :return: a dictionary with port aliases, example: {'Ethernet0': 'etp1'}
        """
        result = {}
        interfaces_data = self.show_interfaces_alias()
        regex_pattern = r"(Ethernet\d+)\s*(etp\d+\w*)"
        list_output = re.findall(regex_pattern, interfaces_data, re.IGNORECASE)
        for port, port_sonic_alias in list_output:
            result[port] = port_sonic_alias
        return result

    def check_ports_status(self, ports_list, expected_status='up'):
        """
        This method verifies that each iinterface is in expected oper state
        :param ports_list: list with port names which should be in UP state
        :param expected_status: 'up' if expected UP, or 'down' if expected DOWN
        :return Assertion exception in case of failure
        """
        logger.info('Checking that ifaces: {} in expected state: {}'.format(ports_list, expected_status))
        ports_status = self.parse_interfaces_status()

        for port in ports_list:
            assert ports_status.get(port), \
                f"show interfaces status doesn't return status of port {port}, check the dockers status"
            assert ports_status[port]['Oper'] == expected_status,\
                'Interface {} in unexpected state, expected is {}'.format(port, expected_status)

    def configure_dpb_on_ports(self, conf, expect_error=False, force=False):
        for breakout_mode, ports_list in conf.items():
            for port in ports_list:
                with allure.step(f"Configuring breakout mode: {breakout_mode} on port: {port}, force mode: {force}"):
                    self.configure_dpb_on_port(port, breakout_mode, expect_error, force)

    def configure_dpb_on_port(self, port, breakout_mode, expect_error=False, force=False):
        """
        :param port: i.e, Ethernet0
        :param breakout_mode: i.e, 4x50G[40G,25G,10G,1G]
        :param expect_error: True if breakout configuration is expected to fail, else False
        :param force: True if breakout configuration should be applied with force, else False
        :return: command output
        """
        logger.info('Configuring breakout mode: {} on port: {}, force mode: {}'.format(breakout_mode, port, force))
        force = "" if force is False else "-f"
        try:
            cmd = f'sudo config interface breakout {port} {breakout_mode} -y {force}'
            pattern = r"\s+".join([r"Do", r"you", r"wish", r"to", r"Continue\?", r"\[y\/N\]:"])
            output = self.engine.run_cmd_set([cmd, 'y'], tries_after_run_cmd=75, patterns_list=[pattern])
            self.verify_dpb_cmd(output, expect_error)
            return output
        except Exception as e:
            if expect_error:
                logger.info(output)
                return output
            else:
                logger.error(f"Command: {cmd} failed with error {e} when was expected to pass")
                raise AssertionError(f"Command: {cmd} failed with error {e} when was expected to pass")

    @staticmethod
    def verify_dpb_cmd(output, expect_error):
        """
        :param output: output of breakout command
        :param expect_error: True if command was expected to fail
        :return: verify the breakout command output only if it expected to pass successfully
        """
        if not expect_error:
            expected_msg_breakout_success = \
                r"\s+".join([r"Breakout", r"process", r"got",
                             r"successfully", r"completed"])
            expected_msg_breakout_mode_same = \
                r"\s+".join([r"No", r"action", r"will", r"be", r"taken", r"as",
                             r"current", r"and", r"desired", r"Breakout",
                             r"Mode", r"are", r"same"])
            with allure.step(f"Verify breakout command output"):
                if not re.search(f"{expected_msg_breakout_success}|{expected_msg_breakout_mode_same}",
                                 output, re.IGNORECASE):
                    logger.error(f"Breakout command didn't return expected message: {expected_msg_breakout_success}")
                    raise AssertionError(f"Verification of Breakout command failed")

    def config_auto_negotiation_mode(self, interface, mode):
        """
        configure the auto negotiation mode on the interface
        :param interface: i.e, Ethernet0
        :param mode: the auto negotiation mode to be configured, i.e. 'enabled'/'disabled'
        :return: the command output
        """
        return self.engine.run_cmd("sudo config interface autoneg {interface_name} {mode}"
                                   .format(interface_name=interface, mode=mode))

    def config_advertised_speeds(self, interface, speed_list):
        """
        configure the advertised speeds on the interface
        :param interface: i.e, Ethernet0
        :param speed_list: a string of speed configuration, i.e, "10000,50000" or "all"
        :return:  the command output
        """
        return self.engine.run_cmd("sudo config interface advertised-speeds {interface_name} {speed_list}"
                                   .format(interface_name=interface, speed_list=speed_list))

    def config_interface_type(self, interface, interface_type):
        """
        configure the type on the interface
        :param interface: i.e, Ethernet0
        :param interface_type: a string of interface type , i.e. "CR"/"CR2"
        :return: the command output
        """
        return self.engine.run_cmd("sudo config interface type {interface_name} {interface_type}"
                                   .format(interface_name=interface, interface_type=interface_type))

    def config_advertised_interface_types(self, interface, interface_type_list):
        """
        configure the advertised types on the interface
        :param interface: i.e, Ethernet0
        :param interface_type_list:  a string of interfaces types to advertised , i.e. "CR,CR2" or "all"
        :return: the command output
        """
        return self.engine.run_cmd("sudo config interface advertised-types {interface_name} {interface_type_list}"
                                   .format(interface_name=interface, interface_type_list=interface_type_list))

    def show_interfaces_auto_negotiation_status(self, interface=''):
        """
        show interfaces auto negotiation status for specific interface or all interfaces.
        :param interface: i.e, Ethernet0 or empty string '' for all interfaces
        :return: the command output
        """
        return self.engine.run_cmd("sudo show interfaces autoneg status {interface_name}"
                                   .format(interface_name=interface))

    def parse_show_interfaces_auto_negotiation_status(self, interface=''):
        """
        Method which getting parsed interfaces auto negotiation status
        :return: a dictionary of parsed output of show command
        {'Ethernet0':
        {'Interface': 'Ethernet0',
        'Auto-Neg Mode': 'disabled',
        'Speed': '10G',
        'Adv Speeds': 'all',
        'Type': 'CR',
        'Adv Types': 'all',
        'Oper': 'up',
        'Admin': 'up'}}
        """
        ifaces_auto_neg_status = self.show_interfaces_auto_negotiation_status(interface=interface)
        return generic_sonic_output_parser(ifaces_auto_neg_status,
                                           headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Interface')

    def show_port_mlxlink_status(self, pci_conf, port_number):
        """
        show the mlxlink status of the interface
        :param pci_conf: i.e, /dev/mst/mt53100_pciconf0
        :param port_number: i.e, 1,2,3
        :return: the command output
        """
        return self.engine.run_cmd("sudo mlxlink -d {pci_conf} -m -p {port_number}"
                                   .format(pci_conf=pci_conf, port_number=port_number))

    def configure_interface_fec(self, interface, fec_option):
        """
        configure the interface fec
        :param interface: i.e Ethernet0
        :param fec_option: i.e, none | fec91 | fec74
        :return: the command output
        """
        return self.engine.run_cmd("sudo config interface fec {interface_name} {fec_option}"
                                   .format(interface_name=interface, fec_option=fec_option))

    def parse_port_mlxlink_status(self, pci_conf, port_number):
        """
        parsing the mlxlink status command,
        sudo mlxlink -d /dev/mst/mt53100_pciconf0 -m -p 35

        Operational Info
        ----------------
        State                           : Active
        Physical state                  : ETH_AN_FSM_ENABLE
        Speed                           : 1G
        Width                           : 1x
        FEC                             : No FEC
        Loopback Mode                   : No Loopback
        Auto Negotiation                : ON

        ...
        :param pci_conf: /dev/mst/mt53100_pciconf0
        :param port_number: i.e. 35
        :return: a dictionary with the parsed mlxlink status of the port
        for example,
        {
        }
        """
        port_mlxlink_status = self.show_port_mlxlink_status(pci_conf, port_number)
        regex_expressions = AutonegCommandConstants.REGEX_PARSE_EXPRESSION_FOR_MLXLINK
        parsed_info = {}
        for key, regex_expression_tuple in regex_expressions.items():
            regex_exp, expected_val, parsed_val, default_val = regex_expression_tuple
            actual_val = re.search(regex_exp, port_mlxlink_status)
            if actual_val:
                actual_val = actual_val.group(1)
            else:
                raise AssertionError("Couldn't get value match with regex expression {}".format(regex_exp))
            parsed_info[key] = actual_val
            if key == AutonegCommandConstants.FEC:
                parsed_info[key] = self.parse_fec_mode(actual_val)
            elif expected_val is not None and re.search(expected_val, actual_val):
                parsed_info[key] = parsed_val
            elif default_val is not None:
                parsed_info[key] = default_val
        return parsed_info

    @staticmethod
    def parse_fec_mode(actual_mlxlink_fec_val):
        if re.search("Firecode FEC", actual_mlxlink_fec_val, re.IGNORECASE):
            return SonicConst.FEC_FC_MODE
        elif re.search(SonicConst.FEC_RS_MODE, actual_mlxlink_fec_val, re.IGNORECASE):
            return SonicConst.FEC_RS_MODE
        elif re.search("No FEC", actual_mlxlink_fec_val, re.IGNORECASE):
            return SonicConst.FEC_NONE_MODE
        else:
            raise AssertionError("Couldn't parse FEC value: {} on mlxlink output".format(actual_mlxlink_fec_val))

    def clear_counters(self):
        """
        clear counters
        """
        return self.engine.run_cmd("sonic-clear counters", validate=True)

    def get_interface_supported_fec_modes(self, interface):
        """
        configure invalid fec mode on port to get actual fec modes supported on port from the error message
        :param interface: port name, i.e Ethernet0
        :return: a list of FEC modes supported on port
        """
        invalid_fec_option = "invalid_fec_mode"
        output = self.configure_interface_fec(interface, fec_option=invalid_fec_option)
        fec_options_list_string = re.search(r"Error:\s+\'fec\s+not\s+in\s+(\[.*\])!", output).group(1)
        fec_options_list = ast.literal_eval(fec_options_list_string)
        return fec_options_list

    def get_active_phy_port(self):
        intf_status = self.parse_interfaces_status()
        for interface in intf_status.keys():
            if (intf_status[interface]['Oper'] == 'up' and
                intf_status[interface]['Admin'] == 'up' and
                    interface.startswith('Ethernet')):

                return interface
        return None
