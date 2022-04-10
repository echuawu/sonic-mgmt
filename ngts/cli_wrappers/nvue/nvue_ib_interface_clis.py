import logging

logger = logging.getLogger()


class NvueIbInterfaceCli:

    @staticmethod
    def set_interface(engine, port_name, interface, value):
        """
        Execute set interface command
        cmd: nv set interface <port_name> <interface> <value>
        :param engine: ssh engine object
        :param value: value to set
        :param port_name: the name of the port/ports
        :param interface: interface to set (ib-speed, speed, lanes, state, opvls, mtu)
        """
        cmd = 'nv set interface {port_name} {interface} {value}'.format(port_name=port_name,
                                                                        interface=interface,
                                                                        value=value)
        logging.info('Running ' + cmd)
        return engine.run_cmd(cmd)

    @staticmethod
    def unset_interface(engine, port_name, interface):
        """
        Execute unset interface command
        cmd: nv unset interface <port_name> <interface> <value>
        :param engine: ssh engine object
        :param port_name: the name of the port/ports
        :param interface: interface to set (ib-speed, speed, lanes, state, opvls, mtu)
        """
        cmd = 'nv unset interface {port_name} {interface}'.format(port_name=port_name, interface=interface)
        logging.info('Running ' + cmd)
        return engine.run_cmd(cmd)

    @staticmethod
    def clear_stats(engine, port_name):
        """
        Clears the interface counters
        :param engine: ssh engine object
        :param port_name: the name of the port/ports
        """
        cmd = 'nv action interface {port_name} link clear stats'.format(port_name=port_name)
        logging.info('Running ' + cmd)
        return engine.run_cmd(cmd)
