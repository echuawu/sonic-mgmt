import logging
import allure


logger = logging.getLogger()


class NvosInstallationSteps:

    @staticmethod
    def pre_installation_steps():
        """
        Pre-installation steps for NVOS NOS
        """
        pass

    @staticmethod
    def post_installation_steps():
        """
        Post-installation steps for NVOS NOS
        :return:
        """
        pass

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
