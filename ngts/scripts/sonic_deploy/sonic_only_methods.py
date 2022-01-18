import logging
import os
import requests
import json
import allure

from ngts.scripts.sonic_deploy.image_preparetion_methods import is_url, get_sonic_branch
from ngts.constants.constants import MarsConstants
from ngts.scripts.sonic_deploy.community_only_methods import deploy_fanout_config, generate_minigraph, \
    deploy_minigprah, reboot_validation, execute_script
from retry.api import retry_call

logger = logging.getLogger()


class SonicInstallationSteps:

    @staticmethod
    def pre_installation_steps(sonic_topo, upgrade_only, base_version, target_version, dut_name, ansible_path):
        """
        Pre-installation steps for SONIC
        :param sonic_topo: the topo for SONiC testing, for example: t0, t1, t1-lag, ptf32
        :param upgrade_only: bool value
        :param base_version: base version
        :param target_version: target version if provided
        :param dut_name: dut_name
        :param ansible_path: path to ansible directory
        """
        if sonic_topo and sonic_topo != 'ptf-any' and upgrade_only:
            # Get ptf docker tag
            ptf_tag = SonicInstallationSteps.get_ptf_tag_sonic(base_version, target_version)
            # Recover topology
            SonicInstallationSteps.recover_topology(ansible_path, dut_name, sonic_topo, ptf_tag)

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
    def recover_topology(ansible_path, dut_name, sonic_topo, ptf_tag):
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
                execute_script(cmd, ansible_path)

            logger.info("Add topology")
            cmd = "./testbed-cli.sh -k ceos add-topo {SWITCH}-{TOPO} vault -e" \
                  "ptf_imagetag={PTF_TAG}".format(SWITCH=dut_name, TOPO=sonic_topo, PTF_TAG=ptf_tag)
            logger.info("Running CMD: {}".format(cmd))
            execute_script(cmd, ansible_path)

    @staticmethod
    def post_install_check(ansible_path, dut_name, sonic_topo):
        """
        Method which doing post install checks: check ports status, check dockers status, etc.
        """
        with allure.step("Post install check"):
            post_install_validation = "ansible-playbook -i inventory --limit {SWITCH}-{TOPO} " \
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
        cmd = "ansible-playbook install_wjh.yml -i inventory --limit {SWITCH}-{TOPO} \
                            -e testbed_name={SWITCH}-{TOPO} -e testbed_type={TOPO} \
                            -e wjh_deb_url={PATH} -vvv".format(SWITCH=dut_name, TOPO=sonic_topo,
                                                               PATH=wjh_deb_url)
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
    def post_installation_steps(cli, topology_obj, dut_name, host_name, sonic_topo, deploy_fanout, onyx_image_url, ansible_path,
                                port_number, recover_by_reboot, setup_name, platform_params, deploy_type,
                                apply_base_config, target_version, wjh_deb_url, is_shutdown_bgp, reboot_after_install,
                                deploy_only_target, fw_pkg_path, reboot, additional_apps):
        """
        Post-installation steps
        :param cli: Sonic cli object
        :param topology_obj: topology object
        :param dut_name: dut_name
        :param host_name: host_name
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
        # Community only steps - Deploy fanout
        SonicInstallationSteps.deploy_fanout_sonic(sonic_topo, deploy_fanout,
                                                   onyx_image_url, ansible_path, host_name,
                                                   dut_name, port_number, recover_by_reboot)

        # Post install check
        SonicInstallationSteps.post_install_check_sonic(sonic_topo, dut_name, ansible_path)

        # Upgrade switch to the target version
        SonicInstallationSteps.upgrade_switch(topology_obj=topology_obj,
                                              dut_name=dut_name, setup_name=setup_name,
                                              platform_params=platform_params,
                                              sonic_topo=sonic_topo, deploy_type=deploy_type,
                                              apply_base_config=apply_base_config,
                                              target_version=target_version, wjh_deb_url=wjh_deb_url,
                                              is_shutdown_bgp=is_shutdown_bgp, ansible_path=ansible_path,
                                              reboot_after_install=reboot_after_install,
                                              deploy_only_target=deploy_only_target,
                                              fw_pkg_path=fw_pkg_path, cli=cli)

        # Reboot validation
        SonicInstallationSteps.reboot_validation_sonic(dut_name=dut_name,
                                                       sonic_topo=sonic_topo, reboot=reboot, ansible_path=ansible_path)

        # Install WJH is requested
        SonicInstallationSteps.install_wjh_sonic(dut_name=dut_name,
                                                 sonic_topo=sonic_topo, additional_apps=additional_apps,
                                                 ansible_path=ansible_path)

        # Install supported app extension
        SonicInstallationSteps.install_app_extension_sonic(dut_name=dut_name,
                                                           setup_name=setup_name, additional_apps=additional_apps,
                                                           ansible_path=ansible_path)

    @staticmethod
    def deploy_image(cli, topology_obj, setup_name, platform_params, image_url, wjh_deb_url, deploy_type,
                     apply_base_config, reboot_after_install, is_shutdown_bgp, fw_pkg_path):
        """
        This method will deploy sonic image on the dut.
        :param topology_obj: topology object
        :param setup_name: setup_name from NOGA
        :param platform_params: platform_params
        :param image_url: path to sonic version to be installed
        :param wjh_deb_url: wjh_deb_url
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
                                 wjh_deb_url=wjh_deb_url, deploy_type=deploy_type,
                                 reboot_after_install=reboot_after_install, fw_pkg_path=fw_pkg_path)
        except Exception as err:
            raise AssertionError(err)
        finally:
            # for sonic only (is_shutdown_bgp is False for NVOS)
            if is_shutdown_bgp and dut_engine:
                with allure.step('Startup bgp'):
                    dut_engine.run_cmd('sudo config bgp startup all', validate=True)

    @staticmethod
    def deploy_fanout_sonic(sonic_topo, deploy_fanout, onyx_image_url, ansible_path, host_name, dut_name,
                            port_number, recover_by_reboot):
        """
        Deploy fanout on sonic switch
        :param sonic_topo: the topo for SONiC testing, for example: t0, t1, t1-lag, ptf32
        :param deploy_fanout: bool value
        :param onyx_image_url: url path to onyx image
        :param ansible_path: path to ansible directory
        :param host_name: host name
        :param dut_name: dut name
        :param port_number: port number
        :param recover_by_reboot: bool value
        :return:
        """
        if sonic_topo != 'ptf-any':
            if deploy_fanout:
                with allure.step('Deploy fanout'):
                    deploy_fanout_config(onyx_image_url=onyx_image_url, ansible_path=ansible_path, host_name=host_name)
            with allure.step('Generate Minigraph'):
                generate_minigraph(ansible_path=ansible_path, dut_name=dut_name, sonic_topo=sonic_topo,
                                   port_number=port_number)
            with allure.step('Deploy Minigraph'):
                retry_call(deploy_minigprah, fargs=[ansible_path, dut_name, sonic_topo, recover_by_reboot],
                           tries=3, delay=30, logger=logger)

    @staticmethod
    def post_install_check_sonic(sonic_topo, dut_name, ansible_path):
        """
        Method which doing post install checks: check ports status, check dockers status, etc.
        :param sonic_topo: the topo for SONiC testing, for example: t0, t1, t1-lag, ptf32
        :param dut_name: dut name
        :param ansible_path: path to ansible directory
        """
        if sonic_topo != 'ptf-any':
            SonicInstallationSteps.post_install_check(ansible_path=ansible_path, dut_name=dut_name,
                                                      sonic_topo=sonic_topo)

    @staticmethod
    def upgrade_switch(topology_obj, dut_name, setup_name, platform_params, sonic_topo, deploy_type,
                       apply_base_config, target_version, wjh_deb_url, is_shutdown_bgp, ansible_path,
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
        :param wjh_deb_url: WJH url
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
                                                    wjh_deb_url=wjh_deb_url, deploy_type=deploy_type,
                                                    apply_base_config=apply_base_config,
                                                    reboot_after_install=reboot_after_install,
                                                    is_shutdown_bgp=is_shutdown_bgp, fw_pkg_path=fw_pkg_path, cli=cli)
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
        if SonicInstallationSteps.is_additional_apps_argument_is_deb_package(additional_apps):
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
        if SonicInstallationSteps.is_additional_apps_argument_is_app_ext_dict(additional_apps):
            app_extension_dict_path = additional_apps
            if app_extension_dict_path:
                with allure.step("Install supported app extension"):
                    SonicInstallationSteps.install_supported_app_extensions(ansible_path=ansible_path,
                                                                            setup_name=setup_name,
                                                                            app_extension_dict_path=app_extension_dict_path,
                                                                            dut_name=dut_name)
