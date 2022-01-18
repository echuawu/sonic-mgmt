import allure
import logging
import time
import os
from collections import namedtuple

from ngts.scripts.sonic_deploy.image_preparetion_methods import prepare_images
from ngts.scripts.sonic_deploy.sonic_only_methods import SonicInstallationSteps
from ngts.scripts.sonic_deploy.nvos_only_methods import NvosInstallationSteps
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli

logger = logging.getLogger()
SetupInfo = namedtuple('SetupInfo', ['dut_name', 'host_name', 'cli_obj', 'cli_type', 'ansible_path'])


@allure.title('Deploy and upgrade image')
def test_deploy_and_upgrade(topology_obj, base_version, target_version, serve_files, upgrade_only, sonic_topo,
                            deploy_only_target, deploy_fanout, onyx_image_url, port_number, setup_name, platform_params,
                            wjh_deb_url, deploy_type, apply_base_config, reboot_after_install, is_shutdown_bgp,
                            fw_pkg_path, recover_by_reboot, reboot, additional_apps, workspace_path):
    """
        Deploy SONiC/NVOS testing topology and upgrade switch

        Flow:
            1. Get relevant setup info from topology object
            2. Prepare an image to be installed and get base version url
            3. Pre-installation steps
                If it's SONIC Community setup
                3.1. Get ptf docker tag
                3.2. Recover topology
            4. Deploy sonic/nvos image on the dut
            5. Post-installation steps
                For SONIC NOS only:
                5.1. Community only steps - Deploy fanout
                5.2. Post install check
                5.3. Upgrade switch to the target version
                5.4. Reboot validation
                5.5. Install WJH is requested
                5.6. Install supported app extension

        :param topology_obj: topology object fixture.
        :param base_version: base_version fixture
        :param target_version: target_version fixture
        :param serve_files: serve_files fixture
        :param upgrade_only: upgrade_only fixture (True/False)
        :param sonic_topo: sonic_topo fixture
        :param deploy_fanout: deploy_fanout fixture
        :param deploy_only_target: deploy_only_target fixture (True/False)
        :param onyx_image_url: onyx_image_url fixture
        :param port_number: port_number fixture
        :param setup_name: setup_name fixture
        :param wjh_deb_url: wjh_deb_url fixture
        :param platform_params: platform_params fixture
        :param deploy_type: deploy_type fixture
        :param apply_base_config: apply_base_config fixture
        :param reboot_after_install: reboot_after_install fixture
        :param is_shutdown_bgp: is_shutdown_bgp fixture
        :param fw_pkg_path: fw_pkg_path fixture
        :param recover_by_reboot: recover_by_reboot fixture
        :param reboot: reboot fixture
        :param additional_apps: additional_apps fixture
        :param workspace_path: workspace_path fixture
        :raise AssertionError: in case of script failure.
    """
    try:
        logger.info("Deploy SONiC testing topology and upgrade switch")

        setup_info = get_info_from_topology(topology_obj, workspace_path)

        image_urls = prepare_images_to_install(base_version, target_version, serve_files)
        base_version_url = get_base_version_url(deploy_only_target, image_urls)

        pre_installation_steps(setup_info.cli_obj, sonic_topo, upgrade_only, base_version, target_version,
                               setup_info.dut_name, setup_info.ansible_path)

        deploy_image(topology_obj=topology_obj, setup_name=setup_name,
                     image_url=base_version_url, platform_params=platform_params,
                     wjh_deb_url=wjh_deb_url, deploy_type=deploy_type,
                     apply_base_config=apply_base_config, reboot_after_install=reboot_after_install,
                     is_shutdown_bgp=is_shutdown_bgp, fw_pkg_path=fw_pkg_path, cli_type=setup_info.cli_obj)

        port_installation_steps(setup_info.cli_obj, topology_obj, setup_info.dut_name, setup_info.host_name, sonic_topo,
                                deploy_fanout, onyx_image_url, setup_info.ansible_path, port_number, recover_by_reboot, setup_name,
                                platform_params, deploy_type, apply_base_config, target_version, wjh_deb_url,
                                is_shutdown_bgp, reboot_after_install, deploy_only_target, fw_pkg_path, reboot,
                                additional_apps)

    except Exception as err:
        raise AssertionError(err)


def pre_installation_steps(cli_type, sonic_topo, upgrade_only, base_version, target_version, dut_name, ansible_path):
    """
    Pre-installation steps
    :param cli_type: Sonic or NVOS cli object
    :param sonic_topo: sonic_topo fixture
    :param upgrade_only: upgrade_only fixture (True/False)
    :param base_version: base_version fixture
    :param target_version: target version argument
    :param dut_name: dut name
    :param ansible_path: path to ansible directory
    """
    if cli_type == NvueGeneralCli:
        NvosInstallationSteps.pre_installation_steps()
    else:
        SonicInstallationSteps.pre_installation_steps(sonic_topo, upgrade_only, base_version, target_version,
                                                      dut_name, ansible_path)


def port_installation_steps(cli_type, topology_obj, dut_name, host_name, sonic_topo, deploy_fanout, onyx_image_url,
                            ansible_path, port_number, recover_by_reboot, setup_name, platform_params, deploy_type,
                            apply_base_config, target_version, wjh_deb_url, is_shutdown_bgp, reboot_after_install,
                            deploy_only_target, fw_pkg_path, reboot, additional_apps):
    """
    Post-installation steps
    :param cli_type: Sonic or NVOS cli object
    :param topology_obj: topology object
    :param dut_name: dut name
    :param host_name: host name
    :param sonic_topo: sonic_topo fixture
    :param deploy_fanout: deploy_fanout fixture
    :param onyx_image_url: onyx_image_url fixture
    :param ansible_path: path to ansible directory
    :param port_number: port number
    :param recover_by_reboot: bool value
    :param setup_name: setup_name from NOGA
    :param platform_params: platform_params
    :param deploy_type: deploy_type
    :param apply_base_config: apply_base_config
    :param target_version: target_version
    :param wjh_deb_url: WJH url
    :param is_shutdown_bgp: bool value
    :param reboot_after_install:  bool value
    :param deploy_only_target:  bool value
    :param fw_pkg_path: path to FW pkg
    :param reboot: reboot fixture
    :param additional_apps: additional_apps fixture
    """
    if cli_type == NvueGeneralCli:
        NvosInstallationSteps.post_installation_steps()
    else:
        SonicInstallationSteps.post_installation_steps(cli_type, topology_obj, dut_name, host_name, sonic_topo,
                                                       deploy_fanout, onyx_image_url, ansible_path, port_number,
                                                       recover_by_reboot, setup_name, platform_params, deploy_type,
                                                       apply_base_config, target_version, wjh_deb_url, is_shutdown_bgp,
                                                       reboot_after_install, deploy_only_target, fw_pkg_path, reboot,
                                                       additional_apps)


def get_info_from_topology(topology_obj, workspace_path):
    """
    Creates a class which contains setup info
    :param topology_obj: topology object
    :param workspace_path: workspace_path argument
    :return: SetupInfo object
    """
    with allure.step("Create setup_info object"):
        dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
        host_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['hostname']
        cli_type = topology_obj[0]['dut']['attributes'].noga_query_data['attributes']['Topology Conn.']['CLI_TYPE']
        if cli_type == "NVUE":
            cli_obj = NvueGeneralCli
        else:
            cli_obj = SonicGeneralCli
        ansible_path = os.path.join(workspace_path, "sonic-mgmt/ansible/")
        setup_info = SetupInfo(dut_name, host_name, cli_obj, cli_type, ansible_path)
    return setup_info


def prepare_images_to_install(base_version, target_version, serve_files):
    """
    Prepare images to be installed
    :param base_version: base version argument
    :param target_version: target version argument
    :param serve_files: serve files
    :return:
    '"""
    with allure.step('Prepare images and get base version url'):
        return prepare_images(base_version, target_version, serve_files)


def get_base_version_url(deploy_only_target, image_urls):
    """
    Get base version url
    :return:
    """
    with allure.step('Get base version url'):
        base_version_url = image_urls["base_version"]
        if deploy_only_target:
            if image_urls["target_version"]:
                base_version_url = image_urls["target_version"]
            else:
                raise Exception(
                    'Argument "target_version" must be provided when "deploy_only_target" flag is set to "yes".'
                    ' Please provide a target version.')
    return base_version_url


def deploy_image(topology_obj, setup_name, platform_params, image_url, wjh_deb_url, deploy_type,
                 apply_base_config, reboot_after_install, is_shutdown_bgp, fw_pkg_path, cli_type):
    """
    This method will deploy sonic image on the dut.
    :param topology_obj: topology object
    :param setup_name: setup_name from NOGA
    :param platform_params: platform_params
    :param image_url: path to sonic version to be installed
    :param wjh_deb_url: WJH url
    :param deploy_type: deploy_type
    :param apply_base_config: apply_base_config
    :param reboot_after_install: reboot_after_install
    :param is_shutdown_bgp: shutdown bgp flag, True or False
    :param fw_pkg_path: fw_pkg_path
    :param cli_type: NVUE or SONIC cli object
    :return: raise assertion error in case of script failure
    """

    if cli_type == NvueGeneralCli:
        NvosInstallationSteps.deploy_image(cli_type, topology_obj, setup_name, platform_params, image_url, deploy_type,
                                           apply_base_config, reboot_after_install, fw_pkg_path)
    else:
        SonicInstallationSteps.deploy_image(cli_type, topology_obj, setup_name, platform_params, image_url, wjh_deb_url,
                                            deploy_type, apply_base_config, reboot_after_install, is_shutdown_bgp,
                                            fw_pkg_path)
    time.sleep(30)
