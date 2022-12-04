import logging
from ngts.nvos_constants.constants_nvos import OutputFormat

logger = logging.getLogger()


class NvueBaseCli:
    cli_name = ""

    @staticmethod
    def show(engine, resource_path, op_param="", output_format=OutputFormat.json):
        path = resource_path.replace('/', ' ')
        cmd = "nv show {path} {params} --output {output_format}".\
            format(output_format=output_format, path=path, params=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def set(engine, resource_path, op_param_name="", op_param_value=""):
        path = resource_path.replace('/', ' ')
        cmd = "nv set {path} {param_name} {param_value}".\
            format(path=path, param_name=op_param_name, param_value=op_param_value)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

    @staticmethod
    def unset(engine, resource_path, op_param=""):
        path = resource_path.replace('/', ' ')
        cmd = "nv unset {path} {params}".\
            format(path=path, params=op_param)
        cmd = " ".join(cmd.split())
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)
