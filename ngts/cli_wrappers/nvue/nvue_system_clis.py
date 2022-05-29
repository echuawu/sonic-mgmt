import logging

logger = logging.getLogger()


class NvueSystemCli:
    @staticmethod
    def show(engine, resource_path="", output_format='json'):
        """
        :param engine: ssh engine object
        :param output_format: format of the output: auto(table), json or yaml. OutputFormat object is expected
        :param resource_path: the show level
        :return: output str
        """
        cmd = "nv show --output {output_format} system {resource_path}" \
            .format(resource_path=resource_path, output_format=output_format)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def set(engine, value, resource_path=""):
        """
        :param engine: ssh engine object
        :param resource_path: the show level
        :return: output str
        """
        cmd = "nv set system {resource_path} {value}" \
            .format(resource_path=resource_path, value=value)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def unset(engine, resource_path=""):
        """
        :param engine: ssh engine object
        :param resource_path: the show level
        :return: output str
        """
        cmd = "nv unset system {resource_path}" \
            .format(resource_path=resource_path)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
