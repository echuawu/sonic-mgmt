import logging
from ngts.nvos_constants.constants_nvos import OutputFormat

logger = logging.getLogger()


class NvueIbInterfaceCli:

    @staticmethod
    def set_interface(engine, port_name, interface, field_name, value):
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
        cmd = 'nv action clear interface {port_name} link stats'.format(port_name=port_name)
        logging.info('Running ' + cmd)
        return engine.run_cmd(cmd)

    @staticmethod
    def show_interface(engine, port_name, interface_hierarchy="", output_format=OutputFormat.json):
        """
        Displays the configuration ans the status of the interface
        :param engine: ssh engine object
        :param port_name: the name of the port/ports
        :param output_format: format of the output: auto(table), json or yaml. OutputFormat object is expected
        :param interface_hierarchy: the show level
        :return: output str
        """
        cmd = "nv show interface {port_name} {interface_hierarchy} --output {output_format}"\
            .format(port_name=port_name, interface_hierarchy=interface_hierarchy, output_format=output_format)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
