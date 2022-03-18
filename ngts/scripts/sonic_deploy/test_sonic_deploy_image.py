#!/usr/bin/env python
import allure
import logging
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from retry.api import retry_call


logger = logging.getLogger()


@allure.title('Deploy sonic image')
def test_deploy_sonic_image(topology_obj, setup_name, platform_params, base_version, wjh_deb_url, deploy_type, apply_base_config,
                            reboot_after_install, is_shutdown_bgp, fw_pkg_path):
    """
    This script will deploy sonic image on the dut.
    :param topology_obj: topology object fixture
    :param setup_name: setup_name fixture
    :param platform_params: platform_params fixture
    :param base_version: path to sonic version to be installed
    :param wjh_deb_url: wjh_deb_url fixture
    :param deploy_type: deploy_type fixture
    :param apply_base_config: apply_base_config fixture
    :param reboot_after_install: reboot_after_install fixture
    :param is_shutdown_bgp: shutdown bgp flag, True or False
    :param fw_pkg_path: fw_pkg_path fixture
    :return: raise assertion error in case of script failure
    """
    dut_engine = topology_obj.players['dut']['engine']
    try:
        # when bgp is up, dut can not access the external IP such as fit69.mtl.labs.mlnx. So shutodwn bgp
        if is_shutdown_bgp:
            dut_engine.run_cmd('sudo config bgp shutdown all', validate=True)
            logger.info("Wait all bgp sessions are down")
            retry_call(check_bgp_is_shutdown,
                       fargs=[dut_engine],
                       tries=6,
                       delay=10,
                       logger=logger)
        SonicGeneralCli(engine=dut_engine).deploy_image(topology_obj, base_version, apply_base_config=apply_base_config,
                                                        setup_name=setup_name, platform_params=platform_params,
                                                        wjh_deb_url=wjh_deb_url, deploy_type=deploy_type,
                                                        reboot_after_install=reboot_after_install,
                                                        fw_pkg_path=fw_pkg_path)
    except Exception as err:
        raise AssertionError(err)
    finally:
        if is_shutdown_bgp:
            dut_engine.run_cmd('sudo config bgp startup all', validate=True)


def check_bgp_is_shutdown(dut_engine):
    assert dut_engine.run_cmd("show ip route bgp") == "" and dut_engine.run_cmd("show ipv6 route bgp") == "", \
        "Not all bgp sessions are down"
