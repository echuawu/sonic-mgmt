import logging

logger = logging.getLogger()


class OutputFormat:
    auto = 'auto'
    json = 'json'
    yaml = 'yaml'


class NvueInterfaceShowClis:

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
        cmd = "nv show --output {output_format} interface {port_name} {interface_hierarchy}"\
            .format(port_name=port_name, interface_hierarchy=interface_hierarchy, output_format=output_format)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
