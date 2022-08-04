import pytest
import allure
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.ConfigTool import ConfigTool
from ngts.constants.constants_nvos import SystemConsts, ConfigConsts
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.ib.InterfaceConfiguration.MgmtPort import MgmtPort
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit


@pytest.mark.general
def test_show_diff_history(engines):
    """
    Test flow:
        1. run nv config history - save as history_output1
        2. run nv config show - save as show_output1
        3. run nv config diff - save as diff_output1
        4. run nv set system hostname <new_hostname>
        5. run nv config diff - save as diff_output2
        6. run nv config apply
        7. run nv config history - save as history_output2
        8. run nv config show - save as show_output2
        9. run nv config diff - save as diff_output3
        10. verify diff_output3 is empty
        11. verify diff_output2 = diff_output1 + hostname: new_hostname
        12. verify show_output2 = show_output1 + hostname: new_hostname
        13. verify size(history_output2) = size(history_output1) + 1
        14. verify history_output2 last apply_id = n/size(history)  value, user name = hostname
        15. run nv unset system hostname
        16. run nv config diff - save as diff_output4
        17. verify hostname in diff_output4
        18. run nv config apply
    """
    err_message = ''
    with allure.step('Run show system command and verify that each field has a value'):
        system = System()
        with allure.step('saving the current diff, history and show outputs'):
            show_before_set, diff_before_set, history_before_set = save_diff_hisoty_show_outputs(engines.dut)

        new_hostname_value = 'TestingConfigCmds'
        with allure.step('set hostname to be {hostname} - without apply'.format(hostname=new_hostname_value)):
            system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME, False)

        with allure.step('saving the diff, history and show outputs after set hostname without apply'):
            show_after_set, diff_after_set, history_after_set = save_diff_hisoty_show_outputs(engines.dut)

        with allure.step('apply hostname set configuration'):
            NvueGeneralCli.apply_config(engines.dut, True)

        with allure.step('saving the diff, history and show outputs after applying the hostname'):
            show_after_apply, diff_after_apply, history_after_apply = save_diff_hisoty_show_outputs(engines.dut)

        with allure.step('unset hostname - without apply'.format(hostname=new_hostname_value)):
            system.unset(engines.dut, SystemConsts.HOSTNAME, False)

        with allure.step('saving the diff, history and show outputs after unset hostname without apply'):
            show_after_unset, diff_after_unset, history_after_unset = save_diff_hisoty_show_outputs(engines.dut)

        with allure.step('apply hostname unset configuration'):
            NvueGeneralCli.apply_config(engines.dut, True)

        with allure.step('saving the diff, history and show outputs after applying the hostname'):
            show_after_unset_apply, diff_after_unset_apply, history_after_unset_apply = save_diff_hisoty_show_outputs(engines.dut)

        with allure.step('unset system - with apply'):
            system.unset(engines.dut)

        with allure.step('saving the diff, history and show outputs after running unset system with apply'):
            show_after_unset_all, diff_after_unset_all, history_after_unset_all = save_diff_hisoty_show_outputs(
                engines.dut)

        with allure.step('verify diff command outputs'):
            err_message += verify_diff_outputs(diff_before_set, diff_after_set, diff_after_apply, diff_after_unset, diff_after_unset_apply,
                                               diff_after_unset_all)

        with allure.step('verify show command outputs'):
            err_message += verify_show_outputs(show_before_set, show_after_set, show_after_apply, show_after_unset, show_after_unset_apply,
                                               show_after_unset_all)

        with allure.step('verify history command outputs'):
            err_message += verify_history_outputs(history_before_set, history_after_set, history_after_apply, history_after_unset,
                                                  history_after_unset_apply, history_after_unset_all, engines.dut.username)

        assert err_message == '', '{message}'.format(message=err_message)


@pytest.mark.general
def test_diff_history_revision_ids(engines):
    """
        Test flow:
            1. run nv set system hostname <new_hostname> with apply
            2. run nv set interface ib0 description <new_description> with apply
            3. run nv set interface eth0 description <new_description> with apply
            4. run nv config history - save as history_output1
            5. get last 3 rev id's using history_output1
            6. run nv config diff one_configs_back_revision two_configs_back_revision
            7. verify it includes the first config only
            6. run nv config diff two_configs_back_revision rev_id3
            9. verify it includes the second config only
            10. run nv config diff one_configs_back_revision rev_id3
            11. verify it includes both configs
            12. run nv config history rev_id3
            13. verify it's same as output1
        """
    err_message = ''
    with allure.step('Run show system command and verify that each field has a value'):
        with allure.step('get the curring config history'):
            history_output_base = OutputParsingTool.parse_config_history(NvueGeneralCli.history_config(engines.dut)) \
                .get_returned_value()
        system = System()
        new_hostname_value = 'TestingConfigCmds'
        with allure.step('set hostname to be {hostname} - with apply'.format(hostname=new_hostname_value)):
            system.set(new_hostname_value, engines.dut, SystemConsts.HOSTNAME)

        ib0_port = MgmtPort('ib0')
        new_ib0_description = '"ib0description"'
        with allure.step('set ib0 description to be {description} - with apply'.format(
                description=new_ib0_description)):
            ib0_port.interface.description.set(value=new_ib0_description, apply=True).verify_result()

        new_ib0_description = '"testingsecond"'
        with allure.step('set ib0 description to be {description} - with apply'.format(
                description=new_ib0_description)):
            ib0_port.interface.description.set(value=new_ib0_description, apply=True).verify_result()

        with allure.step('get the last revision ids - all test applies'):
            history_output = OutputParsingTool.parse_config_history(NvueGeneralCli.history_config(engines.dut))\
                .get_returned_value()

            one_configs_back_revision = ConfigTool.read_from_history(history_output, 1, 'rev_id').get_returned_value()
            two_configs_back_revision = ConfigTool.read_from_history(history_output, 2, 'rev_id').get_returned_value()

        with allure.step('verify history before 3 applies is equal to base output'):
            history_output_rev2 = OutputParsingTool.parse_config_history(
                NvueGeneralCli.history_config(engines.dut, two_configs_back_revision)).get_returned_value()

            if history_output_rev2 != history_output_base:
                err_message += '\n after applying 3 times the history of two revision back ' \
                               'should be history before apply'

        with allure.step('verify diff between revision1 and revision0'):
            diff_output_rev0_rev1 = OutputParsingTool.parse_json_str_to_dictionary(
                NvueGeneralCli.diff_config(engines.dut, one_configs_back_revision, two_configs_back_revision)).get_returned_value()

            if diff_output_rev0_rev1 == {}:
                err_message += '\n after applying 3 times the diff between two revision back and two revision back ' \
                               'should include the first configuration we applied'

        with allure.step('unset system - with apply'):
            system.unset(engines.dut)
            engines.dut.run_cmd('nv unset interface')
            NvueGeneralCli.apply_config(engines.dut)
    with allure.step('validate the test results'):
        assert err_message == '', '{message}'.format(message=err_message)


def validate_history_labels(history_list, username):
    """
    validate apply_id value, user value of a specific apply
    :param username: the user name
    :param history_list: history
    :return: err message
    """
    err_message = ''
    apply_id = ConfigTool.read_from_history(history_list, 0, ConfigConsts.HISTORY_APPLY_ID).get_returned_value()
    user = ConfigTool.read_from_history(history_list, 0, ConfigConsts.HISTORY_USER).get_returned_value()

    if user != username:
        err_message += 'the user is not equal to the user name'

    if apply_id != 'n/' + str(len(history_list)):
        err_message += 'the apply_id is not as expected, should be apply_<applies_amount>'

    return err_message


def verify_diff_outputs(diff1, diff2, diff3, diff4, diff5, diff6):
    """
    :param diff1: diff_before_set
    :param diff2: diff_after_set
    :param diff3: diff_after_apply
    :param diff4: diff_after_unset
    :param diff5: diff_after_unset_apply
    :param diff6: diff_after_unset_all
    :return: error message if one of diff1, diff3, diff5, diff6 is not empty
            or if one of diff2, diff4 is does not include the configuration

    """
    err_message = ''
    with allure.step('verify diff commands after apply'):
        if diff1 != {} or diff3 != {} or diff5 != {} or diff6 != {}:
            err_message += '\n the diff output should be empty after applying the configurations'

    with allure.step('verify diff commands after set and before apply'):
        if diff2 == {} or diff4 == {}:
            err_message += '\n the diff output should include the configuration'

    return err_message


def verify_show_outputs(show1, show2, show3, show4, show5, show6):
    """
    :param show1: show_before_set
    :param show2: show_after_set
    :param show3: show_after_apply
    :param show4: show_after_unset
    :param show5: show_after_unset_apply
    :param show6: show_after_unset_all
    :return: error message if one of show1, show2, show6 is not empty
                or if any of show3, show4, show5 does not include the configuration

    """
    err_message = ''
    with allure.step('verify show commands before apply'):
        if show1 != {} or show2 != {} or show6 != {}:
            err_message += '\n the show output should be empty before applying the configurations'

    with allure.step('verify show commands after set and apply'):
        if show3 == {} or show4 == {} or show5 == {}:
            err_message += '\n the show output should include the configuration'

    return err_message


def verify_history_outputs(history1, history2, history3, history4, history5, history6, username):
    """
    :param history1: history_before_set
    :param history2: history_after_set
    :param history3: history_after_apply
    :param history4: history_after_unset
    :param history5: history_after_unset_apply
    :param history6: history_after_unset_all
    :param username: the user name who configured the last configuration
    :return: error message if history1 and history2 are not equal
                or history3 and history4 are not equal
                or nothing added to history3
                or nothing added to history5
                or nothing added to history6
    """
    err_message = ''
    with allure.step('verify history commands before apply'):
        if history1 != history2 or history3 != history4:
            err_message += '\n the history output should not change before applying'

    with allure.step('verify history commands after first apply'):
        if len(history2) != len(history3) - 1 or len(history4) != len(history5) - 1 or len(history5) != len(history6) - 1:
            err_message += '\n the history output should add the new apply_id'
    err_message += validate_history_labels(history6, username)
    return err_message


def save_diff_hisoty_show_outputs(engine):
    """
    saving the output if diff and show and history commands
    after each set/unset/apply running
    :param engine:
    :return:three outputs
    """
    with allure.step('saving the current diff, history and show outputs'):
        show_output = OutputParsingTool.parse_json_str_to_dictionary(
            TestToolkit.GeneralApi[TestToolkit.tested_api].show_config(engine)).get_returned_value()
        diff_output = OutputParsingTool.parse_json_str_to_dictionary(
            TestToolkit.GeneralApi[TestToolkit.tested_api].diff_config(engine)).get_returned_value()
        history_output = OutputParsingTool.parse_config_history(
            TestToolkit.GeneralApi[TestToolkit.tested_api].history_config(engine)).get_returned_value()
    return show_output, diff_output, history_output
