import logging
import os
import requests
import json
import allure

from ngts.scripts.sonic_deploy.image_preparetion_methods import is_url, get_sonic_branch
from ngts.constants.constants import MarsConstants
from ngts.scripts.sonic_deploy.community_only_methods import generate_minigraph, deploy_minigprah, reboot_validation, \
    execute_script
from retry.api import retry_call

logger = logging.getLogger()


class SonicInstallationSteps:

    @staticmethod
    def pre_installation_steps(sonic_topo, base_version, target_version, setup_info, port_number):
        """
        Pre-installation steps for SONIC
        :param sonic_topo: the topo for SONiC testing, for example: t0, t1, t1-lag, ptf32
        :param base_version: base version
        :param target_version: target version if provided
        :param setup_info: dictionary with setup info
        """
        if is_community(sonic_topo):
            ansible_path = setup_info['ansible_path']
            # Get ptf docker tag
            ptf_tag = SonicInstallationSteps.get_ptf_tag_sonic(base_version, target_version)

            with allure.step('Remove topologies'):
                for dut in setup_info['duts']:
                    SonicInstallationSteps.remove_topologies(ansible_path=ansible_path, dut_name=dut['dut_name'])

            dut_name = setup_info['duts'][0]['dut_name']
            setup_name = setup_info['setup_name']
            SonicInstallationSteps.add_topology(ansible_path, setup_name, dut_name, sonic_topo, ptf_tag)
            generate_minigraph(ansible_path, setup_info, dut_name, sonic_topo, port_number)

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
    def remove_topologies(ansible_path, dut_name):
        """
        Method which add cEOS dockers and topo in case of community setup
        """
        logger.info("Preparing topology for SONiC testing")
        with allure.step("Recover Topology (community step)"):
            logger.info("Remove all topologies. This may increase a chance to deploy a new one successful")
            for topology in MarsConstants.TOPO_ARRAY:
                logger.info("Remove topo {}".format(topology))
                cmd = "./testbed-cli.sh -k ceos remove-topo {SWITCH}-{TOPO} vault".format(SWITCH=dut_name,
                                                                                          TOPO=topology)
                logger.info("Running CMD: {}".format(cmd))
                execute_script(cmd, ansible_path, validate=False)

    @staticmethod
    def add_topology(ansible_path, setup_name, dut_name, sonic_topo, ptf_tag):
        with allure.step('Adding topolgy: {}'.format(sonic_topo)):
            if sonic_topo == 'dualtor':
                dut_name = setup_name
            logger.info("Add topology")
            cmd = "./testbed-cli.sh -k ceos add-topo {SWITCH}-{TOPO} vault -e " \
                  "ptf_imagetag={PTF_TAG}".format(SWITCH=dut_name, TOPO=sonic_topo, PTF_TAG=ptf_tag)
            logger.info("Running CMD: {}".format(cmd))
            execute_script(cmd, ansible_path)

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
        cmd = "PYTHONPATH=/devts:{sonic_mgmt_dir} {ngts_pytest} --setup_name={setup_name} --rootdir={sonic_mgmt_dir}/ngts" \
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
            requests.get('{}/{}'.format(MarsConstants.HTTTP_SERVER_FIT69, additional_apps_argument)).json()
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
                deploy_minigprah(ansible_path=ansible_path, dut_name=dut['dut_name'], sonic_topo=sonic_topo,
                                 recover_by_reboot=recover_by_reboot)

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
            # when bgp is up, dut can not access the external IP such as fit69.mtl.labs.mlnx. So shutodwn bgp
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
                cli.deploy_image(topology_obj=topology_obj, image_path=image_url, apply_base_config=apply_base_config,
                                 setup_name=setup_name, platform_params=platform_params,
                                 deploy_type=deploy_type,
                                 reboot_after_install=reboot_after_install, fw_pkg_path=fw_pkg_path)
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
        wjh_deb_url_arg = '{}{}'.format(MarsConstants.HTTTP_SERVER_FIT69, additional_apps)
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


def is_community(sonic_topo):
    return sonic_topo != 'ptf-any'
