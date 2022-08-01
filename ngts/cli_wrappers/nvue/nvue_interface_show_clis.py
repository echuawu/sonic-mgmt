import logging
from ngts.constants.constants_nvos import OutputFormat

logger = logging.getLogger()


class NvueInterfaceShowClis:

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
        cmd = "nv show interface {port_name} {interface_hierarchy} --output {output_format}"\
            .format(port_name=port_name, interface_hierarchy=interface_hierarchy, output_format=output_format)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
