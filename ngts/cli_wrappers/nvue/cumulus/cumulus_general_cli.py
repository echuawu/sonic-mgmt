from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_constants.constants_nvos import NvosConst
from ngts.tools.test_utils import allure_utils as allure
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
import logging
from retry.api import retry

logger = logging.getLogger()


class CumulusGeneralCli(NvueGeneralCli):

    def __init__(self, engine, device):
        super().__init__(engine, device)

    def _onie_nos_install_image(self, serial_engine, image_url, expected_patterns):
        logger.info('Install image using url')
        _, index = serial_engine.run_cmd(
            f'{NvosConst.ONIE_NOS_INSTALL_CMD} {image_url}', expected_patterns,
            timeout=self.device.install_from_onie_timeout)
        logger.info(f'"{expected_patterns[index]}" pattern found')
        if index == 1:  # found "boot:" pattern and waiting for enter
            return self._complete_cumulus_installation(serial_engine, num_of_attempts=3)
        return index

    def _complete_cumulus_installation(self, serial_engine, num_of_attempts):
        logger.info("Send enter to continue cumulus installation")
        _, index = serial_engine.run_cmd('\r', self.device.install_success_patterns,
                                         timeout=self.device.install_from_onie_timeout, send_without_enter=True)
        logger.info(f'"{self.device.install_success_patterns[index]}" pattern found')
        if index == 1 and num_of_attempts > 0:  # boot: pattern  -> enter and continue
            self._complete_cumulus_installation(serial_engine, --num_of_attempts)

    def remote_reboot(self, topology_obj):
        serial_engine = self.enter_serial_connection_context(topology_obj)

        super().remote_reboot(topology_obj)

        try:
            logging.info(f"Waiting for '{NvosConst.INSTALL_BOOT_PATTERN}' pattern")
            _, index = serial_engine.run_cmd('', [NvosConst.INSTALL_BOOT_PATTERN], timeout=60,
                                             send_without_enter=True)
            logger.info(f'"{NvosConst.INSTALL_BOOT_PATTERN}" pattern found')
            if index == 0:
                logging.info("sending enter")
                serial_engine.run_cmd('\r', expected_value='.*', send_without_enter=True)
        except BaseException:
            logging.info(f"{NvosConst.INSTALL_BOOT_PATTERN} was not found - will continue")

    def _wait_nos_to_become_functional(self, engine, topology_obj=""):
        serial_engine = self.enter_serial_connection_context(topology_obj)

        with allure.step('Set default password'):
            logging.info(f"Login using default user {self.device.default_username}")
            _, index = serial_engine.run_cmd(self.device.default_username, ["Password:"], timeout=5)
            logging.info(f"Enter default password {self.device.manufacture_password}")
            _, index = serial_engine.run_cmd(self.device.manufacture_password, ["Current password:"], timeout=5)
            logging.info(f"Enter default password {self.device.manufacture_password} again")
            _, index = serial_engine.run_cmd(self.device.manufacture_password, ["New password:"], timeout=5)
            logging.info(f"Enter new password {self.device.default_password}")
            _, index = serial_engine.run_cmd(self.device.default_password, ["Retype new password:"], timeout=5)
            logging.info(f"Enter new password {self.device.default_password} again")
            _, index = serial_engine.run_cmd(self.device.default_password, [".*"],
                                             timeout=10)

        with allure.step('Wait until switch is up'):
            engine.disconnect()  # force engines.dut to reconnect
            DutUtilsTool.wait_for_cumulus_to_become_functional(engine=engine)

    def init_telemetry_keys(self):
        pass

    def apply_basic_config(self, topology_obj, setup_name, platform_params, reload_before_qos=False,
                           disable_ztp=False, configure_dns=True):
        pass

    def disable_ztp(self, disable_ztp=False):
        pass

    def _verify_dockers_are_up(self, dockers_list):
        pass
