import logging
import pytest
import allure
from ngts.nvos_tools.infra.Tools import Tools

logger = logging.getLogger()


@pytest.mark.general
def test_start_open_sm(topology_obj):
    """
    Start OpenSM
    """
    with allure.step('Connecting to hypervisor'):
        engine = topology_obj.players['ha']['engine']

    with allure.step('Check if OpenSM is already running'):
        if Tools.OpenSmTool.verify_open_sm_is_running(engine):
            logging.info("OpenSM is already running")
            pytest.exit(msg="OpenSM is running", returncode=0)
        else:
            logging.info("OpenSM is not running")

    with allure.step("Start OpenSM"):
        Tools.OpenSmTool.start_open_sm(engine)
