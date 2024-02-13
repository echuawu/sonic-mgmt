import logging
from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool

logger = logging.getLogger()


class NvuePlatformCli(NvueBaseCli):

    def __init__(self):
        self.cli_name = "Platform"

    @staticmethod
    def action_turn(engine, turn_type="", led=""):
        cmd = "nv action turn-{type} platform environment led {led}".format(type=turn_type, led=led)
        logging.info("Running '{cmd}' on dut using NVUE".format(cmd=cmd))
        return engine.run_cmd(cmd)

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

    @staticmethod
    def action_install_fae_bios_firmware(engine, bios_image_path, resource_path='', device=None):
        """
        Method to install BIOS firmware using NVUE
        :param engine: the engine to use
        :param device: Noga device info
        :param bios_image_path: the path to the BIOS firmware image
        :param resource_path: unused
        """
        return NvuePlatformCli.action_install(engine=engine, device=device, fae_command=True, args='firmware bios {}'.format(bios_image_path), expect_reboot=True, force=True)
