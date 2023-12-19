import os
import pytest
from ngts.tests_nvos.general.security.conftest import check_if_need_remote_reboot_to_recover_dut
from ngts.tools.test_utils import allure_utils as allure
import logging
import subprocess
from retry import retry
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.nvue.nvue_system_clis import NvueSystemCli

logger = logging.getLogger()


@pytest.mark.general
@pytest.mark.disable_loganalyzer
@pytest.mark.no_log_test_wrapper
@pytest.mark.no_cli_coverage_run
def test_post_checker(engines, topology_obj, dumps_folder, setup_name, aaa_post_checker):
    """
    Post checker flow:
        1. Check if ssh port is open and we can connect to it
        2. If no connection generate sysdump
        3. Check if we have uncleaned configuration after test, clean it if exist
        4. Check if ssh port is open and we can connect to it
        5. If no connection generate sysdump
        6. Check if we have uncleaned configuration after test, clean it if exist
        7. If after cleanup we still have uncleaned configuration, perform reboot
        8. Check if ssh port is open, if not perform reboot
        9. Upload sysdump to shared location
    """
    if aaa_post_checker:
        check_if_need_remote_reboot_to_recover_dut(topology_obj, engines)

    system = System()
    serial_engine = topology_obj.players['dut_serial']['engine']
    remote_reboot = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['remote_reboot']
    hypervisor_bringup = 'PYTHONPATH=/ngts_venv/ ' \
                         '/ngts_venv/bin/python ' \
                         '/root/mars/workspace/sonic-mgmt/ngts/nvos_tools/hypervisor/VerifyServerFunctionality.py ' \
                         '-u root -p 3tango11 -s all '
    hosts_bringup = 'PYTHONPATH=/ngts_venv/ /ngts_venv/bin/python ' \
                    '/devts/scripts/docker/containers_bringup.py --setup_name {} --metrox2xc_setup'.format(setup_name)
    try:
        with allure.step('Check dut is up'):
            ping_device(engines.dut)
            DutUtilsTool.wait_for_nvos_to_become_functional(engines.dut).verify_result()
    except Exception as err:
        logger.info(str(err))
        logger.info("dut {} is unreachable".format(engines.dut.ip))
        with allure.step('Run remote reboot and check it go up'):
            subprocess.check_output(remote_reboot, shell=True, universal_newlines=True)
            DutUtilsTool.wait_for_nvos_to_become_functional(engines.dut).verify_result()
    if hasattr(engines, 'ha') and hasattr(engines, 'hb'):
        try:
            with allure.step('Check traffic hosts and hypervisor are up'):
                ping_device(engines.ha)
                ping_device(engines.hb)
        except Exception as err:
            logger.info(str(err))
            logger.info("dut {} is unreachable".format(engines.dut.ip))
            with allure.step('Run reboot on hypervisor and bringup containers'):
                subprocess.check_output(hypervisor_bringup, shell=True, universal_newlines=True)
                subprocess.check_output(hosts_bringup, shell=True, universal_newlines=True)
    try:
        check_port_status_till_alive(True, engines.dut.ip, engines.dut.ssh_port, tries=3, delay=2)
    except Exception as err:
        with allure.step('Generating a sysdump'):
            tar_file, duration = system.techsupport.action_generate(engine=serial_engine)
            logger.info("Dump was created at: {}".format(tar_file))
            tarball_file_name = str(tar_file.replace('/var/dump/', ''))

        with allure.step('Check if we have not cleaned config'):
            show_output = OutputParsingTool.parse_json_str_to_dictionary(
                TestToolkit.GeneralApi[TestToolkit.tested_api].show_config(serial_engine)).get_returned_value()
            if len(show_output) != 0:
                logger.info("Not cleaned config after test: {}".format(show_output))
                with allure.step('The config is not empty - try to cleanup the config'):
                    clear_config(engine=serial_engine)

                    with allure.step('Check if we have not cleaned config after cleanup'):
                        show_output = OutputParsingTool.parse_json_str_to_dictionary(
                            TestToolkit.GeneralApi[TestToolkit.tested_api].show_config(serial_engine))\
                            .get_returned_value()
                        if len(show_output) != 0:
                            logger.info("Not cleaned config after clean up: {}".format(show_output))

                        with allure.step('Check connection and perform reboot if needed'):
                            try:
                                logger.info('Check port status, should be up after cleanup')
                                check_port_status_till_alive(True, engines.dut.ip, engines.dut.ssh_port,
                                                             tries=15, delay=2)
                            except Exception as err:
                                logger.info('System not up after cleanup, performing reboot to revive system')
                                system.reboot.action_reboot(engine=serial_engine)
            else:
                logger.info('System not up, performing reboot to revive system')
                system.reboot.action_reboot(engine=serial_engine)

        with allure.step('Copy dump: {} to log folder {}'.format(tarball_file_name, dumps_folder)):
            dest_file = dumps_folder + '/sysdump_' + tarball_file_name
            logger.info('Copy dump {} to log folder {}'.format(tar_file, dumps_folder))
            engines.dut.copy_file(source_file=tar_file, dest_file=dest_file, file_system='/', direction='get',
                                  overwrite_file=True, verify_file=False)
            os.chmod(dest_file, 0o777)
            logger.info('Dump file location: {}'.format(dest_file))


@retry(Exception, tries=5, delay=10)
def ping_device(dut):
    ip_add = dut.ip
    logger.info("Ping {}".format(dut))
    cmd = "ping -c 3 {}".format(ip_add)
    logger.info("Running cmd: {}".format(cmd))
    output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
    logger.info("output: " + str(output))
    if " 0% packet loss" in str(output):
        logger.info("Reachable using ip address: " + ip_add)
        return True
    else:
        logger.error("ip address {} is unreachable".format(ip_add))
        raise Exception("ip address {} is unreachable".format(ip_add))


def clear_config(engine):
    try:
        NvueGeneralCli.detach_config(engine)
        NvueSystemCli.unset(engine, 'system')
        NvueSystemCli.unset(engine, 'ib')
        NvueSystemCli.unset(engine, 'interface')
        NvueGeneralCli.apply_config(engine=engine, option='--assume-yes')
    except Exception as err:
        logging.warning("Failed to detach config:" + str(err))
