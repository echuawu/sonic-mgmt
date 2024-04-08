import logging

from ngts.nvos_constants.constants_nvos import OutputFormat
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool

logger = logging.getLogger()


class NvueBaseCli:
    cli_name = ""

    @staticmethod
    def show(engine, resource_path, op_param="", output_format=OutputFormat.json):
        path = resource_path.replace('/', ' ')
        cmd = "nv show {path} {params}".format(path=path, params=op_param)
        if output_format:
            cmd = f'{cmd} --output {output_format}'
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

    @staticmethod
    def action(engine, device, action_type: str, resource_path: str, suffix="", param_name="", param_value="",
               output_format=None, expect_reboot=False, recovery_engine=None):
        """See documentation of BaseComponent.action"""
        command = ' '.join(['nv action', action_type, resource_path.replace('/', ' '), suffix,
                            (param_value or param_name)])
        if output_format:
            command += f" --output {output_format}"
        command = ' '.join(command.split())  # delete double-spaces
        logger.info(f"Running command: {command}")
        if expect_reboot:
            return DutUtilsTool.reload(engine=engine, device=device, command=command, confirm=True,
                                       recovery_engine=recovery_engine).verify_result()
        else:
            return engine.run_cmd(command)

    @staticmethod
    def action_install(engine, device, fae_command=False, args='', expect_reboot=False, force=False):
        """
        Method to runs nv action install <fae> platform <args> <force>
        :param engine: the engine to use
        :param device: Noga device info
        :param fae_command: if True, will add fae argument to the command
        :param args: arguments to the example above
        :param expect_reboot: if True, will expect the machine to reload as result of the command, and reconnect engines
        :param force: if True, will add "force" argument to the command
        """
        cmd = "nv action install {fae} platform {args} {force}".format(fae="fae" if fae_command else '', args=args, force="force" if force else '')
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        if expect_reboot:
            return DutUtilsTool.reload(engine=engine, device=device, command=cmd, confirm=True).verify_result()
        else:
            return engine.run_cmd(cmd)
