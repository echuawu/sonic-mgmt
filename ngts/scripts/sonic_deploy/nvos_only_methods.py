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


class NvosInstallationSteps:

    @staticmethod
    def pre_installation_steps(setup_info, base_version='', target_version=''):
        assert target_version, 'Argument "target_version" must be provided for installing NVOS'

    @staticmethod
    def post_installation_steps(topology_obj, workspace_path, base_version='', target_version=''):
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
            dut_engine = topology_obj.players['dut']['engine']
            assert NvosInstallationSteps.wait_for_nvos_to_become_functional(dut_engine), "Timeout " \
                "occurred while waiting for " \
                "NVOS to complete the initialization"

        with allure.step('Show system and firmware version'):
            system = System()
            system.version.show(dut_engine=dut_engine)
            system.firmware.show(dut_engine=dut_engine)

        if base_version:
            with allure.step('========== NVOS - Upgrade With Saved Configuration Flow =========='):
                # if deploy_and_upgrade was invoked also with base_version, meaning that base_version is the version that
                #   was installed, and now we want to test the scenario where we set pre-defined configuration,
                #   apply & save it, and upgrade to the given target_version, which is the one that will be used for testing
                with allure.step('Upgrade to target version with saved configuration'):
                    NvosInstallationSteps.upgrade_version_with_saved_configuration(dut_engine, topology_obj, target_version)
                with allure.step('Show system and firmware version after upgrade'):
                    system = System()
                    system.version.show(dut_engine=dut_engine)
                    system.firmware.show(dut_engine=dut_engine)
        else:
            logger.info('NVOS: Argument "base-version" was not given. therefore not running the upgrade with saved configuration scenario')

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
    def upgrade_version_with_saved_configuration(dut_engine: ProxySshEngine, topology_obj, target_version_path: str):
        with allure.step('Apply and save pre-defined configuration'):
            NGTS_PATH = os.path.join(os.path.abspath(__file__).split('ngts', 1)[0], 'ngts')
            CONF_YML_FILE_NAME = 'nvos_conf_for_upgrade_test.yml'
            CONF_YML_FILE_PATH = os.path.join(NGTS_PATH, 'tools', 'test_utils', 'nvos_resources', CONF_YML_FILE_NAME)
            logger.info(f'NGTS_PATH: {NGTS_PATH}')
            logger.info(f'CONF_YML_FILE_PATH: {CONF_YML_FILE_PATH}')

            sonic_mgmt_engine = topology_obj.players['sonic-mgmt']['engine']
            host_creds = f'{sonic_mgmt_engine.username}:{sonic_mgmt_engine.password}@{sonic_mgmt_engine.ip}'
            conf_scp_url = f'scp://{host_creds}{CONF_YML_FILE_PATH}'
            system = System()
            system.config.action_fetch(remote_url=conf_scp_url, dut_engine=dut_engine)
            NvueGeneralCli.replace_config(engine=dut_engine, file=CONF_YML_FILE_NAME)
            NvueGeneralCli.apply_config(engine=dut_engine)
            NvueGeneralCli.save_config(engine=dut_engine)

        with allure.step('Upgrade to target version'):
            if target_version_path.startswith('http'):
                target_version_path = f'/auto/{target_version_path.split("/auto/")[1]}'
            image_scp_url = f'scp://{sonic_mgmt_engine.username}:{sonic_mgmt_engine.password}@{sonic_mgmt_engine.ip}{target_version_path}'
            bin_filename = target_version_path.split('/')[-1]
            system.image.action_fetch(url=image_scp_url, dut_engine=dut_engine)
            system.image.files_resource.file[bin_filename].action_install(param_force=True, engine=dut_engine)

        with allure.step('Wait for connection and system services'):
            # with allure.step('Ping switch until shutting down'):
            #     ping_till_alive(should_be_alive=False, destination_host=dut_engine.ip)
            # with allure.step('Ping switch until back alive'):
            #     ping_till_alive(should_be_alive=True, destination_host=dut_engine.ip)
            with allure.step('Wait until switch is up'):
                dut_engine.disconnect()  # force engines.dut to reconnect
                DutUtilsTool.wait_for_nvos_to_become_functional(engine=dut_engine)

        with allure.step('Verify configuration after upgrade'):
            with allure.step('Upload expected conf to switch (for running diff)'):
                EXPECTED_CONFIG_FILE_PATH = '/tmp/expected_config.yml'
                scp_file(dut_engine, CONF_YML_FILE_PATH, EXPECTED_CONFIG_FILE_PATH)

            with allure.step('Export actual configuration to file'):
                ACTUAL_CONFIG_EXPORT_FILENAME = 'upgrade_flow_config_export.yml'
                system.config.action_export(ACTUAL_CONFIG_EXPORT_FILENAME, dut_engine=dut_engine)

            with allure.step('Compare expected and actual configuration files'):
                ACTUAL_CONFIG_EXPORT_FILE_PATH = f'/host/config_files/{ACTUAL_CONFIG_EXPORT_FILENAME}'
                expression_to_start_diff = '- set:'
                # run diff for 2 yaml files (expected and actual). ignore anything before line containing expression_to_start_diff
                diff_cmd = f'diff <(sed -n "/{expression_to_start_diff}/,\\$p" {ACTUAL_CONFIG_EXPORT_FILE_PATH}) <(sed -n "/{expression_to_start_diff}/,\\$p" {EXPECTED_CONFIG_FILE_PATH})'
                diff_output = dut_engine.run_cmd(diff_cmd)
                assert not diff_output, f'Diff of {ACTUAL_CONFIG_EXPORT_FILE_PATH} and {EXPECTED_CONFIG_FILE_PATH}:\n{diff_output}'

        with allure.step('Clear tested configuration for the tests'):
            NvueGeneralCli.detach_config(dut_engine)
            NvueSystemCli.unset(dut_engine, 'system')
            NvueSystemCli.unset(dut_engine, 'ib')
            NvueSystemCli.unset(dut_engine, 'interface')
            NvueGeneralCli.apply_config(engine=dut_engine, option='--assume-yes')
            NvueGeneralCli.save_config(dut_engine)

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
