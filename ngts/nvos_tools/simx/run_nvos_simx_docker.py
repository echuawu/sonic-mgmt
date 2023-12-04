import logging
import pytest
import allure
import os
import time
from retry import retry
from ngts.nvos_tools.infra.ConnectionTool import ConnectionTool

logger = logging.getLogger()

path_to_source_code = "/auto/sw_system_project/NVOS_INFRA/ChipSim/nvos/scripts"
chipsim_script_file_name = "run_nvos_in_chipsim.py"


def test_run_nvos_simx_docker(topology_obj, target_version):
    dut_engine = topology_obj.players['dut']['engine']

    server_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['serial_conn_command'].split()[1]
    server_engine = ConnectionTool.create_ssh_conn(server_name, os.getenv("TEST_SERVER_USER"), os.getenv("TEST_SERVER_PASSWORD")).returned_value

    dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']

    with allure.step("Check existence of relevant files"):
        assert os.path.isdir(path_to_source_code), "Relevant script files can't be found in " + path_to_source_code

    with allure.step("Start the NVOS simx docker"):
        start_simx_docker(target_version, dut_engine, server_engine)

    with allure.step("Wait until the switch is ready (~5 min)"):
        wait_till_the_switch_is_ready(dut_engine.ip)

    with allure.step("Check installed image"):
        dut_engine.run_cmd('nv show system version')


@retry(Exception, tries=3, delay=10)
def start_simx_docker(target_version, dut_engine, server_engine):
    output = server_engine.run_cmd(f"sudo {path_to_source_code}/{chipsim_script_file_name} --ip {dut_engine.ip} "
                                   f"--nos-image {target_version}")
    time.sleep(5)
    assert "NOS installed successfully" in output, "Failed to start simx docker"


def wait_till_the_switch_is_ready(switch_ip):
    try:
        switch_is_ready = ConnectionTool.ping_device(switch_ip)
    except BaseException:
        raise Exception("Timeout during simx docker initiation")

    assert switch_is_ready, "Failed to initiate simx docker components"
    logging.info("All simx docker components are active")
