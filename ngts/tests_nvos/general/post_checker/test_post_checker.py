import logging
import os
import pytest
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive
from ngts.nvos_tools.infra.DutUtilsTool import DutUtilsTool
from ngts.nvos_tools.infra.TrafficGeneratorTool import TrafficGeneratorTool
from ngts.nvos_tools.system.System import System
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool
from ngts.tools.test_utils import allure_utils as allure
from ngts.tools.test_utils.nvos_config_utils import ib_clear_conf
from ngts.tools.test_utils.switch_recovery import check_switch_connectivity

logger = logging.getLogger()


@pytest.mark.general
@pytest.mark.disable_loganalyzer
@pytest.mark.no_log_test_wrapper
@pytest.mark.no_cli_coverage_run
def test_post_checker(engines, topology_obj, dumps_folder, setup_name, security_post_checker):
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
    try:
        if security_post_checker:
            check_switch_connectivity(topology_obj, engines)

        with allure.step('Check dut is up'):
            if not ConnectionTool.ping_device(engines.dut.ip, num_of_retries=1):
                NvueGeneralCli(engines.dut).remote_reboot(topology_obj)

            res_obj = DutUtilsTool.wait_for_nvos_to_become_functional(engines.dut)

            if res_obj.result:
                with allure.step("Clear config"):
                    ib_clear_conf(engines.dut)
            else:
                logging.info("Try to clear the config using serial console")

                with allure.step("Create serial engine"):
                    system = System()
                    serial_engine = topology_obj.players['dut_serial']['engine']

                with allure.step("Try to generate techsupport using serial console"):
                    generate_techsupport(dumps_folder, system, serial_engine)

                with allure.step("Clear config using serial console"):
                    ib_clear_conf(serial_engine)

                with allure.step('Check connection and perform reboot if needed'):
                    logger.info('Check port status, should be up after cleanup')
                    if not check_if_dut_port_is_open(engines):
                        logger.info('System not up after cleanup, performing reboot to revive system')
                        NvueGeneralCli(engines.dut).remote_reboot(topology_obj)
                        DutUtilsTool.wait_for_nvos_to_become_functional(engines.dut).verify_result()

        if not security_post_checker:
            TrafficGeneratorTool.bring_up_traffic_containers(engines, setup_name)

    except BaseException as err:
        logging.error(f"Exception during post checker: {err}")
        raise err


def check_if_dut_port_is_open(engines):
    try:
        check_port_status_till_alive(True, engines.dut.ip, engines.dut.ssh_port, tries=3, delay=2)
        return True
    except BaseException:
        return False


def generate_techsupport(dumps_folder, system, serial_engine):

    with allure.step('Generating a sysdump'):
        tar_file, duration = system.techsupport.action_generate(engine=serial_engine)
        logger.info("Dump was created at: {}".format(tar_file))
        tarball_file_name = str(tar_file.replace('/var/dump/', ''))

    with allure.step('Copy dump: {} to log folder {}'.format(tarball_file_name, dumps_folder)):
        dest_file = dumps_folder + '/sysdump_' + tarball_file_name
        logger.info('Copy dump {} to log folder {}'.format(tar_file, dumps_folder))
        serial_engine.copy_file(source_file=tar_file, dest_file=dest_file, file_system='/', direction='get',
                                overwrite_file=True, verify_file=False)
        os.chmod(dest_file, 0o777)
        logger.info('Dump file location: {}'.format(dest_file))
