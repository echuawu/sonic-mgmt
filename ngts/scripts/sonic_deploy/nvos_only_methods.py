import logging
import allure
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
import shutil
import os
from ngts.constants.constants import LinuxConsts
from ngts.tests_nvos.system.clock.ClockConsts import ClockConsts
from ngts.nvos_tools.system.System import System

logger = logging.getLogger()


class NvosInstallationSteps:

    @staticmethod
    def pre_installation_steps(setup_info):
        pass

    @staticmethod
    def post_installation_steps(topology_obj, workspace_path):
        """
        Post-installation steps for NVOS NOS
        :return:
        """
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

        with allure.step('Configure timezone'):
            try:
                logger.info("Configuring same time zone for dut and local engine to {}"
                            .format(LinuxConsts.JERUSALEM_TIMEZONE))
                logger.info('Set timezone using NVUE')
                System().set(ClockConsts.TIMEZONE, LinuxConsts.JERUSALEM_TIMEZONE, apply=True, dut_engine=dut_engine)\
                    .verify_result()
                with allure.step('Save configuration'):
                    logger.info('Save configuration')
                    NvueGeneralCli.save_config(dut_engine)
                with allure.step('Set timezone using timedatectl command'):
                    logger.info('Set timezone using linux command')
                    os.popen('sudo timedatectl set-timezone {}'.format(LinuxConsts.JERUSALEM_TIMEZONE))
            except BaseException as ex:
                logger.warning('Failed to configure timezone')

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
    def deploy_image(cli, topology_obj, setup_name, platform_params, image_url, deploy_type,
                     apply_base_config, reboot_after_install, fw_pkg_path):
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
        with allure.step('Deploy sonic image on the dut'):
            cli.deploy_image(topology_obj=topology_obj, image_path=image_url, apply_base_config=apply_base_config,
                             setup_name=setup_name, platform_params=platform_params,
                             deploy_type=deploy_type, reboot_after_install=reboot_after_install,
                             fw_pkg_path=fw_pkg_path, set_timezone=None)
