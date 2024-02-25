import logging
from infra.tools.validations.traffic_validations.ping.send import ping_till_alive
from ngts.tests_nvos.conftest import ProxySshEngine
from ngts.tools.test_utils import allure_utils as allure
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
import shutil
import os
from ngts.constants.constants import LinuxConsts
from ngts.tests_nvos.general.security.authentication_restrictions.constants import RestrictionsConsts
from ngts.tests_nvos.system.clock.ClockConsts import ClockConsts
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils.nvos_general_utils import set_base_configurations
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from infra.tools.linux_tools.linux_tools import scp_file


logger = logging.getLogger()


class CumulusInstallationSteps:

    @staticmethod
    def pre_installation_steps(setup_info, base_version='', target_version=''):
        assert target_version, 'Argument "target_version" must be provided for installing Cumulus'

    @staticmethod
    def post_installation_steps():
        """
        Post-installation steps for NVOS NOS
        :return:
        """
        pass
