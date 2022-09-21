import logging
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
logger = logging.getLogger()


def test_saved_users_after_reboot(engines):
    """
        Test flow:
            1. create new user
            2. nv config save
            3. reboot
            4. verify user still
    """
    with allure.step('username after reboot testing '):
        system = System(None)
        viewer_name, viewer_password = system.create_new_user(engine=engines.dut, role=SystemConsts.ROLE_VIEWER)
        TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engines.dut)
        TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)
        configurator_name, configurator_password = system.create_new_user(engine=engines.dut)
        TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config(engines.dut)
        system.reboot.action_reboot()
        system.aaa.user.set_username('')
        output = OutputParsingTool.parse_json_str_to_dictionary(system.aaa.user.show()).get_returned_value()
        assert configurator_name not in output.keys(), "the not saved user {viewer} in the users list".format(viewer=viewer_name)
        assert viewer_name in output.keys(), "the saved user {viewer} not in the users list".format(
            viewer=configurator_name)
        system.unset(engines.dut)
        NvueGeneralCli.save_config(engines.dut)
