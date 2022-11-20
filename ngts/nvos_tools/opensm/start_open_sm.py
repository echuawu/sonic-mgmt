import logging
import pytest
import allure
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool
from dotted_dict import DottedDict
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit

logger = logging.getLogger()


@pytest.mark.general
def test_start_open_sm(topology_obj):
    """
    Start OpenSM
    """
    with allure.step('Connecting to hypervisor'):
        engines_data = DottedDict()
        engines_data.dut = topology_obj.players['dut']['engine']
        TestToolkit.update_engines(engines_data)

    with allure.step('Check if OpenSM is already running'):
        if OpenSmTool.verify_open_sm_is_running():
            logging.info("OpenSM is already running")
            pytest.exit(msg="OpenSM is running", returncode=0)
        else:
            logging.info("OpenSM is not running")

    with allure.step("Start OpenSM"):
        OpenSmTool.start_open_sm(TestToolkit.engines.dut)
