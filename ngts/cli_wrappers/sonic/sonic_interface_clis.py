import re
import logging

from ngts.cli_wrappers.common.interface_clis_common import InterfaceCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser
from ngts.constants.constants import ConfigDbJsonConst

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
    def parse_interfaces_status(engine):
        """
        Method which getting parsed interfaces status
        :param engine: ssh engine object
        :return: dictionary, example: {'Ethernet0': {'Lanes': '0,1,2,3,4,5,6,7', 'Speed': '100G', 'MTU': '9100',
        'FEC': 'N/A', 'Alias': 'etp1', 'Vlan': 'routed', 'Oper': 'up', 'Admin': 'up', 'Type': 'QSFP28 or later',
        'Asym PFC': 'N/A'}, 'Ethernet8': {'Lanes'.......
        """
        ifaces_status = SonicInterfaceCli.show_interfaces_status(engine)
        return generic_sonic_output_parser(ifaces_status, headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
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
        regex_pattern = "(Ethernet\d+)\s*(etp\d+\w*)"
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
            assert ports_status[port]['Oper'] == expected_status,\
                'Interface {} in unexpected state, expected is {}'.format(port, expected_status)

    def configure_dpb_on_ports(self, engine, conf, expect_error=False, force=False):
        for breakout_mode, ports_list in conf.items():
            for port in ports_list:
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
            cmd = 'sudo config interface breakout {PORT} {MODE} -y {FORCE}'.format(PORT=port,
                                                                                   MODE=breakout_mode,
                                                                                   FORCE=force)
            output = engine.send_config_set([cmd, 'y'])
            logger.info(output)
            return output
        except Exception as e:
            if expect_error:
                logger.info(output)
                return output
            else:
                raise AssertionError("Command: {} failed with error {} when was expected to pass".format(cmd, e))

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
    def get_speed_in_G_format(speed_in_kb):
        """
        :param speed_in_kb: i.e, 25000
        :return: speed in G format, i.e, 25G
        """
        return "{}G".format(int(int(speed_in_kb)/1000))

    @staticmethod
    def get_breakout_mode_configured_speed(breakout_mode):
        """
        this function will return the speed that will be configured on the port be the breakout mode.
        :param breakout_mode: i,e. '4x25G[10G,1G]'
        :return: return 25G
        """
        return re.search(r"\dx(\d+G)\[[\d*G,]*\]|\dx\d+G", breakout_mode).group(1)

    @staticmethod
    def get_breakout_mode_by_speed_conf(breakout_modes_list, port_speed):
        """
        :param breakout_modes_list: i.e, ['4x25G[10G,1G]', '4x1G']
        :param port_speed: i.e, 25G
        :return:
        """
        for breakout_mode in breakout_modes_list:
            brk_mode_configured_speed = SonicInterfaceCli.get_breakout_mode_configured_speed(breakout_mode)
            if brk_mode_configured_speed == port_speed:
                return breakout_mode
        raise Exception("Didn't found breakout mode that configured speed: {} in breakout_modes_list: {}"
                        .format(port_speed, breakout_modes_list))

    @staticmethod
    def get_dut_first_split_port_info(config_db_json):
        """

        :param config_db_json: a json object of the switch config_db.json file
        :return: a list of tuples of first split port and their split number
        for example, [('Ethernet196', 2), ('Ethernet200', 2), ('Ethernet204', 4), ('Ethernet208', 4)]
        """
        dut_first_split_port_info = []
        port_info_dict = config_db_json.get(ConfigDbJsonConst.PORT)
        if port_info_dict:
            for port, port_info in port_info_dict.items():
                port_alias = port_info[ConfigDbJsonConst.ALIAS]
                is_first_split_port = bool(re.match('etp\d+a', port_alias))
                if is_first_split_port:
                    split_num = SonicInterfaceCli.get_split_number(config_db_json, port_alias)
                    dut_first_split_port_info.append((port, split_num))
        return dut_first_split_port_info

    @staticmethod
    def get_split_number(config_db_json, port_alias):
        """
        return the port split number, as the port was split to 2/4/8.
        :param config_db_json: a json object of the switch config_db.json file
        :param port_alias: the sonic port alias, e.g. 'etp1'
        :return: the number the port was split to, 2/4/8.
        """
        all_aliases = [port_info['alias'] for port_info in config_db_json[ConfigDbJsonConst.PORT].values()]
        port_alias_number = SonicInterfaceCli.get_alias_number(port_alias)
        all_aliases_of_split_port = list(filter(lambda alias: re.search("etp{}[a-z]$".format(port_alias_number), alias),
                                                all_aliases))
        split_number = len(all_aliases_of_split_port)
        return split_number

    @staticmethod
    def get_alias_number(port_alias):
        """
        :param port_alias:  the sonic port alias, e.g. 'etp1'
        :return: the number in the alias, e.g. 1
        """
        return re.search('etp(\d*)', port_alias).group(1)
