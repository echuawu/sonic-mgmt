import logging
import allure
import subprocess
import shlex
import os
import time
import pytest
from retry import retry
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive

logger = logging.getLogger()

REBOOT_CMD_TO_RUN = "ipmitool -I lanplus -H {server_name}-ilo -U root -P 3tango11 chassis power cycle"


@pytest.mark.no_cli_coverage_run
def test_regression_pre_step(engines, topology_obj):
    """
    Check that dut is reachable.
    If not, will reboot and try to recover
    """
    res = True
    info = ""

    with allure.step(f"Verify DUT {engines.dut.ip} is reachable and functional"):
        if not ping_device(engines.dut.ip):
            res = remote_reboot_dut(topology_obj)
            if res:
                with allure.step("Try to ping dut after remote reboot"):
                    logging.info("Try to ping dut after remote reboot")
                    wait_till_dut_is_up(engines)
                    res = ping_device(engines.dut.ip)
                    info = f"dut {engines.dut.ip} is unreachable"

    if "server" in topology_obj.players:
        with allure.step(f"Verify server {engines.server.ip} is reachable"):
            if not ping_device(engines.server.ip):
                server_name = topology_obj.players['server']['attributes'].noga_query_data['attributes']['Common']['Name']
                reboot_server(server_name)
                res = ping_device(engines.server.ip)
                info += f"server {engines.dut.ip} is unreachable"

    assert res, info


def ping_device(ip_add):
    try:
        return _ping_device(ip_add)
    except BaseException as ex:
        logging.error(str(ex))
        logging.info(f"ip address {ip_add} is unreachable")
        return False


@retry(Exception, tries=5, delay=3)
def _ping_device(ip_add):
    with allure.step(f"Ping device ip {ip_add}"):
        cmd = f"ping -c 3 {ip_add}"
        logging.info(f"Running cmd: {cmd}")
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        output, error = process.communicate()
        logging.info("output: " + str(output))
        logging.info("error: " + str(error))
        if " 0% packet loss" in str(output):
            logging.info("Reachable using ip address: " + ip_add)
            return True
        else:
            logging.error("Unreachable using ip address: " + ip_add)
            logging.info(f"ip address {ip_add} is unreachable")
            raise Exception(f"ip address {ip_add} is unreachable")


def remote_reboot_dut(topology_obj):
    with allure.step("Remote reboot DUT"):
        cmd = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['remote_reboot']
        logging.info(f"Running cmd: {cmd}")
        p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            std_out, std_err = p.communicate(timeout=60)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            logger.debug('Process is not responding. Sending SIGKILL.')
            p.kill()
            std_out, std_err = p.communicate()
            rc = p.returncode
            std_out = str(std_out.decode('utf-8') or '')
            std_err = str(std_err.decode('utf-8') or '')
            logging.info(f"std_out = {std_out}, std_err = {std_err}")
        return rc == 0


def wait_till_dut_is_up(engines):
    with allure.step('Waiting for switch to bring-up after reload'):
        logger.info('Waiting for switch to bring-up after reload')
        check_port_status_till_alive(should_be_alive=True, destination_host=engines.dut.ip,
                                     destination_port=engines.dut.ssh_port)


def reboot_server(server_name):
    with allure.step(f"Reboot server {server_name}"):
        logging.info(f"--- Rebooting '{server_name}'")
        cmd = REBOOT_CMD_TO_RUN.format(server_name=server_name)
        logging.info(f"cmd: {cmd}")
        os.system(cmd)
        logging.info("Sleep for 2 min")
        time.sleep(120)
        logging.info(f"Reboot completed for '{server_name}'")
