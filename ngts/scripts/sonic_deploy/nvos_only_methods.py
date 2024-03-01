import logging
import os
import shutil

import yaml

from infra.tools.connection_tools.linux_ssh_engine import LinuxSshEngine
from infra.tools.linux_tools.linux_tools import scp_file
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli
from ngts.constants.constants import LinuxConsts
from ngts.nvos_tools.Devices.BaseDevice import BaseDevice
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.Files import File
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.conftest import ProxySshEngine
from ngts.tools.test_utils import allure_utils as allure
from ngts.tools.test_utils.nvos_config_utils import ib_clear_conf
from ngts.tools.test_utils.nvos_general_utils import set_base_configurations, is_secure_boot_enabled

logger = logging.getLogger()


class NvosInstallationSteps:

    @staticmethod
    def pre_installation_steps(setup_info, base_version='', target_version=''):
        assert target_version, 'Argument "target_version" must be provided for installing NVOS'

    @staticmethod
    def post_installation_steps(topology_obj, workspace_path, setup_info, base_version='', target_version='',
                                verify_secure_boot: bool = True):
        """
        Post-installation steps for NVOS NOS
        :return:
        """
        assert target_version, 'Argument "target_version" must have been provided for installing NVOS'

        with allure.step('Replace minigraph_facts.py replaced in ansible/library'):
            source_py = os.path.join(workspace_path, "sonic-mgmt/sonic-tool/sonic_ngts/scripts/minigraph_facts.py")
            destination_path = os.path.join(workspace_path, "sonic-mgmt/ansible/library/minigraph_facts.py")
            try:
                shutil.os.system('sudo cp "{source}" "{destination}"'.format(source=source_py,
                                                                             destination=destination_path))
                logger.info("minigraph_facts.py was replaced in ansible/library")
                logger.info("source path: " + source_py)
                logger.info("destination path: " + destination_path)
            except BaseException:
                logger.warning("Failed to replace minigraph_facts.py in ansible path. Community tests will fail.")

        with allure.step('Waiting till NVOS become functional'):
            cli_obj: NvueGeneralCli = setup_info['duts'][0]['cli_obj']
            dut_device = cli_obj.device
            dut_engine = cli_obj.engine
            assert NvosInstallationSteps.wait_for_nvos_to_become_functional(dut_engine), \
                "Timeout occurred while waiting for NVOS to complete the initialization "

        with allure.step('Show system and firmware version'):
            system = System()
            system.version.show(dut_engine=dut_engine)
            system.firmware.show(dut_engine=dut_engine)

        if verify_secure_boot:
            with allure.step('Verify Secure-Boot is enabled'):
                assert is_secure_boot_enabled(dut_engine), "Secure-Boot is expected to be enabled, but it's disabled!"

        if base_version:
            with allure.step('========== NVOS - Upgrade With Saved Configuration Flow =========='):
                # if deploy_and_upgrade was invoked also with base_version, meaning that base_version is the version that
                #   was installed, and now we want to test the scenario where we set pre-defined configuration,
                #   apply & save it, and upgrade to the given target_version, which is the one that will be used for testing
                NvosInstallationSteps.upgrade_with_saved_config_flow(topology_obj, dut_engine, dut_device, base_version,
                                                                     target_version)
        else:
            logger.info('NVOS: Argument "base-version" was not given. therefore not running the upgrade with saved '
                        'configuration scenario')

        with allure.step('Set base configuration for tests after the install phase'):
            try:
                set_base_configurations(dut_engine=dut_engine, timezone=LinuxConsts.JERUSALEM_TIMEZONE, apply=True,
                                        save_conf=True)
                with allure.step('Set timezone using timedatectl command'):
                    logger.info("Configuring same time zone for dut and local engine to {}"
                                .format(LinuxConsts.JERUSALEM_TIMEZONE))
                    logger.info('Set timezone using linux command')
                    os.popen('sudo timedatectl set-timezone {}'.format(LinuxConsts.JERUSALEM_TIMEZONE))
            except BaseException as ex:
                logger.warning('Failed to configure timezone')

        logger.info('========== NVOS - Post installation steps Done ==========')

    @staticmethod
    def upgrade_with_saved_config_flow(topology_obj, dut_engine, dut_device, base_version='', target_version=''):
        with allure.step('Upgrade to target version with saved configuration'):
            NvosInstallationSteps.upgrade_version_with_saved_configuration(dut_engine, dut_device,
                                                                           topology_obj, target_version)
        with allure.step('Show system and firmware version after upgrade'):
            system = System()
            system.version.show(dut_engine=dut_engine)
            system.firmware.show(dut_engine=dut_engine)

    @staticmethod
    def upgrade_version_with_saved_configuration(dut_engine: ProxySshEngine, dut_device: BaseDevice,
                                                 topology_obj, target_version_path: str):
        with allure.step('Strings preparation'):
            ngts_path = os.path.join(os.path.abspath(__file__).split('ngts', 1)[0], 'ngts')
            config_filename = 'nvos_config_ga_2500.yml'
            config_file_path = os.path.join(ngts_path, 'tools', 'test_utils', 'nvos_resources', config_filename)
            logger.info(f'NGTS_PATH: {ngts_path}')
            logger.info(f'CONF_YML_FILE_PATH: {config_file_path}')
            system = System()
            sonic_mgmt_engine = topology_obj.players['sonic-mgmt']['engine']
            scp_host_creds = f'{sonic_mgmt_engine.username}:{sonic_mgmt_engine.password}@{sonic_mgmt_engine.ip}'
            if target_version_path.startswith('http'):
                target_version_path = f'/auto/{target_version_path.split("/auto/")[1]}'
            bin_filename = target_version_path.split('/')[-1]

        with allure.step('Apply and save pre-defined configuration'):
            NvosInstallationSteps.fetch_apply_save_config(config_filename, config_file_path, dut_engine,
                                                          scp_host_creds, system)

        with allure.step('Upgrade to target version'):
            NvosInstallationSteps.upgrade_to_target_version(bin_filename, dut_engine, dut_device, scp_host_creds, system,
                                                            target_version_path)

        with allure.step('Wait until switch is up'):
            dut_engine.disconnect()  # force engines.dut to reconnect
            dut_engine.password = dut_device.default_password   # after upgrade flow switch has new default password

        with allure.step('Verify configuration after upgrade'):
            NvosInstallationSteps.verify_config_after_upgrade(config_file_path, dut_engine)

        with allure.step('Clear tested configuration for the tests'):
            ib_clear_conf(dut_engine)

        with allure.step('Clear fetched files for the tests'):
            system = System()
            with allure.step('Delete config files'):
                system.config.files.delete_system_files([config_filename], engine=dut_engine)
            with allure.step('Delete fetched image file'):
                system.image.files.delete_system_files([bin_filename], engine=dut_engine)
            with allure.step('Uninstall older version'):
                system.image.action_uninstall(engine=dut_engine)

    @staticmethod
    def verify_config_after_upgrade(config_file_path, dut_engine):
        with allure.step('Get actual configuration'):
            actual_config = OutputParsingTool.parse_json_str_to_dictionary(NvueGeneralCli.show_config(dut_engine)).get_returned_value()
            actual_config = [item for item in actual_config if 'set' in item][0]
        with allure.step('Get expected configuration from yml file'):
            # safe load my yml file - [{"header":...}, {"set":...}]
            with open(config_file_path, 'r') as file:
                expected_config = yaml.safe_load(file)
                expected_config = [item for item in expected_config if 'set' in item][0]
        with allure.step('Check differences between expected and actual configurations'):
            logger.info(f'config before upgrade (expected):\n{expected_config}')
            logger.info(f'config after upgrade (actual):\n{actual_config}')
            exceptions = {"secret": "*", "password": "*"}
            dicts_diff = ValidationTool.get_dictionaries_diff(expected_config, actual_config, exceptions=exceptions)
            logger.info(f'configs diff:\n{dicts_diff}')
            assert not dicts_diff, f'Configuration after upgrade is not as saved before the upgrade. diff:\n{dicts_diff}'

    @staticmethod
    def upgrade_to_target_version(bin_filename, dut_engine, dut_device, scp_host_creds, system, target_version_path):
        image_scp_url = f'scp://{scp_host_creds}{target_version_path}'
        system.image.action_fetch(url=image_scp_url, dut_engine=dut_engine)
        # use new default password for recovery after upgrade
        recovery_engine = LinuxSshEngine(dut_engine.ip, dut_engine.username, dut_device.default_password)
        File(system.image.files, bin_filename).action_file_install_with_reboot(engine=dut_engine, device=dut_device,
                                                                               recovery_engine=recovery_engine)

    @staticmethod
    def fetch_apply_save_config(config_filename, config_file_path, dut_engine, scp_host_creds, system):
        conf_scp_url = f'scp://{scp_host_creds}{config_file_path}'
        system.config.action_fetch(remote_url=conf_scp_url, dut_engine=dut_engine)
        NvueGeneralCli.replace_config(engine=dut_engine, file=config_filename)
        NvueGeneralCli.apply_config(engine=dut_engine, option='-y')
        NvueGeneralCli.save_config(engine=dut_engine)

    @staticmethod
    def wait_for_nvos_to_become_functional(dut_engine):
        """
        Waiting for NVOS to complete the init and become functional after the installation
        :return: Bool
        """
        try:
            DutUtilsTool.wait_for_nvos_to_become_functional(dut_engine).verify_result()
            return True
        except Exception as err:
            return False

    @staticmethod
    def deploy_image(cli, topology_obj, setup_name, platform_params, base_image_url, deploy_type,
                     apply_base_config, reboot_after_install, fw_pkg_path, target_image_url=''):
        """
        This method will deploy NVOS image on the dut.
        :param topology_obj: topology object
        :param setup_name: setup_name from NOGA
        :param platform_params: platform_params
        :param image_url: path to sonic version to be installed
        :param deploy_type: deploy_type
        :param apply_base_config: apply_base_config
        :param reboot_after_install: reboot_after_install
        :param cli: NVUE cli object
        :return: raise assertion error in case of script failure
        """
        with allure.step('Decide which version to install'):
            assert target_image_url, 'Argument "target_version" must be provided for installing NVOS'
            # In here, image_url is url to provided base_version ; target_image_url is url to provided target_version.
            # For NVOS, target version is always the one to install, unless base version is provided, and in that
            #   situation we'll install the base version with ONIE, and eventually upgrade to target version
            #   using upgrade CLI.
            logger.info(f'base_image_url: {base_image_url}')
            logger.info(f'target_image_url: {target_image_url}')
            image_to_install_in_onie_url = base_image_url if base_image_url else target_image_url
            logger.info(f'URL of image to install in ONIE: {image_to_install_in_onie_url}')

        with allure.step('Deploy sonic image on the dut'):
            cli.deploy_image(topology_obj=topology_obj, image_path=image_to_install_in_onie_url,
                             apply_base_config=apply_base_config, setup_name=setup_name,
                             platform_params=platform_params, deploy_type=deploy_type,
                             reboot_after_install=reboot_after_install, fw_pkg_path=fw_pkg_path, set_timezone=None)
