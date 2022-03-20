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

    @staticmethod
    def add_interface(engine, interface, iface_type):
        raise NotImplementedError

    @staticmethod
    def del_interface(engine, interface):
        raise NotImplementedError

    @staticmethod
    def enable_interface(engine, interface):
        """
        This method enables a network interface
        :param engine: ssh engine object
        :param interface: interface name which should be enabled, example: Ethernet0
        :return: command output
        """
        return engine.run_cmd("sudo config interface startup {}".format(interface))

    @staticmethod
    def enable_interfaces(engine, interfaces_list):
        """
        This method enables a list of network interfaces
        :param engine: ssh engine object
        :param interfaces_list: a list of interfaces which should be enabled, example: ["Ethernet0", "Ethernet4"]
        :return: command output
        """
        for interface in interfaces_list:
            SonicInterfaceCli.enable_interface(engine, interface)

    @staticmethod
    def disable_interface(engine, interface):
        """
        This method disables network interface
        :param engine: ssh engine object
        :param interface: interface name which should be disabled, example: Ethernet0
        :return: command output
        """
        return engine.run_cmd("sudo config interface shutdown {}".format(interface))

    @staticmethod
    def set_interface_speed(engine, interface, speed):
        """
        Method which setting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :param speed: speed value
        :return: command output
        """
        # TODO: Move 2 lines below to separate method in ngts/utilities
        if 'G' in speed:
            speed = int(speed.split('G')[0]) * 1000
        elif 'M' in speed:
            speed = int(speed.split('M')[0])

        return engine.run_cmd("sudo config interface speed {} {}".format(interface, speed))

    def set_interfaces_speed(self, engine, interfaces_speed_dict):
        """
        Method which setting interface speed
        :param engine: ssh engine object
        :param interfaces_speed_dict:  i.e, {'Ethernet0': '50G'}
        :return: command output
        """
        for interface, speed in interfaces_speed_dict.items():
            self.set_interface_speed(engine, interface, speed)

    @staticmethod
    def set_interface_mtu(engine, interface, mtu):
        """
        Method which setting interface MTU
        :param engine: ssh engine object
        :param interface: interface name
        :param mtu: mtu value
        :return: command output
        """
        return engine.run_cmd("sudo config interface mtu {} {}".format(interface, mtu))

    @staticmethod
    def show_interfaces_status(engine):
        """
        Method which getting interfaces status
        :param engine: ssh engine object
        :return: parsed command output
        """
        return engine.run_cmd("sudo show interfaces status")

    @staticmethod
    def parse_interfaces_status(engine, headers_ofset=0, len_ofset=1, data_ofset_from_start=2):
        """
        Method which getting parsed interfaces status
        :param engine: ssh engine object
        :param headers_ofset: Line number in which we have headers
        :param len_ofset: Line number from which we can find len for all fields, in example above it is line 2
        :param data_ofset_from_start: Line number from which we will start parsing data and fill dictionary with results
        :return: dictionary, example: {'Ethernet0': {'Lanes': '0,1,2,3,4,5,6,7', 'Speed': '100G', 'MTU': '9100',
        'FEC': 'N/A', 'Alias': 'etp1', 'Vlan': 'routed', 'Oper': 'up', 'Admin': 'up', 'Type': 'QSFP28 or later',
        'Asym PFC': 'N/A'}, 'Ethernet8': {'Lanes'.......
        """
        ifaces_status = SonicInterfaceCli.show_interfaces_status(engine)
        return generic_sonic_output_parser(ifaces_status, headers_ofset=headers_ofset, len_ofset=len_ofset, data_ofset_from_start=data_ofset_from_start,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Interface')

    @staticmethod
    def get_interface_speed(engine, interface):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface speed, example: 200G
        """
        return SonicInterfaceCli.parse_interfaces_status(engine)[interface]['Speed']

    @staticmethod
    def get_interfaces_speed(engine, interfaces_list):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface speed dict, example: {'eth1': 200G, 'eth2': '100G'}
        """
        result = {}
        interfaces_data = SonicInterfaceCli.parse_interfaces_status(engine)
        for interface in interfaces_list:
            result[interface] = interfaces_data[interface]['Speed']
        return result

    @staticmethod
    def get_interfaces_transceiver_eeprom(engine, interface=''):
        """
        :param engine:  ssh engine object
        :param interface:  interfaces name, example: 'Ethernet0'
        :return: interface transceiver eeprom,
        i.e, command output sample:
        Ethernet0: SFP EEPROM is not applicable for RJ45 port
        """
        cmd = f'show interfaces transceiver eeprom {interface}'
        return engine.run_cmd(cmd)

    @staticmethod
    def parse_interfaces_transceiver_eeprom(engine, interface='', interfaces_transceiver_eeprom_output=None):
        """
        Parse output 'show interfaces transceiver eeprom' as dictionary
        :param engine: ssh engine object
        :param interface: interfaces name, example: 'Ethernet0'
        :param interfaces_transceiver_eeprom_output: output 'show interfaces transceiver eeprom'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not interfaces_transceiver_eeprom_output:
            interfaces_transceiver_eeprom_output = SonicInterfaceCli.get_interfaces_transceiver_eeprom(engine,
                                                                                                       interface)

        return parse_show_interfaces_transceiver_eeprom(interfaces_transceiver_eeprom_output)

    @staticmethod
    def get_interfaces_transceiver_presence(engine, interface=''):
        """
        :param engine:  ssh engine object
        :param interface:  interfaces name, example: 'Ethernet0'
        :return: interface transceiver presence,
        i.e, command output sample:
        Port       Presence
        ---------  -----------
        Ethernet0  Not present
        """
        cmd = f'show interfaces transceiver presence {interface}'
        return engine.run_cmd(cmd)

    @staticmethod
    def parse_interfaces_transceiver_presence(engine, interface='', interfaces_transceiver_presence_output=None):
        """
        Parse output 'show interfaces transceiver presence' as dictionary
        :param engine: ssh engine object
        :param interface: interfaces name, example: 'Ethernet0'
        :param interfaces_transceiver_presence_output: output 'show interfaces transceiver presence'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not interfaces_transceiver_presence_output:
            interfaces_transceiver_presence_output = SonicInterfaceCli.get_interfaces_transceiver_presence(engine,
                                                                                                           interface)

        return generic_sonic_output_parser(interfaces_transceiver_presence_output,
                                           headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Port')

    @staticmethod
    def get_interfaces_transceiver_lpmode(engine, interface=''):
        """
        :param engine:  ssh engine object
        :param interface:  interfaces name, example: 'Ethernet0'
        :return: interface transceiver lpmode,
        i.e, command output sample:
        Port       Low-power Mode
        ---------  ----------------
        Ethernet0  N/A
        """
        cmd = f'show interfaces transceiver lpmode {interface}'
        return engine.run_cmd(cmd)

    @staticmethod
    def parse_interfaces_transceiver_lpmode(engine, interface='', interfaces_transceiver_lpmode_output=None):
        """
        Parse output 'show interfaces transceiver lpmode' as dictionary
        :param engine: ssh engine object
        :param interface: interfaces name, example: 'Ethernet0'
        :param interfaces_transceiver_lpmode_output: output 'show interfaces transceiver lpmode'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not interfaces_transceiver_lpmode_output:
            interfaces_transceiver_lpmode_output = SonicInterfaceCli.get_interfaces_transceiver_lpmode(engine,
                                                                                                       interface)

        return generic_sonic_output_parser(interfaces_transceiver_lpmode_output,
                                           headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Port')

    @staticmethod
    def get_interfaces_transceiver_error_status(engine, interface=''):
        """
        :param engine:  ssh engine object
        :param interface:  interfaces name, example: 'Ethernet0'
        :return: interface transceiver error-status,
        i.e, command output sample:
        Port       Error Status
        ---------  --------------
        Ethernet0  N/A
        """
        cmd = f'show interfaces transceiver error-status {interface}'
        return engine.run_cmd(cmd)

    @staticmethod
    def parse_interfaces_transceiver_error_status(engine, interface='',
                                                  interfaces_transceiver_error_status_output=None):
        """
        Parse output 'show interfaces transceiver error-status' as dictionary
        :param engine: ssh engine object
        :param interface: interfaces name, example: 'Ethernet0'
        :param interfaces_transceiver_error_status_output: output 'show interfaces transceiver error-status'
        :return: dict, example: {'Ethernet0': 'Present', 'Ethernet1': 'Present'...}
        """
        if not interfaces_transceiver_error_status_output:
            interfaces_transceiver_error_status_output = \
                SonicInterfaceCli.get_interfaces_transceiver_error_status(engine, interface)

        return generic_sonic_output_parser(interfaces_transceiver_error_status_output,
                                           headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Port')

    @staticmethod
    def get_interface_mtu(engine, interface):
        """
        Method which getting interface MTU
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface MTU, example: 9100
        """
        return SonicInterfaceCli.parse_interfaces_status(engine)[interface]['MTU']

    @staticmethod
    def get_interfaces_mtu(engine, interfaces_list):
        """
        Method which getting interface MTU
        :param engine: ssh engine object
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface MTU, example: interface mtu dict, example: {'eth1': 9100, 'eth2': '1500'}
        """
        result = {}
        interfaces_data = SonicInterfaceCli.parse_interfaces_status(engine)
        for interface in interfaces_list:
            result[interface] = interfaces_data[interface]['MTU']
        return result

    @staticmethod
    def show_interfaces_alias(engine):
        """
        This method return output of "show interfaces alias" command
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('show interfaces alias')

    @staticmethod
    def parse_ports_aliases_on_sonic(engine):
        """
        Method which parse "show interfaces alias" command
        :param engine: ssh engine object
        :return: a dictionary with port aliases, example: {'Ethernet0': 'etp1'}
        """
        result = {}
        interfaces_data = SonicInterfaceCli.show_interfaces_alias(engine)
        regex_pattern = r"(Ethernet\d+)\s*(etp\d+\w*)"
        list_output = re.findall(regex_pattern, interfaces_data, re.IGNORECASE)
        for port, port_sonic_alias in list_output:
            result[port] = port_sonic_alias
        return result

    @staticmethod
    def check_ports_status(engine, ports_list, expected_status='up'):
        """
        This method verifies that each iinterface is in expected oper state
        :param engine: ssh engine object
        :param ports_list: list with port names which should be in UP state
        :param expected_status: 'up' if expected UP, or 'down' if expected DOWN
        :return Assertion exception in case of failure
        """
        logger.info('Checking that ifaces: {} in expected state: {}'.format(ports_list, expected_status))
        ports_status = SonicInterfaceCli.parse_interfaces_status(engine)

        for port in ports_list:
            assert ports_status.get(port), \
                f"show interfaces status doesn't return status of port {port}, check the dockers status"
            assert ports_status[port]['Oper'] == expected_status,\
                'Interface {} in unexpected state, expected is {}'.format(port, expected_status)

    def configure_dpb_on_ports(self, engine, conf, expect_error=False, force=False):
        for breakout_mode, ports_list in conf.items():
            for port in ports_list:
                with allure.step(f"Configuring breakout mode: {breakout_mode} on port: {port}, force mode: {force}"):
                    self.configure_dpb_on_port(engine, port, breakout_mode, expect_error, force)

    @staticmethod
    def configure_dpb_on_port(engine, port, breakout_mode, expect_error=False, force=False):
        """
        :param engine: ssh engine object
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
            output = engine.run_cmd_set([cmd, 'y'], tries_after_run_cmd=75,
                                        patterns_list=[pattern])
            SonicInterfaceCli.verify_dpb_cmd(output, expect_error)
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

    @staticmethod
    def config_auto_negotiation_mode(engine, interface, mode):
        """
        configure the auto negotiation mode on the interface
        :param engine: ssh engine object
        :param interface: i.e, Ethernet0
        :param mode: the auto negotiation mode to be configured, i.e. 'enabled'/'disabled'
        :return: the command output
        """
        return engine.run_cmd("sudo config interface autoneg {interface_name} {mode}"
                              .format(interface_name=interface, mode=mode))

    @staticmethod
    def config_advertised_speeds(engine, interface, speed_list):
        """
        configure the advertised speeds on the interface
        :param engine: ssh engine object
        :param interface: i.e, Ethernet0
        :param speed_list: a string of speed configuration, i.e, "10000,50000" or "all"
        :return:  the command output
        """
        return engine.run_cmd("sudo config interface advertised-speeds {interface_name} {speed_list}"
                              .format(interface_name=interface, speed_list=speed_list))

    @staticmethod
    def config_interface_type(engine, interface, interface_type):
        """
        configure the type on the interface
        :param engine: ssh engine object
        :param interface: i.e, Ethernet0
        :param interface_type: a string of interface type , i.e. "CR"/"CR2"
        :return: the command output
        """
        return engine.run_cmd("sudo config interface type {interface_name} {interface_type}"
                              .format(interface_name=interface, interface_type=interface_type))

    @staticmethod
    def config_advertised_interface_types(engine, interface, interface_type_list):
        """
        configure the advertised types on the interface
        :param engine: ssh engine object
        :param interface: i.e, Ethernet0
        :param interface_type_list:  a string of interfaces types to advertised , i.e. "CR,CR2" or "all"
        :return: the command output
        """
        return engine.run_cmd("sudo config interface advertised-types {interface_name} {interface_type_list}"
                              .format(interface_name=interface,
                                      interface_type_list=interface_type_list))

    @staticmethod
    def show_interfaces_auto_negotiation_status(engine, interface=''):
        """
        show interfaces auto negotiation status for specific interface or all interfaces.
        :param engine: ssh engine object
        :param interface: i.e, Ethernet0 or empty string '' for all interfaces
        :return: the command output
        """
        return engine.run_cmd("sudo show interfaces autoneg status {interface_name}".format(interface_name=interface))

    @staticmethod
    def parse_show_interfaces_auto_negotiation_status(engine, interface=''):
        """
        Method which getting parsed interfaces auto negotiation status
        :param engine: ssh engine object
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
        ifaces_auto_neg_status = SonicInterfaceCli.show_interfaces_auto_negotiation_status(engine, interface=interface)
        return generic_sonic_output_parser(ifaces_auto_neg_status,
                                           headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Interface')

    @staticmethod
    def show_port_mlxlink_status(engine, pci_conf, port_number):
        """
        show the mlxlink status of the interface
        :param engine: ssh engine object
        :param pci_conf: i.e, /dev/mst/mt53100_pciconf0
        :param port_number: i.e, 1,2,3
        :return: the command output
        """
        return engine.run_cmd("sudo mlxlink -d {pci_conf} -m -p {port_number}"
                              .format(pci_conf=pci_conf, port_number=port_number))

    @staticmethod
    def configure_interface_fec(engine, interface, fec_option):
        """
        configure the interface fec
        :param engine: ssh engine object
        :param interface: i.e Ethernet0
        :param fec_option: i.e, none | fec91 | fec74
        :return: the command output
        """
        return engine.run_cmd("sudo config interface fec {interface_name} {fec_option}"
                              .format(interface_name=interface, fec_option=fec_option))

    @staticmethod
    def parse_port_mlxlink_status(engine, pci_conf, port_number):
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
        :param engine: ssh engine object
        :param pci_conf: /dev/mst/mt53100_pciconf0
        :param port_number: i.e. 35
        :return: a dictionary with the parsed mlxlink status of the port
        for example,
        {
        }
        """
        port_mlxlink_status = SonicInterfaceCli.show_port_mlxlink_status(engine, pci_conf, port_number)
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
                parsed_info[key] = SonicInterfaceCli.parse_fec_mode(actual_val)
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

    @staticmethod
    def clear_counters(engine):
        """
        clear counters
        :param engine: ssh engine object
        """
        return engine.run_cmd("sonic-clear counters", validate=True)

    @staticmethod
    def get_interface_supported_fec_modes(engine, interface):
        """
        configure invalid fec mode on port to get actual fec modes supported on port from the error message
        :param engine: ssh engine object
        :param interface: port name, i.e Ethernet0
        :return: a list of FEC modes supported on port
        """
        invalid_fec_option = "invalid_fec_mode"
        output = SonicInterfaceCli.configure_interface_fec(engine, interface, fec_option=invalid_fec_option)
        fec_options_list_string = re.search(r"Error:\s+\'fec\s+not\s+in\s+(\[.*\])!", output).group(1)
        fec_options_list = ast.literal_eval(fec_options_list_string)
        return fec_options_list

    @staticmethod
    def get_active_phy_port(engines):
        intf_status = SonicInterfaceCli.parse_interfaces_status(engines.dut)
        for interface in intf_status.keys():
            if (intf_status[interface]['Oper'] == 'up' and
                intf_status[interface]['Admin'] == 'up' and
                    interface.startswith('Ethernet')):

                return interface
        return None
