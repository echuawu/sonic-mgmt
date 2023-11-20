import logging
from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli

logger = logging.getLogger()


class NvueIbInterfaceCli(NvueBaseCli):

    def __init__(self):
        self.cli_name = "interface"

    @staticmethod
    def clear_stats(engine, port_name, fae_param=""):
        """
        Clears the interface counters
        :param engine: ssh engine object
        :param port_name: the name of the port/ports
        :param fae_param: optional - run the command with fae
        """
        cmd = 'nv action clear {fae_param} interface {port_name} link counters'.\
            format(fae_param=fae_param, port_name=port_name)
        cmd = " ".join(cmd.split())
        logging.info('Running ' + cmd)
        return engine.run_cmd(cmd)

    @staticmethod
    def action_clear_counters(engine, fae_param=""):
        """
        Clear counters for all interfaces
        """
        cmd = 'nv action clear {fae_param} interface counters'.format(fae_param=fae_param)
        cmd = " ".join(cmd.split())
        logging.info('Running ' + cmd)
        return engine.run_cmd(cmd)

    @staticmethod
    def show_interface(engine, port_name, interface_hierarchy="", fae_param="", output_format=OutputFormat.json):
        """
        Displays the configuration ans the status of the interface
        :param engine: ssh engine object
        :param port_name: the name of the port/ports
        :param output_format: format of the output: auto(table), json or yaml. OutputFormat object is expected
        :param interface_hierarchy: the show level
        :param fae_param: optional - to command with fae
        :return: output str
        """
        cmd = "nv show {fae_param} interface {port_name} {interface_hierarchy} --output {output_format}"\
            .format(fae_param=fae_param, port_name=port_name,
                    interface_hierarchy=interface_hierarchy, output_format=output_format)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def action_recover(engine, port_name, comp):
        cmd = "nv action recover interface {port_name} {comp}".format(port_name=port_name, comp=comp)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
