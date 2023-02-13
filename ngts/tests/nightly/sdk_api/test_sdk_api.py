import logging
import allure

logger = logging.getLogger()


def test_sdk_api_workability(engines):
    """
    Checks if SDK API command is working
    """
    logger.info("Checking SDK API workability")
    with allure.step("Checking SDK API workability"):
        sdk_cmd = "docker exec -it syncd /usr/bin/sx_api_ports_dump.py"
        engines.dut.run_cmd(sdk_cmd, validate=True)
