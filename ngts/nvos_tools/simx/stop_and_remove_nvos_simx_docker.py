import logging
import allure
logger = logging.getLogger()


def test_stop_and_remove_nvos_simx_docker(topology_obj):
    with allure.step("Get server and dut details"):
        dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
        server_engine = topology_obj.players['server']['engine']

    stop_and_remove_reg_simx_docker(dut_name, server_engine)
    stop_all_nvos_simx_dockers(server_engine)


def test_stop_and_remove_reg_simx_docker(topology_obj):
    with allure.step("Get server and dut details"):
        dut_name = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Common']['Name']
        server_engine = topology_obj.players['server']['engine']

    stop_and_remove_reg_simx_docker(dut_name, server_engine)


def stop_and_remove_reg_simx_docker(dut_name, server_engine):
    with allure.step("Check docker id"):
        docker_info = server_engine.run_cmd("sudo docker ps -a | grep {}".format(dut_name))
        if docker_info:
            docker_id = docker_info.split()[0]
            logging.info("Simx docker id: {}".format(docker_id))

            with allure.step("Stop NVOS simx docker for {}".format(dut_name)):
                output = server_engine.run_cmd("sudo docker stop {}".format(docker_id))
                assert docker_id in output, "Failed to stop simx docker"

                if "nvos_reg-{}".format(dut_name) in docker_info:  # if this docker started by regression
                    with allure.step("Stop NVOS simx docker for {}".format(dut_name)):
                        output = server_engine.run_cmd("sudo docker rm {}".format(docker_id))
                        assert docker_id in output, "Failed to remove simx docker"
        else:
            logging.info("Simx docker is not running for {} - nothing to stop".format(dut_name))


def stop_all_nvos_simx_dockers(server_engine):
    try:
        with allure.step("Stop all SIMX dockers on current server"):
            dockers_info = server_engine.run_cmd("sudo docker ps")
            docker_info_list = dockers_info.split()[1:]
            for docker_info in docker_info_list:
                if "nvos_reg" not in docker_info:
                    docker_id = docker_info.split()[0]
                    with allure.step(f"Stop docker id {docker_id}"):
                        output = server_engine.run_cmd("sudo docker stop {}".format(docker_id))
                        if docker_id not in output:
                            logging.warning(f"Failed to stop simx docker {docker_id}")
    except Exception as err:
        logging.warning(f"Failed to stop simx dockers: {str(err)}")
