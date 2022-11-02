import logging
import allure
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
logger = logging.getLogger()


def test_capability_functionality(engines):
    """
    Run show system message command and verify the required message
        Test flow:
            1. run nv show system aaa user
            2. validate all fields have values
            3. run nv show system aaa user admin
            4. validate all fields have values
            5. run nv show system aaa user monitor
            6. validate all fields have values
    """
    system = System(None)
    admin_engine = system.create_new_connected_user(engine=engines.dut)
    monitor_engine = system.create_new_connected_user(engine=engines.dut, role=SystemConsts.DEFAULT_USER_MONITOR)
    is_monitor(engines, monitor_engine)
    is_admin(engines, admin_engine)


def is_monitor(engines, engine):
    monitor_message = 'You do not have permission to execute that command.'

    logger.info('setting the new engine as engine.dut and updating user name')
    system = System(None)
    tmp_engine = engines.dut
    engines.dut = engine
    TestToolkit.update_engines(engines)
    system.aaa.user.set_username(engine.username)

    with allure.step('testing capability positive flow'):
        show_output = OutputParsingTool.parse_json_str_to_dictionary(system.aaa.user.show()).get_returned_value()
        assert SystemConsts.USER_FULL_NAME in show_output, 'monitor can not set any configuration'

        output = NvueGeneralCli.diff_config(engine)
        assert not output, "monitor can run nv config diff"

        output = engine.run_cmd('cat /var/log/messages.1')
        assert output, "monitor can run nv config diff"

    with allure.step('testing capability negative flow'):
        out_set = system.aaa.user.set(SystemConsts.USER_FULL_NAME, 'TESTING').info
        assert monitor_message in out_set, 'monitor can not set any configuration'

        out_unset = system.aaa.user.unset(SystemConsts.USER_FULL_NAME).info
        assert monitor_message in out_unset, 'monitor can not set any configuration'

        output = NvueGeneralCli.apply_config(engine)

    logger.info('update engine.dut')
    engines.dut = tmp_engine
    TestToolkit.update_engines(engines)


def is_admin(engines, engine):
    logger.info('setting the new engine as engine.dut and updating user name')
    system = System(None)
    tmp_engine = engines.dut
    engines.dut = engine
    TestToolkit.update_engines(engines)
    system.aaa.user.set_username(engine.username)

    with allure.step('testing capability positive flow'):
        show_output = OutputParsingTool.parse_json_str_to_dictionary(system.aaa.user.show()).get_returned_value()
        assert SystemConsts.USER_FULL_NAME in show_output, 'monitor can not set any configuration'
        new_full_name = 'TESTING'
        system.aaa.user.set(SystemConsts.USER_FULL_NAME, new_full_name).get_returned_value()
        NvueGeneralCli.apply_config(engines.dut)
        system.aaa.user.verify_user_label(engine.username, SystemConsts.USER_FULL_NAME, new_full_name)

        system.aaa.user.unset(SystemConsts.USER_FULL_NAME)
        NvueGeneralCli.apply_config(engines.dut)
        system.aaa.user.verify_user_label(engine.username, SystemConsts.USER_FULL_NAME, '')

    logger.info('update engine.dut')
    engines.dut = tmp_engine
    TestToolkit.update_engines(engines)
