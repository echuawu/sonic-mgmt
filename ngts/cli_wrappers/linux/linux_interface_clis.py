import re
from ngts.cli_wrappers.common.interface_clis_common import InterfaceCliCommon


class LinuxInterfaceCli(InterfaceCliCommon):

    @staticmethod
    def add_interface(engine, interface, iface_type):
        """
        This method creates a network interface with specific type
        :param engine: ssh engine object
        :param interface: interface name which should be added
        :param iface_type: linux interface type
        :return: command output
        """
        return engine.run_cmd("sudo ip link add {} type {}".format(interface, iface_type))

    @staticmethod
    def del_interface(engine, interface):
        """
        This method delete a network interface
        :param engine: ssh engine object
        :param interface: interface name which should be removed, example: bond0.5
        :return: command output
        """
        return engine.run_cmd("sudo ip link del {}".format(interface))

    @staticmethod
    def add_bond_interface(engine, interface):
        """
        Method which adding bond interface to linux
        :param engine: ssh engine object
        :param interface: interface name which should be added
        :return: command output
        """
        return engine.run_cmd("sudo ip link add {} type bond".format(interface))

    @staticmethod
    def enable_interface(engine, interface):
        """
        This method enables a network interface
        :param engine: ssh engine object
        :param interface: interface name which should be enabled, example: bond0.5
        :return: command output
        """
        return engine.run_cmd("sudo ip link set {} up".format(interface))

    @staticmethod
    def disable_interface(engine, interface):
        """
        This method disables network interface
        :param engine: ssh engine object
        :param interface: interface name which should be disabled, example: bond0.5
        :return: command output
        """
        return engine.run_cmd("sudo ip link set {} down".format(interface))

    @staticmethod
    def add_port_to_bond(engine, interface, bond_name):
        """
        Method which adding slave to bond interface in linux
        :param engine: ssh engine object
        :param interface: interface name which should be added to bond
        :param bond_name: bond interface name
        :return: command output
        """
        return engine.run_cmd("sudo ip link set {} master {}".format(interface, bond_name))

    @staticmethod
    def set_interface_speed(engine, interface, speed):
        """
        Method which setting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :param speed: speed string value, i.e. '50G' or '50000'
        :return: command output
        """
        if 'G' in speed:
            speed = int(speed.split('G')[0]) * 1000

        return engine.run_cmd("ethtool -s {interface_name} speed {speed}".format(interface_name=interface, speed=speed))

    @staticmethod
    def set_interface_mtu(engine, interface, mtu):
        """
        Method which setting interface MTU
        :param engine: ssh engine object
        :param interface: interface name
        :param mtu: mtu value
        :return: command output
        """
        return engine.run_cmd("ip link set mtu {} dev {}".format(mtu, interface))

    @staticmethod
    def show_interfaces_status(engine):
        """
        Method which getting interfaces status
        :param engine: ssh engine object
        :return: parsed command output
        """
        return engine.run_cmd("ifconfig")

    @staticmethod
    def get_interface_speed(engine, interface):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface speed, example: 200G
        """
        return LinuxInterfaceCli.parse_show_interface_ethtool_status(engine, interface)['speed']

    @staticmethod
    def get_interfaces_speed(engine, interfaces_list):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface speed dict, example: {'eth1': 200G, 'eth2': '100G'}
        """
        res = dict()
        for interface in interfaces_list:
            res[interface] = LinuxInterfaceCli.get_interface_speed(engine, interface)
        return res

    @staticmethod
    def get_interface_mtu(engine, interface):
        """
        Method which getting interface MTU
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface MTU, example: 9100
        """
        return engine.run_cmd('cat /sys/class/net/{}/mtu'.format(interface))

    @staticmethod
    def get_interfaces_mtu(engine, interfaces_list):
        """
        Method which getting interface MTU
        :param engine: ssh engine object
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface MTU, example: interface mtu dict, example: {'eth1': 9100, 'eth2': '1500'}
        """
        result = {}
        for interface in interfaces_list:
            result[interface] = engine.run_cmd('cat /sys/class/net/{}/mtu'.format(interface))
        return result

    @staticmethod
    def config_auto_negotiation_mode(engine, interface, mode):
        """
        configure the auto negotiation mode on the interface
        :param engine: ssh engine object
        :param interface: i.e, enp131s0f1
        :param mode: the auto negotiation mode to be configured, i.e. 'enabled'/'disabled'
        :return: the command output
        """
        return engine.run_cmd("ethtool -s {interface_name} autoneg {mode}"
                              .format(interface_name=interface, mode=mode))

    @staticmethod
    def show_interface_ethtool_status(engine, interface=''):
        """
        ethtool information about the interface.
        :param engine: ssh engine object
        :param interface:  i.e, enp131s0f1
        :return: the command output
        """
        return engine.run_cmd("ethtool {interface_name}"
                              .format(interface_name=interface))

    @staticmethod
    def parse_show_interface_ethtool_status(engine, interface):
        """
        Method which getting parsed interfaces auto negotiation status
        :param engine: ssh engine object
        :return: a dictionary with auto negotiation relevant information,
        for example:
        {'autoneg': 'on',
        'supported speeds': {'25G', '100G', '50G', '1G', '40G', '10G'},
        'supported types': {'40GBASE-LR4', '50GBASE-KR2', '50GBASE-CR2', '1GBASE-KX', '25GBASE-SR', '25GBASE-KR',
        '100GBASE-LR4_ER4', '100GBASE-KR4', '40GBASE-SR4', '100GBASE-CR4', '40GBASE-KR4', '25GBASE-CR',
        '100GBASE-SR4', '40GBASE-CR4', '10GBASE-KR'},
        'advertised speeds': {'25G', '100G', '50G', '1G', '40G', '10G'},
        'advertised types': {'40GBASE-LR4', '50GBASE-KR2', '50GBASE-CR2', '1GBASE-KX', '25GBASE-SR', '25GBASE-KR',
        '100GBASE-LR4_ER4', '100GBASE-KR4', '40GBASE-SR4', '100GBASE-CR4', '40GBASE-KR4', '25GBASE-CR',
        '100GBASE-SR4', '40GBASE-CR4', '10GBASE-KR'},
        'speed': '100G'}
        """
        iface_ethtool_info = LinuxInterfaceCli.show_interface_ethtool_status(engine, interface=interface)
        adv_speed, adv_type = LinuxInterfaceCli.\
            parse_link_mode(re.search("Advertised link modes:([\s*(\d+\w+\/\w+)\s+]*)", iface_ethtool_info).group(1))
        sup_speed, sup_type = LinuxInterfaceCli.\
            parse_link_mode(re.search("Supported link modes:([\s*(\d+\w+\/\w+)\s+]*)", iface_ethtool_info).group(1))
        auto_neg_mode = re.search("Auto-negotiation:\s+(\w+)", iface_ethtool_info).group(1)

        speed = LinuxInterfaceCli.parse_speed(iface_ethtool_info)
        res = {"autoneg": auto_neg_mode,
               "supported speeds": set(sup_speed),
               "supported types": set(sup_type),
               "advertised speeds": set(adv_speed),
               "advertised types": set(adv_type),
               "speed": speed
               }
        return res

    @staticmethod
    def parse_speed(ethtool_output):
        speed_search_regex_res = re.search("Speed:\s+(\d+)Mb/s", ethtool_output)
        if speed_search_regex_res is not None:
            speed = "{}G".format(int(int(speed_search_regex_res.group(1))/1000))
        else:
            speed = "N/A"
        return speed

    @staticmethod
    def parse_link_mode(output_mode_string):
        """
        :param output_mode_string: i.e, "1000baseKX/Full
                                         10000baseKR/Full
	                                     40000baseKR4/Full..."
        :return: a list of speeds and types
        i.e,
        speed_list = ["1G", "10G", "40G"]
        type_list = ["1GBASE-KX", "10GBASE-KR", "40GBASE-KR4"}
        """
        speed_type_list = re.findall("(\d+)base(\w+)\/\w+", output_mode_string)
        speed_list = []
        type_list = []
        for speed, cable_type in speed_type_list:
            speed = "{}G".format(int(int(speed)/1000))
            type_list.append("{}BASE-{}".format(speed, cable_type))
            speed_list.append(speed)
        return speed_list, type_list
