import logging
import pytest
import allure
import os
import time
from retry import retry

logger = logging.getLogger()

path_to_source_code = "/.autodirect/sw_system_project/NVOS_INFRA/ChipSim/simx_repo/sx_ver_build_scripts/simx_docker"


@pytest.mark.platform
def test_run_nvos_simx_docker(topology_obj, base_version):
    dut_engine = topology_obj.players['dut']['engine']
    server_engine = topology_obj.players['server']['engine']
    dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']

    with allure.step("Check existence of relevant files"):
        assert os.path.isdir(path_to_source_code), "Relevant script files can't be found in " + path_to_source_code

    with allure.step("Start the NVOS simx docker"):
        start_simx_docker(base_version, dut_engine, server_engine)

    with allure.step("Wait until the switch is ready (~10-12 min)"):
        wait_till_the_switch_is_ready(dut_name, server_engine)


@retry(Exception, tries=3, delay=10)
def start_simx_docker(base_version, dut_engine, server_engine):
    output = server_engine.run_cmd("sudo {path_to_repo}/run_nvos_vm_in_docker.py --user nvos_reg --ip {ip} "
                                   "--nos-image {path_to_image}".format(path_to_repo=path_to_source_code,
                                                                        ip=dut_engine.ip,
                                                                        path_to_image=base_version))
    time.sleep(5)
    assert "Docker container is running" in output, "Failed to start simx docker"


def wait_till_the_switch_is_ready(dut_name, server_engine):
    try:
        all_components_are_up = check_docker_status(server_engine, dut_name)
    except BaseException:
        raise Exception("Timeout during simx docker initiation")

    assert all_components_are_up, "Failed to initiate simx docker components"
    logging.info("All simx docker components are active")


@retry(Exception, tries=15, delay=60)
def check_docker_status(server_engine, dut_name):
    output = server_engine.run_cmd(f'sudo docker exec nvos_reg-{dut_name} systemctl status chipsim fw simx')
    if "Started SimX VM." in output:
        return True
    elif "Failed to start SimX VM." in output:
        return False
    raise Exception("Simx docker is not ready yet")
