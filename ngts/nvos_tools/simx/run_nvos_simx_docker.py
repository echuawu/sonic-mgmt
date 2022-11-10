import logging
import pytest
import allure
import os

logger = logging.getLogger()

path_to_source_code = "/.autodirect/sw_system_release/nos/nvos/yana-dev/simx_repo/sx_ver_build_scripts/simx_docker"


@pytest.mark.platform
def test_run_nvos_simx_docker(topology_obj):
    with allure.step("Check existence of relevant files"):
        assert os.path.isdir(path_to_source_code), "Relevant script files can't be found in " \
                                                   + path_to_source_code

    with allure.step("Start the NVOS simx docker"):
        dut_engine = topology_obj.players['dut']['engine']
        server_engine = topology_obj.players['server']['engine']
        output = server_engine.run_cmd("{path_to_repo}/run_nvos_vm_in_docker.py --user {username} --ip {ip} "
                                       "--image onie_simx_chipsim:1.0.235".format(path_to_repo=path_to_source_code,
                                                                                  ip=dut_engine.ip,
                                                                                  username=dut_engine.username))
        assert "Docker container is running" in output, "Failed to start simx docker"
