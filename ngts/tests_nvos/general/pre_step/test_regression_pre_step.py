import logging
import datetime as dt
from ngts.constants.constants import LinuxConsts
from ngts.helpers.secure_boot_helper import SecureBootHelper
from ngts.tools.test_utils import allure_utils as allure
import subprocess
import shlex
import os
import time
import pytest
from retry import retry
from infra.tools.validations.traffic_validations.port_check.port_checker import check_port_status_till_alive

logger = logging.getLogger()

REBOOT_CMD_TO_RUN = "ipmitool -I lanplus -H {server_name}-ilo -U root -P 3tango11 chassis power cycle"
SONIC_MGMT_HYPERVISOR = "fit-nvos-vrt-60"


@pytest.mark.no_cli_coverage_run
def test_regression_pre_step(engines, topology_obj):
    """
    Check that dut is reachable.
    If not, will reboot and try to recover
    """
    res = True
    info = ""
    server_engine = None
    vms_to_check = [SONIC_MGMT_HYPERVISOR]

    if "server" in topology_obj.players:
        server_engine = topology_obj.players['server']['engine']
        vms_to_check.append(topology_obj.players['server']['attributes'].noga_query_data['attributes']['Common']['Name'])

    with allure.step(f"Verify DUT {engines.dut.ip} is reachable and functional"):
        if not ping_device(engines.dut.ip):
            res = remote_reboot_dut(topology_obj)
            if res:
                with allure.step("Try to ping dut after remote reboot"):
                    logging.info("Try to ping dut after remote reboot")
                    wait_till_dut_is_up(engines)
                    res = ping_device(engines.dut.ip)

            if not res:
                logging.info(f"dut {engines.dut.ip} is unreachable")

                with allure.step('Generate techsupport to investigate the problem'):
                    serial_engine = SecureBootHelper.get_serial_engine(topology_obj)
                    serial_engine.run_cmd('nv action generate system tech-support')

                # with allure.step('Try to resolve issue by fixing system time'):
                #     serial_engine = SecureBootHelper.get_serial_engine(topology_obj)
                #     serial_engine.run_cmd('nv unset system ; nv config apply -y')
                #     serial_engine.run_cmd('nv unset interface ; nv config apply -y')
                #     serial_engine.run_cmd(f'sudo timedatectl set-timezone {LinuxConsts.JERUSALEM_TIMEZONE}')
                #     serial_engine.run_cmd(
                #         f'sudo timedatectl set-time "{dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"')
                #     res = ping_device(engines.dut.ip)
                #     logging.info(f'dut {engines.dut.ip} is {"still un" if res else "now "}reachable')

    info = ""
    for vm in vms_to_check:
        with allure.step(f"Make sure {vm} is up"):
            if not ping_device(vm):
                reboot_server(vm)
                res = ping_device(vm)
                if not res:
                    info += f"Hypervisor {vm} is unreachable\n"

    assert res, info

    if server_engine:
        with allure.step("Configure traffic server"):
            output = server_engine.run_cmd("docker ps")
            if "Is the docker daemon running?" in output:
                server_engine.run_cmd("sudo service docker start")
            server_engine.run_cmd("sudo groupadd docker")
            server_engine.run_cmd("sudo usermod -aG docker $USER")
            server_engine.run_cmd("sudo chgrp docker /var/run/docker.sock")


def ping_device(ip_add):
    try:
        return _ping_device(ip_add)
    except BaseException as ex:
        logging.error(str(ex))
        logging.info(f"ip address {ip_add} is unreachable")
        return False


@retry(Exception, tries=5, delay=10)
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
        logging.info("Sleep for 5 min")
        time.sleep(300)
        logging.info(f"Reboot completed for '{server_name}'")
