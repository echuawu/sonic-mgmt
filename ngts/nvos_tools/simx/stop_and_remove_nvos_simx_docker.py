import logging
import pytest
import allure
logger = logging.getLogger()


@pytest.mark.platform
def test_stop_and_remove_nvos_simx_docker(topology_obj):
    with allure.step("Get server and dut details"):
        dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
        server_engine = topology_obj.players['server']['engine']

    with allure.step("Check docker id"):
        docker_info = server_engine.run_cmd("docker ps | grep {}".format(dut_name))
        if docker_info:
            docker_id = docker_info.split()[0]
            logging.info("Simx docker id: {}".format(docker_id))

            with allure.step("Stop NVOS simx docker for {}".format(dut_name)):
                output = server_engine.run_cmd("docker stop {}".format(docker_id))
                assert docker_id in output, "Failed to stop simx docker"

                if "nvos_reg-{}".format(dut_name) in docker_info:  # if this docker started by regression
                    with allure.step("Stop NVOS simx docker for {}".format(dut_name)):
                        output = server_engine.run_cmd("docker rm {}".format(docker_id))
                        assert docker_id in output, "Failed to remove simx docker"
        else:
            logging.info("Simx docker is not running for {} - nothing to stop".format(dut_name))
