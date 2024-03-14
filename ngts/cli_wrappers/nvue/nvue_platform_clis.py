import logging

from ngts.cli_wrappers.nvue.nvue_base_clis import NvueBaseCli

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
    def action_install_fae_bios_firmware(engine, bios_image_path, resource_path='', device=None):
        """
        Method to install BIOS firmware using NVUE
        :param engine: the engine to use
        :param device: Noga device info
        :param bios_image_path: the path to the BIOS firmware image
        :param resource_path: unused
        """
        return NvuePlatformCli.action_install(engine=engine, device=device, fae_command=True, args='firmware bios {}'.format(bios_image_path), expect_reboot=True, force=True)
