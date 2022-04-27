import allure
import logging
import time
import os
import pytest

from ngts.scripts.sonic_deploy.image_preparetion_methods import prepare_images
from ngts.scripts.sonic_deploy.sonic_only_methods import SonicInstallationSteps
from ngts.scripts.sonic_deploy.nvos_only_methods import NvosInstallationSteps
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.sonic.sonic_cli import SonicCli

logger = logging.getLogger()
DUTS = ['dut', 'dut-b']


@pytest.mark.disable_loganalyzer
@allure.title('Deploy and upgrade image')
def test_deploy_and_upgrade(topology_obj, base_version, target_version, serve_files, sonic_topo,
                            deploy_only_target, port_number, setup_name, platform_params,
                            deploy_type, apply_base_config, reboot_after_install, is_shutdown_bgp,
                            fw_pkg_path, recover_by_reboot, reboot, additional_apps, workspace_path, wjh_deb_url):
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
        :param sonic_topo: sonic_topo fixture
        :param deploy_only_target: deploy_only_target fixture (True/False)
        :param port_number: port_number fixture
        :param setup_name: setup_name fixture
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
        :param wjh_deb_url: WJH deb URL
        :raise AssertionError: in case of script failure.
    """
    try:
        logger.info("Deploy SONiC testing topology and upgrade switch")

        setup_info = get_info_from_topology(topology_obj, workspace_path)
        setup_info['setup_name'] = setup_name

        image_urls = prepare_images_to_install(base_version, target_version, serve_files)
        base_version_url = get_base_version_url(deploy_only_target, image_urls)

        if sonic_topo == 'ptf-any':
            apply_base_config = True

        if wjh_deb_url and additional_apps:
            raise Exception('Arguments "wjh_deb_url" and "additional_apps" can not be used together')
        if not additional_apps:
            additional_apps = wjh_deb_url

        pre_installation_steps(sonic_topo, base_version, target_version, setup_info, port_number)

        for dut in setup_info['duts']:
            with allure.step('Install image on DUT: {}'.format(dut['host_name'])):
                # Disconnect ssh connection, prevent "Socket is closed" in case when pre step took more than 15 min
                topology_obj.players[dut['dut_alias']]['engine'].disconnect()
                deploy_image(topology_obj=topology_obj, setup_name=setup_name, image_url=base_version_url,
                             platform_params=platform_params, deploy_type=deploy_type,
                             apply_base_config=apply_base_config,
                             reboot_after_install=reboot_after_install, is_shutdown_bgp=is_shutdown_bgp,
                             fw_pkg_path=fw_pkg_path, cli_type=dut['cli_obj'])

        post_installation_steps(topology_obj=topology_obj, sonic_topo=sonic_topo,
                                recover_by_reboot=recover_by_reboot, setup_name=setup_name,
                                platform_params=platform_params, apply_base_config=apply_base_config,
                                target_version=target_version, is_shutdown_bgp=True,
                                reboot_after_install=reboot_after_install, deploy_only_target=deploy_only_target,
                                fw_pkg_path=fw_pkg_path, reboot=reboot, additional_apps=additional_apps,
                                setup_info=setup_info)

    except Exception as err:
        raise AssertionError(err)


def pre_installation_steps(sonic_topo, base_version, target_version, setup_info, port_number):
    """
    Pre-installation steps
    :param sonic_topo: sonic_topo fixture
    :param base_version: base_version fixture
    :param target_version: target version argument
    :param setup_info: dictionary with setup info
    """
    cli_type = setup_info['duts'][0]['cli_obj']
    if isinstance(cli_type, NvueGeneralCli):
        NvosInstallationSteps.pre_installation_steps()
    else:
        SonicInstallationSteps.pre_installation_steps(sonic_topo, base_version, target_version, setup_info, port_number)


def post_installation_steps(topology_obj, sonic_topo, recover_by_reboot,
                            setup_name, platform_params, apply_base_config, target_version,
                            is_shutdown_bgp, reboot_after_install, deploy_only_target, fw_pkg_path, reboot,
                            additional_apps, setup_info):
    """
    Post-installation steps
    :param topology_obj: topology object
    :param sonic_topo: sonic_topo fixture
    :param recover_by_reboot: bool value
    :param setup_name: setup_name from NOGA
    :param platform_params: platform_params
    :param apply_base_config: apply_base_config
    :param target_version: target_version
    :param is_shutdown_bgp: bool value
    :param reboot_after_install:  bool value
    :param deploy_only_target:  bool value
    :param fw_pkg_path: path to FW pkg
    :param reboot: reboot fixture
    :param additional_apps: additional_apps fixture
    :param setup_info: dictionary with setup info
    """
    dut_cli_obj = setup_info['duts'][0]['cli_obj']
    if isinstance(dut_cli_obj, NvueGeneralCli):
        NvosInstallationSteps.post_installation_steps(topology_obj)
    else:
        SonicInstallationSteps.post_installation_steps(topology_obj, sonic_topo, recover_by_reboot,
                                                       setup_name, platform_params,
                                                       apply_base_config, target_version,
                                                       is_shutdown_bgp, reboot_after_install, deploy_only_target,
                                                       fw_pkg_path, reboot, additional_apps, setup_info)


def get_info_from_topology(topology_obj, workspace_path):
    """
    Creates a class which contains setup info
    :param topology_obj: topology object
    :param workspace_path: workspace_path argument
    :return: SetupInfo object
    """
    ansible_path = os.path.join(workspace_path, "sonic-mgmt/ansible/")
    setup_info = {'ansible_path': ansible_path, 'duts': []}

    with allure.step("Create setup_info object"):
        for host in topology_obj.players:
            if host in DUTS:
                dut_name = topology_obj.players[host]['attributes'].noga_query_data['attributes']['Common']['Name']
                dut_alias = topology_obj.players[host]['attributes'].noga_query_data['attributes']['Common']['Description']
                host_name = topology_obj.players[host]['attributes'].noga_query_data['attributes']['Specific']['hostname']
                cli_type = topology_obj[0][host]['attributes'].noga_query_data['attributes']['Topology Conn.']['CLI_TYPE']
                engine = topology_obj.players[host]['engine']
                if cli_type == "NVUE":
                    cli_obj = NvueGeneralCli(engine)
                else:
                    cli_obj = SonicCli(topology_obj, dut_alias=host).general
                dut_info = {'dut_name': dut_name, 'host_name': host_name, 'cli_type': cli_type, 'engine': engine,
                            'cli_obj': cli_obj, 'dut_alias': dut_alias}
                setup_info['duts'].append(dut_info)

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


def deploy_image(topology_obj, setup_name, platform_params, image_url, deploy_type,
                 apply_base_config, reboot_after_install, is_shutdown_bgp, fw_pkg_path, cli_type):
    """
    This method will deploy sonic image on the dut.
    :param topology_obj: topology object
    :param setup_name: setup_name from NOGA
    :param platform_params: platform_params
    :param image_url: path to sonic version to be installed
    :param deploy_type: deploy_type
    :param apply_base_config: apply_base_config
    :param reboot_after_install: reboot_after_install
    :param is_shutdown_bgp: shutdown bgp flag, True or False
    :param fw_pkg_path: fw_pkg_path
    :param cli_type: NVUE or SONIC cli object
    :return: raise assertion error in case of script failure
    """

    if isinstance(cli_type, NvueGeneralCli):
        NvosInstallationSteps.deploy_image(cli_type, topology_obj, setup_name, platform_params, image_url, deploy_type,
                                           apply_base_config, reboot_after_install, fw_pkg_path)
    else:
        SonicInstallationSteps.deploy_image(cli_type, topology_obj, setup_name, platform_params, image_url,
                                            deploy_type, apply_base_config, reboot_after_install, is_shutdown_bgp,
                                            fw_pkg_path)
    time.sleep(30)
