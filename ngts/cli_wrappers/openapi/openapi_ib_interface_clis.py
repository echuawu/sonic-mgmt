from .openapi_command_builder import OpenApiCommandHelper
from ngts.nvos_constants.constants_nvos import OutputFormat, OpenApiReqType


class OpenApiIbInterfaceCli:

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
        resource_path = interface.replace(' ', '/')
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password, OpenApiReqType.PATCH,
                                                   engine.ip,
                                                   '/interface/{interface_id}{resource_path}'.format(
                                                       interface_id=port_name,
                                                       resource_path="/" + resource_path if resource_path else ''),
                                                   field_name, value)

    @staticmethod
    def unset_interface(engine, port_name, interface):
        """
        Execute unset interface command
        cmd: nv unset interface <port_name> <interface> <value>
        :param engine: ssh engine object
        :param port_name: the name of the port/ports
        :param interface: interface to set (ib-speed, speed, lanes, state, opvls, mtu)
        """
        resource_path = interface.replace(' ', '/')
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password,
                                                   OpenApiReqType.DELETE, engine.ip,
                                                   '/interface/{interface_id}{resource_path}'.format(
                                                       interface_id=port_name,
                                                       resource_path="/" + resource_path if resource_path else ''),
                                                   "", None)

    @staticmethod
    def clear_stats(engine, port_name):
        """
        Clears the interface counters
        :param engine: ssh engine object
        :param port_name: the name of the port/ports
        """
        assert "Not implemented"

    @staticmethod
    def show_interface(engine, port_name, interface_hierarchy="", output_format=OutputFormat.json):
        """
        Displays the configuration and the status of the interface
        :param engine: ssh engine object
        :param port_name: the name of the port/ports
        :param output_format: format of the output: auto(table), json or yaml. OutputFormat object is expected
        :param interface_hierarchy: the show level
        :return: output str
        """
        resource_path = interface_hierarchy.replace(' ', '/')
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password, OpenApiReqType.GET,
                                                   engine.ip,
                                                   '/interface{interface_id}{resource_path}'.format(
                                                       interface_id="/" + port_name if port_name else '',
                                                       resource_path="/" + resource_path if resource_path else ''))

    @staticmethod
    def action_recover(engine, port_name, comp):
        return OpenApiCommandHelper.execute_action("recover", engine.engine.username, engine.engine.password,
                                                   engine.ip, '/interface{interface_id}{resource_path}'.format(
                                                       interface_id="/" + port_name if port_name else '',
                                                       resource_path="/" + comp))

    @staticmethod
    def show_interface_signal_degrade(engine, port_name, output_format=OutputFormat.json):
        return OpenApiCommandHelper.execute_script(engine.engine.username, engine.engine.password, OpenApiReqType.GET,
                                                   engine.ip,
                                                   '/interface{interface_id}{resource_path}'.format(
                                                       interface_id="/" + port_name if port_name else '',
                                                       resource_path="/" + resource_path if resource_path else ''))
