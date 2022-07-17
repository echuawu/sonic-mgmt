import logging
import allure
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import NvueInterfaceShowClis
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
import json
import time
import shutil
import os

logger = logging.getLogger()


class NvosInstallationSteps:

    @staticmethod
    def pre_installation_steps():
        """
        Pre-installation steps for NVOS NOS
        """
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
            assert NvosInstallationSteps.wait_for_nvos_to_become_functional(topology_obj), "Timeout " \
                "occurred while waiting for " \
                "NVOS to complete the initialization"

    @staticmethod
    def wait_for_nvos_to_become_functional(topology_obj):
        """
        Waiting for NVOS to complete the init and become functional after the installation
        :return: Bool
        """
        dut_engine = topology_obj.players['dut']['engine']
        try:
            NvueGeneralCli.wait_for_nvos_to_become_functional(dut_engine)
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
                             wjh_deb_url="", deploy_type=deploy_type,
                             reboot_after_install=reboot_after_install, fw_pkg_path=fw_pkg_path)
