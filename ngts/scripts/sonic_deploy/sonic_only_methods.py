import logging
import os
import requests
import json
import allure
import sys

from ngts.scripts.sonic_deploy.image_preparetion_methods import is_url, get_sonic_branch
from ngts.constants.constants import MarsConstants, SonicDeployConstants
from ngts.scripts.sonic_deploy.community_only_methods import get_generate_minigraph_cmd, deploy_minigpraph, \
    reboot_validation, execute_script, is_bf_topo
from retry.api import retry_call
from ngts.helpers.run_process_on_host import run_background_process_on_host

logger = logging.getLogger()


class SonicInstallationSteps:

    @staticmethod
    def pre_installation_steps(sonic_topo, base_version, target_version, setup_info, port_number, is_simx, threads_dict):
        """
        Pre-installation steps for SONIC
        :param sonic_topo: the topo for SONiC testing, for example: t0, t1, t1-lag, ptf32
        :param base_version: base version
        :param target_version: target version if provided
        :param setup_info: dictionary with setup info
        :param port_number: number of DUT ports
        :param is_simx: fixture, True if setup is SIMX, else False
        :param threads_dict: dict, contain threads which will run in background
        """
        setup_name = setup_info['setup_name']
        dut_name = setup_info['duts'][0]['dut_name']
        SonicInstallationSteps.verify_sonic_branch_supported(setup_info, base_version)
        if is_community(sonic_topo):
            ansible_path = setup_info['ansible_path']
            # Get ptf docker tag
            ptf_tag = SonicInstallationSteps.get_ptf_tag_sonic(base_version, target_version)

            with allure.step('Remove topologies'):
                for dut in setup_info['duts']:
                    SonicInstallationSteps.remove_topologies(ansible_path=ansible_path,
                                                             dut_name=dut['dut_name'],
                                                             sonic_topo=sonic_topo)

            SonicInstallationSteps.start_community_background_threads(threads_dict, setup_name,
                                                                      dut_name, sonic_topo, ptf_tag, port_number,
                                                                      ansible_path, setup_info)
        else:
            SonicInstallationSteps.start_canonical_background_threads(threads_dict, setup_name, dut_name, is_simx)

    @staticmethod
    def start_community_background_threads(threads_dict, setup_name, dut_name, sonic_topo, ptf_tag, port_number,
                                           ansible_path, setup_info):
        """
        Start background threads for community setup
        """
        add_topo_cmd = SonicInstallationSteps.get_add_topology_cmd(setup_name, dut_name, sonic_topo, ptf_tag)
        run_background_process_on_host(threads_dict, 'add_topology', add_topo_cmd, timeout=1800, exec_path=ansible_path)
        if not is_bf_topo(sonic_topo):
            gen_mg_cmd = get_generate_minigraph_cmd(setup_info, dut_name, sonic_topo, port_number)
            run_background_process_on_host(threads_dict, 'generate_minigraph', gen_mg_cmd, timeout=300,
                                           exec_path=ansible_path)

    @staticmethod
    def start_canonical_background_threads(threads_dict, setup_name, dut_name, is_simx):
        """
        Start background threads for canonical setup
        """
        python_bin_path = sys.executable

        if not is_simx:
            run_containers_cmd = SonicInstallationSteps.generate_run_containers_command(python_bin_path, setup_name)
            run_background_process_on_host(threads_dict, 'containers_bringup', run_containers_cmd, timeout=300)

        update_repo_cmd = SonicInstallationSteps.generate_update_sonic_mgmt_cmd(python_bin_path, dut_name)
        run_background_process_on_host(threads_dict, 'update_sonic_mgmt', update_repo_cmd)

    @staticmethod
    def generate_run_containers_command(python_bin_path, setup_name):
        """
        Generate command which can run containers_bringup.py script
        :param python_bin_path: path to python interpreter
        :param setup_name: name of setup
        :return: string, command which will contain containers_bringup.py script with arguments
        """
        devts_path = SonicInstallationSteps.get_devts_path()
        cmd = f'{python_bin_path} {devts_path}/scripts/docker/containers_bringup.py ' \
              f'--setup_name {setup_name} --sonic_setup'
        return cmd

    @staticmethod
    def generate_update_sonic_mgmt_cmd(python_bin_path, dut_name):
        """
        Generate command which can run update_sonic_mgmt.py script
        :param python_bin_path: path to python interpreter
        :param dut_name: name of DUT
        :return: string, command which will contain update_sonic_mgmt.py script with arguments
        """
        sonic_mgmt_path = os.path.abspath(__file__).split('/ngts/')[0]
        cmd = f'{python_bin_path} {sonic_mgmt_path}/sonic-tool/sonic_ngts/scripts/update_sonic_mgmt.py ' \
              f'--dut={dut_name} --mgmt_repo={sonic_mgmt_path}'
        return cmd

    @staticmethod
    def get_devts_path():
        """
        Get path to DevTS repository
        :return: string, path to DevTS repository
        """
        devts_path = None
        for path in sys.path:
            if path.endswith('devts'):
                devts_path = path
                break
        return devts_path

    @staticmethod
    def get_ptf_tag_sonic(base_version, target_version):
        """
        Getting ptf docker tag
        :param base_version: base version
        :param target_version: target version if provided
        :return: ptf_tag
        """
        with allure.step('Getting ptf docker tag'):
            if target_version:
                ptf_tag = SonicInstallationSteps.get_ptf_docker_tag(target_version)
            else:
                ptf_tag = SonicInstallationSteps.get_ptf_docker_tag(base_version)
        return ptf_tag

    @staticmethod
    def get_ptf_docker_tag(image_path):
        """
        Get PTF docker tag from SONiC image path
        :param image_path: example: /auto/sw_system_release/sonic/master.234-27a6641fb_Internal/Mellanox/sonic-mellanox.bin
        :return: ptf docker tag, example: '42007'
        """
        ptf_tag = 'latest'
        try:
            if is_url(image_path):
                file_path_index = 3
                image_path = '/' + '/'.join(image_path.split('/')[file_path_index:])
            branch = get_sonic_branch(image_path)
            logger.info('SONiC branch is: {}'.format(branch))
            ptf_tag = MarsConstants.BRANCH_PTF_MAPPING.get(branch, 'latest')
        except Exception as err:
            logger.error('Can not get SONiC branch and PTF tag from path: {}, using "latest". Error: {}'.format(image_path,
                                                                                                                err))

        return ptf_tag

    @staticmethod
    def remove_topologies(ansible_path, dut_name, sonic_topo):
        """
        The method removes the topologies to get the clear environment.
        """
        logger.info("Removing topologies to get the clear environment")
        with allure.step("Remove Topologies (community step)"):
            topologies = SonicInstallationSteps.get_topologies_to_remove(sonic_topo)
            logger.info(f"Remove topologies: {topologies}. This may increase a chance to deploy a new one successful")
            for topology in topologies:
                logger.info("Remove topo {}".format(topology))
                cmd = "./testbed-cli.sh -k ceos remove-topo {SWITCH}-{TOPO} vault".format(SWITCH=dut_name,
                                                                                          TOPO=topology)
                logger.info("Running CMD: {}".format(cmd))
                try:
                    execute_script(cmd, ansible_path, validate=False, timeout=600)
                except Exception as err:
                    logger.warning(f'Failed to remove topology. Got error: {err}')

    @staticmethod
    def get_topologies_to_remove(required_topology):
        if is_bf_topo(required_topology):
            return [required_topology]
        return MarsConstants.TOPO_ARRAY

    @staticmethod
    def get_add_topology_cmd(setup_name, dut_name, sonic_topo, ptf_tag):
        if sonic_topo == 'dualtor':
            dut_name = setup_name
        cmd = "./testbed-cli.sh -k ceos add-topo {SWITCH}-{TOPO} vault -e " \
              "ptf_imagetag={PTF_TAG}".format(SWITCH=dut_name, TOPO=sonic_topo, PTF_TAG=ptf_tag)
        return cmd

    @staticmethod
    def post_install_check(ansible_path, dut_name, sonic_topo):
        """
        Method which doing post install checks: check ports status, check dockers status, etc.
        """
        with allure.step("Post install check"):
            post_install_validation = "ansible-playbook -i inventory --limit {SWITCH} " \
                                      "post_upgrade_check.yml -e " \
                                      "topo={TOPO} -b -vvv".format(SWITCH=dut_name, TOPO=sonic_topo)
            logger.info("Performing post-install validation by running: {}".format(post_install_validation))
            return execute_script(cmd=post_install_validation, exec_path=ansible_path)

    @staticmethod
    def is_additional_apps_argument_is_deb_package(additional_apps_argument):
        is_deb_package = False
        path = additional_apps_argument
        try:
            if os.path.islink(additional_apps_argument):
                path = os.readlink(additional_apps_argument)
            if path.endswith('.deb'):
                is_deb_package = True
        except OSError:
            pass
        return is_deb_package

    @staticmethod
    def install_wjh(ansible_path, dut_name, sonic_topo, wjh_deb_url):
        """
        Method which doing WJH installation on DUT
        """
        logger.info("Starting installation of SONiC what-just-happened")
        cmd = "ansible-playbook install_wjh.yml -i inventory --limit {SWITCH} " \
              "-e testbed_name={SWITCH}-{TOPO} -e testbed_type={TOPO} " \
              "-e wjh_deb_url={PATH} -vvv".format(SWITCH=dut_name, TOPO=sonic_topo, PATH=wjh_deb_url)
        execute_script(cmd, ansible_path)

    @staticmethod
    def install_supported_app_extensions(ansible_path, setup_name, dut_name, app_extension_dict_path):
        app_extension_path_str = ''
        if app_extension_dict_path:
            app_extension_path_str = '--app_extension_dict_path={}'.format(app_extension_dict_path)
        cmd = "{ngts_pytest} --setup_name={setup_name} --rootdir={sonic_mgmt_dir}/ngts" \
              " -c {sonic_mgmt_dir}/ngts/pytest.ini --log-level=INFO --clean-alluredir --alluredir=/tmp/allure-results " \
              " --disable_loganalyzer {app_extension_path_str} " \
              " {sonic_mgmt_dir}/ngts/scripts/install_app_extension/install_app_extesions.py". \
            format(ngts_pytest=MarsConstants.NGTS_PATH_PYTEST, sonic_mgmt_dir=MarsConstants.SONIC_MGMT_DIR,
                   setup_name=setup_name, app_extension_path_str=app_extension_path_str)
        logger.info("Running CMD: {}".format(cmd))
        execute_script(cmd, ansible_path)

    @staticmethod
    def check_bgp_is_shutdown(dut_engine):
        assert dut_engine.run_cmd("show ip route bgp") == "" and dut_engine.run_cmd("show ipv6 route bgp") == "", \
            "Not all bgp sessions are down"

    @staticmethod
    def is_additional_apps_argument_is_app_ext_dict(additional_apps_argument):
        is_app_ext_dict = False
        try:
            requests.get('{}/{}'.format(MarsConstants.HTTP_SERVER_NBU_NFS, additional_apps_argument)).json()
            is_app_ext_dict = True
        except json.decoder.JSONDecodeError:
            pass
        return is_app_ext_dict

    @staticmethod
    def post_installation_steps(topology_obj, sonic_topo,
                                recover_by_reboot, setup_name, platform_params,
                                apply_base_config, target_version, is_shutdown_bgp, reboot_after_install,
                                deploy_only_target, fw_pkg_path, reboot, additional_apps, setup_info):
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
        ansible_path = setup_info['ansible_path']

        # Community only steps
        if is_community(sonic_topo):
            for dut in setup_info['duts']:
                general_cli_obj = dut['cli_obj']
                deploy_minigpraph(ansible_path=ansible_path, dut_name=dut['dut_name'], sonic_topo=sonic_topo,
                                  recover_by_reboot=recover_by_reboot, topology_obj=topology_obj,
                                  cli_obj=general_cli_obj)
            # TODO remove the "if" for DPU when the RM issue 3203843 will be resolved
            if not is_bf_topo(sonic_topo):
                for dut in setup_info['duts']:
                    SonicInstallationSteps.post_install_check_sonic(sonic_topo=sonic_topo, dut_name=dut['dut_name'],
                                                                    ansible_path=ansible_path)

        for dut in setup_info['duts']:
            SonicInstallationSteps.upgrade_switch(topology_obj=topology_obj, dut_name=dut['dut_name'],
                                                  setup_name=setup_name, platform_params=platform_params,
                                                  sonic_topo=sonic_topo, deploy_type='sonic',
                                                  apply_base_config=apply_base_config, target_version=target_version,
                                                  is_shutdown_bgp=is_shutdown_bgp, ansible_path=ansible_path,
                                                  reboot_after_install=reboot_after_install,
                                                  deploy_only_target=deploy_only_target, fw_pkg_path=fw_pkg_path,
                                                  cli=dut['cli_obj'])

        for dut in setup_info['duts']:
            SonicInstallationSteps.reboot_validation_sonic(dut_name=dut['dut_name'], sonic_topo=sonic_topo,
                                                           reboot=reboot, ansible_path=ansible_path)

        for dut in setup_info['duts']:
            if SonicInstallationSteps.is_additional_apps_argument_is_deb_package(additional_apps):
                SonicInstallationSteps.install_wjh_sonic(dut_name=dut['dut_name'], sonic_topo=sonic_topo,
                                                         additional_apps=additional_apps, ansible_path=ansible_path)
            else:
                if SonicInstallationSteps.is_additional_apps_argument_is_app_ext_dict(additional_apps):
                    SonicInstallationSteps.install_app_extension_sonic(dut_name=dut['dut_name'], setup_name=setup_name,
                                                                       additional_apps=additional_apps,
                                                                       ansible_path=ansible_path)
        # This check is for swb respin r-anaconda-15, only the SONiC image with hw-management version
        # higher than 7.0020.3100 runs properly on this dut, stop the regression if the image is not suitable
        for dut in setup_info['duts']:
            if dut['dut_name'] == 'r-anaconda-15':
                SonicInstallationSteps.verify_hw_management_version(engine=topology_obj.players['dut']['engine'])

        for dut in setup_info['duts']:
            # Disconnect ssh connection, prevent "Socket is closed" in case when previous steps did reboot
            topology_obj.players[dut['dut_alias']]['engine'].disconnect()
            SonicInstallationSteps.enable_info_logging(cli=dut['cli_obj'])

        if not is_community(sonic_topo):
            # Only check port status at canonical setup, there is an ansible counterpart for community setup
            for dut in setup_info['duts']:
                ports_list = topology_obj.players_all_ports[dut['dut_alias']]
                dut['cli_obj'].cli_obj.interface.check_link_state(ports_list)

    @staticmethod
    def deploy_image(cli, topology_obj, setup_name, platform_params, image_url, deploy_type,
                     apply_base_config, reboot_after_install, is_shutdown_bgp, fw_pkg_path):
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
        :param cli : SONIC cli object
        :return: raise assertion error in case of script failure
        """
        dut_engine = None
        try:
            # when bgp is up, dut can not access the external IP such as nbu-nfs.mellanox.com. So shutodwn bgp
            # for sonic only (is_shutdown_bgp is False for NVOS)
            if is_shutdown_bgp:
                with allure.step('Shutdown bgp'):
                    dut_engine = topology_obj.players['dut']['engine']
                    dut_engine.run_cmd('sudo config bgp shutdown all', validate=True)
                    logger.info("Wait all bgp sessions are down")
                    retry_call(SonicInstallationSteps.check_bgp_is_shutdown,
                               fargs=[dut_engine],
                               tries=6,
                               delay=10,
                               logger=logger)

            with allure.step('Deploy sonic image on the dut'):
                disable_ztp = False
                if deploy_type == 'onie':
                    disable_ztp = True
                cli.deploy_image(topology_obj=topology_obj, image_path=image_url, apply_base_config=apply_base_config,
                                 setup_name=setup_name, platform_params=platform_params,
                                 deploy_type=deploy_type,
                                 reboot_after_install=reboot_after_install, fw_pkg_path=fw_pkg_path,
                                 disable_ztp=disable_ztp)
        except Exception as err:
            raise AssertionError(err)
        finally:
            # for sonic only (is_shutdown_bgp is False for NVOS)
            if is_shutdown_bgp and dut_engine:
                with allure.step('Startup bgp'):
                    dut_engine.run_cmd('sudo config bgp startup all', validate=True)

    @staticmethod
    def post_install_check_sonic(sonic_topo, dut_name, ansible_path):
        """
        Method which doing post install checks: check ports status, check dockers status, etc.
        :param sonic_topo: the topo for SONiC testing, for example: t0, t1, t1-lag, ptf32
        :param dut_name: dut name
        :param ansible_path: path to ansible directory
        """
        SonicInstallationSteps.post_install_check(ansible_path=ansible_path, dut_name=dut_name,
                                                  sonic_topo=sonic_topo)

    @staticmethod
    def upgrade_switch(topology_obj, dut_name, setup_name, platform_params, sonic_topo, deploy_type,
                       apply_base_config, target_version, is_shutdown_bgp, ansible_path,
                       reboot_after_install, deploy_only_target, fw_pkg_path, cli):
        """
        Upgrade switch to the target version
        :param topology_obj: topology object
        :param dut_name: dut name
        :param setup_name: setup name
        :param platform_params: platform params
        :param sonic_topo: the topo for SONiC testing, for example: t0, t1, t1-lag, ptf32
        :param deploy_type: deploy type - 'onie', 'sonic'
        :param apply_base_config: bool value
        :param target_version: path to target version
        :param is_shutdown_bgp: bool value
        :param ansible_path: path to ansible directory
        :param reboot_after_install: bool value
        :param deploy_only_target: bool value
        :param fw_pkg_path: path to FW pkg
        :param cli: cli - SonicCli / NvueCli
        """
        if target_version and not deploy_only_target:
            with allure.step("Upgrade switch to the target version"):
                logger.info("Target version is defined, upgrade switch again to the target version.")
                SonicInstallationSteps.deploy_image(topology_obj=topology_obj, setup_name=setup_name,
                                                    image_url=target_version, platform_params=platform_params,
                                                    deploy_type=deploy_type,
                                                    apply_base_config=apply_base_config,
                                                    reboot_after_install=reboot_after_install,
                                                    is_shutdown_bgp=is_shutdown_bgp, fw_pkg_path=fw_pkg_path, cli=cli)
                if is_community(sonic_topo):
                    SonicInstallationSteps.post_install_check(ansible_path=ansible_path, dut_name=dut_name,
                                                              sonic_topo=sonic_topo)

    @staticmethod
    def reboot_validation_sonic(dut_name, sonic_topo, reboot, ansible_path):
        """
        Reboot validation
        :param dut_name: dut name
        :param sonic_topo: the topo for SONiC testing, for example: t0, t1, t1-lag, ptf32
        :param reboot: whether reboot the switch after deploy. Default: 'no'
        :param ansible_path: path to ansible directory
        """
        if reboot and reboot != "no":
            reboot_validation(ansible_path=ansible_path, reboot=reboot, dut_name=dut_name, sonic_topo=sonic_topo)

    @staticmethod
    def install_wjh_sonic(dut_name, sonic_topo, additional_apps, ansible_path):
        """
        Install WJH
        :param dut_name: dut name
        :param sonic_topo: the topo for SONiC testing, for example: t0, t1, t1-lag, ptf32
        :param additional_apps: additional apps
        :param ansible_path: path to ansible directory
        """
        wjh_deb_url_arg = '{}{}'.format(MarsConstants.HTTP_SERVER_NBU_NFS, additional_apps)
        if wjh_deb_url_arg:
            with allure.step("Install WJH"):
                SonicInstallationSteps.install_wjh(ansible_path=ansible_path, dut_name=dut_name,
                                                   sonic_topo=sonic_topo, wjh_deb_url=wjh_deb_url_arg)

    @staticmethod
    def install_app_extension_sonic(dut_name, setup_name, additional_apps, ansible_path):
        """
        Install supported app extension
        :param dut_name: dut name
        :param setup_name: setup name
        :param additional_apps: additional apps
        :param ansible_path: path to ansible directory
        """
        app_extension_dict_path = additional_apps
        if app_extension_dict_path:
            with allure.step("Install supported app extension"):
                SonicInstallationSteps.install_supported_app_extensions(ansible_path=ansible_path,
                                                                        setup_name=setup_name,
                                                                        app_extension_dict_path=app_extension_dict_path,
                                                                        dut_name=dut_name)

    @staticmethod
    def enable_info_logging(cli):
        """
        This method will enable INFO logging on swss and will save configuration.
        :param cli : SONIC cli object
        :return: none
        """
        with allure.step("Enable INFO logging on swss"):
            cli.enable_info_logging_on_docker(docker_name='swss')
            cli.save_configuration()

    @staticmethod
    def verify_hw_management_version(engine):
        lowest_valid_version = '7.0020.3100'
        with allure.step('Getting the hw-management version from dut'):
            output = engine.run_cmd('dpkg -l | grep hw-management')

        with allure.step('Comparing the hw-management version with the lowest valid version'):
            version = output.split()[2]
            version = version.split('mlnx.')[-1]
            assert version >= lowest_valid_version, \
                'Current hw-management version {} is lower than the required version {}.'.format(version, lowest_valid_version)

    @staticmethod
    def verify_sonic_branch_supported(setup_info, image_path):
        for dut in setup_info['duts']:
            if dut['dut_name'] in SonicDeployConstants.UN_SUPPORT_BRANCH_MAP:
                not_support_branch = SonicDeployConstants.UN_SUPPORT_BRANCH_MAP[dut['dut_name']]
                logger.info(f'The not supported branch for {dut["dut_name"]} are {not_support_branch}')
                with allure.step('Getting the image version'):
                    branch = get_sonic_branch(image_path)
                    logger.info('SONiC branch is: {}'.format(branch))
                assert branch not in not_support_branch, f"The setup dose not support to install image of {branch}"


def is_community(sonic_topo):
    return sonic_topo != 'ptf-any'
