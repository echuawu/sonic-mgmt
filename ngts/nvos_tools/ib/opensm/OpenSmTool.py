import allure
import pytest
import logging

logger = logging.getLogger()


class OpenSmTool:

    @staticmethod
    def start_open_sm(engine):
        """
        Start open sm if it's not running
        """
        with allure.step("Check if OpenSM is running"):
            output = engine.run_cmd("ibdev2netdev")
            if "(Up)" in output:
                pytest.exit(msg="OpenSM is already running", returncode=0)
            elif "(Down)" in output:
                port_name = output.split()[0]
            else:
                assert "ibdev2netdev command failed"

        with allure.step("Get GUID to start OpenSM"):
            output = engine.run_cmd("ibstat {}".format(port_name))
            guid = ''
            for line in output.splitlines():
                if "System image GUID" in line:
                    guid = line.split(":")[1]
            if guid:
                logging.info("GUID: " + guid)
            else:
                assert "Failed to find GUID to start OpenSM"

        with allure.step("Start OpenSM"):
            engine.run_cmd("opensm -g {} -B".format(guid))

        with allure.step("Verify OpenSM is running"):
            assert OpenSmTool.verify_open_sm_is_running(engine), "Failed to start OpenSM"

    @staticmethod
    def verify_open_sm_is_running(engine):
        output = engine.run_cmd("ibdev2netdev")
        if "(Up)" in output:
            logging.info("OpenSM is running")
            return True
        else:
            logging.info("OpenSM is down")
            return False
