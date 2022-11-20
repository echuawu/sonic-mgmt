import logging
import pytest
import allure
import os
import time

logger = logging.getLogger()

path_to_source_code = "/.autodirect/sw_system_release/nos/nvos/yana-dev/simx_repo/sx_ver_build_scripts/simx_docker"


@pytest.mark.platform
def test_run_nvos_simx_docker(topology_obj, base_version):
    with allure.step("Check existence of relevant files"):
        assert os.path.isdir(path_to_source_code), "Relevant script files can't be found in " \
                                                   + path_to_source_code

    with allure.step("Start the NVOS simx docker"):
        dut_engine = topology_obj.players['dut']['engine']
        server_engine = topology_obj.players['server']['engine']
        output = server_engine.run_cmd("{path_to_repo}/run_nvos_vm_in_docker.py --user {username} --ip {ip} "
                                       "--nos-image {path_to_image}".format(path_to_repo=path_to_source_code,
                                                                            ip=dut_engine.ip,
                                                                            username="nvos_reg",
                                                                            path_to_image=base_version))
        assert "Docker container is running" in output, "Failed to start simx docker"

    with allure.step("Wait untill the switch is ready (~10-12 min)"):
        dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
        all_components_are_up = False
        timeout = 15    # min
        while not all_components_are_up and timeout > 0:
            output = server_engine.run_cmd('docker exec {user}-{dut_name} systemctl status chipsim fw simx | '.format(
                user="nvos_reg", dut_name=dut_name) + 'grep Active:')
            if "inactive" not in output and "activating" not in output:
                all_components_are_up = True
            else:
                timeout -= 1
                time.sleep(60)

        assert timeout > 0, "Timeout during simx docker initiation"
        assert all_components_are_up, "Failed to initiate simx docker components"
        logging.info("All simx docker components are active")
