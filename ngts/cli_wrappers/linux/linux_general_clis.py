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
        Instalation of BFB image on Bluefield from Server
        :param image_path: path to image
        :param rshim_num: the number of RSHIM on server
        :return: output
        """
        ctrl_c_cmd = '\x03'
        if image_path.startswith('http'):
            image_path = '/auto' + image_path.split('/auto')[1]
        try:
            cmd = f'bfb-install -b {image_path} -r rshim{rshim_num}'
            pattern = r"\s+".join([r"INFO\[MISC\]:", r"Linux", r"up"])
            logger.info(f'Install sonic BFB image {image_path} on Server: {self.engine.ip},  RSHIM{rshim_num}')
            output = self.engine.run_cmd_set([cmd, ctrl_c_cmd], tries_after_run_cmd=75, patterns_list=[pattern])
            return output
        except Exception as e:
            logger.error(f"Command: {cmd} failed with error {e} when was expected to pass")
            raise AssertionError(f"Command: {cmd} failed with error {e} when was expected to pass")
