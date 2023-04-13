import os
import logging
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon

logger = logging.getLogger()


class LinuxGeneralCli(GeneralCliCommon):
    """
    This class is for general cli commands for linux only
    """

    def __init__(self, engine):
        self.engine = engine

    def install_bfb_image(self, image_path, rshim_num):
        """
        Installation of BFB image on Bluefield from Server
        To use this method, the class must be created with hypervisor engine
        :param image_path: path to image
        :param rshim_num: the number of RSHIM on server
        :return: output
        """
        if image_path.endswith('.bin'):
            image_path = image_path.replace('.bin', '.bfb')
        assert os.path.exists(image_path), "The required image path doesn't exists"
        try:
            cmd = f'bfb-install -b {image_path} -r rshim{rshim_num}'
            pattern = r"\s+".join([r"INFO\[MISC\]:", r"Linux", r"up"])
            logger.info(f'Install sonic BFB image: {image_path},  on Server: {self.engine.ip},  RSHIM: {rshim_num}')
            output = self.engine.run_cmd_set([cmd], tries_after_run_cmd=75, patterns_list=[pattern])
            assert 'Installation finished' in output, f'Installation failed, please check bfb-install output:\n{output}'
            return output
        except Exception as e:
            logger.error(f"Command: {cmd} failed with error {e} when was expected to pass")
            raise AssertionError(f"Command: {cmd} failed with error {e} when was expected to pass")

    def set_next_boot_pxe_bf(self):
        """
        Sets boot mode of Bluefield to PXE
        To use this method, the class must be created with BMC engine
        :return: command output
        """
        return self.engine.run_cmd("ipmitool chassis bootparam set bootflag force_pxe")

    def remote_reboot_bf(self):
        """
        Remote reboot for Bluefield Device
        To use this method, the class must be created with BMC engine
        :return: command output
        """
        return self.engine.run_cmd("ipmitool chassis power cycle")

    def get_history(self):
        """
        get history
        :return: command output
        """
        logger.info("Running 'history' on dut")
        return self.engine.run_cmd("history")

    def clear_history(self):
        """
        clear history
        :return: command output
        """
        logger.info("Running 'history -c' on dut")
        return self.engine.run_cmd("history -c")
