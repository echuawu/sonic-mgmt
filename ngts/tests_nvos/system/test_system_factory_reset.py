import logging
import allure
import pytest
import time
from datetime import datetime
from ngts.nvos_tools.system.System import System
from ngts.nvos_tools.platform.Platform import Platform
from ngts.nvos_tools.infra.Tools import Tools
from ngts.nvos_tools.ib.opensm.OpenSmTool import OpenSmTool
from ngts.nvos_constants.constants_nvos import SystemConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli

logger = logging.getLogger()


@pytest.mark.system
@pytest.mark.checklist
def test_reset_factory_without_params(engines, devices, topology_obj):
    """
    Validate reset factory without params cleanup done as expected

        Test flow:
            1. set description to ib ports:
                - set, apply and save configuration
                - set and apply
                - set
            2. Validate ports description
            3. Add data
            4. Run reset factory without params
            5. After system is up again, verify the cleanup done successfully
            6. Verify the setup is functional:
                6.1.	Start openSM
                6.2.	Run several show commands
                6.3.    Run set command & apply
    """
    with allure.step('Create System object'):
        system = System()

    with allure.step('Set description to ib ports'):
        logger.info("Set description to ib ports")
        description = "test_reset_factory_without_params"
        ports = Tools.RandomizationTool.select_random_ports(requested_ports_state=None,
                                                            num_of_ports_to_select=3).get_returned_value()
        apply_and_save_port = ports[0]
        just_apply_port = ports[1]
        not_apply_port = ports[2]

    '''with allure.step("Change profile to breakout mode"):
        _change_profile_to_breakout()

    with allure.step("Split a random port"):
        split_port = _split_port(engines.dut)'''

    with allure.step('Set and apply description to ib port, save config after it'):
        logger.info("Set and apply description to ib port, save config after it")
        apply_and_save_port.ib_interface.description.set(value=description, apply=True).verify_result()
        TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)
        NvueGeneralCli.save_config(engines.dut)
    with allure.step('Set and apply description to ib port'):
        logger.info("Set and apply description to ib port")
        just_apply_port.ib_interface.description.set(value=description, apply=True).verify_result()
    with allure.step('Set description to ib port'):
        logger.info("Set description to ib port")
        not_apply_port.ib_interface.description.set(value=description, apply=False).verify_result()
    with allure.step('Validate ports description'):
        logger.info("Validate ports description")
        _validate_port_description(engines.dut, apply_and_save_port, description)
        _validate_port_description(engines.dut, just_apply_port, description)
        _validate_port_description(engines.dut, not_apply_port, "")

    with allure.step("Add data before reset factory"):
        username = _add_verification_data(engines.dut, system)

    with allure.step("Run reset factory without params"):
        date_time_str = engines.dut.run_cmd("date").split(" ", 1)[1]
        current_time = datetime.strptime(date_time_str, '%d %b %Y %H:%M:%S %p %Z')
        logging.info("Current time: " + str(current_time))
        system.factory_default.action_reset().verify_result()

    with allure.step("Verify description has been deleted"):
        _validate_port_description(engines.dut, apply_and_save_port, "")
        _validate_port_description(engines.dut, just_apply_port, "")
        _validate_port_description(engines.dut, not_apply_port, "")

    with allure.step("Verify the cleanup done successfully"):
        _verify_cleanup_done(engines.dut, current_time, system, username)

    '''with allure.step("Verify the breakup mode is disabled and selected port is not split any more"):
        _verify_profile_and_split(split_port)'''

    with allure.step("Verify the setup is functional"):
        _verify_the_setup_is_functional(system, engines)


def _validate_port_description(engine, port, expected_description):
    output_dictionary = Tools.OutputParsingTool.parse_show_interface_output_to_dictionary(
        port.show_interface(engine, port.name)).get_returned_value()
    Tools.ValidationTool.verify_field_value_in_output(output_dictionary=output_dictionary,
                                                      field_name=port.ib_interface.description.label,
                                                      expected_value=expected_description).verify_result()


def _change_profile_to_breakout():
    logging.info("Change profile to breakout mode")
    logging.warning("Currently not supported")


def _split_port(engine):
    with allure.step("Start openSM"):
        OpenSmTool.start_open_sm(engine)
        time.sleep(7)

    with allure.step("Select an active random port"):
        logging.info("Select an active random port")
        random_port = Tools.RandomizationTool.get_random_active_port().get_returned_value()[0]

        with allure.step("Split selected port ({})".format(random_port.name)):
            logging.info("Split selected port ({})".format(random_port.name))
            logging.warning("Currently not supported")

    return random_port


def _create_date_time_obj(str_info):
    tmp_str = str_info.split()
    str_date_time = "{date} {time}".format(date=tmp_str[1], time=tmp_str[2].split('.')[0])
    datetime_object = datetime.strptime(str_date_time, '%Y-%m-%d %H:%M:%S')
    return datetime_object


def _add_verification_data(engine, system):
    with allure.step("Add file to /host/mlnx/images"):
        output = engine.run_cmd("ls /host/mlnx")
        if "No such file or directory" in output:
            output = engine.run_cmd("sudo mkdir /host/mlnx")
        output = engine.run_cmd("ls /host/mlnx/images")
        if "No such file or directory" in output:
            output = engine.run_cmd("sudo mkdir /host/mlnx/images")
        output = engine.run_cmd("sudo touch /host/mlnx/images/verification_test")

    with allure.step("Add file to /var/dump/"):
        output = engine.run_cmd("ls /var/dump/")
        if "No such file or directory" in output:
            output = engine.run_cmd("sudo mkdir /var/dump/")
        output = engine.run_cmd("sudo touch /var/dump/verification_test")

    with allure.step("Add history files to /home"):
        output = engine.run_cmd("ls /home")
        if ".bash_history" not in output:
            output = engine.run_cmd("sudo touch /home/.bash_history")
        if ".python_history" not in output:
            output = engine.run_cmd("sudo touch /home/.python_history")
        if ".viminfo" not in output:
            output = engine.run_cmd("sudo touch /home/.viminfo")
        output = engine.run_cmd("sudo touch /home/verification_test")

    with allure.step("Create new user"):
        username, password = system.create_new_user(engine)
        return username


def _verify_cleanup_done(engine, current_time, system, username):
    logging.info("Verify cleanup done as expected")
    errors = ""
    with allure.step("Verify NVUE reset done"):
        output = engine.run_cmd("stat /etc/sonic/nvue.d/platform/immutables.yaml | grep Birth")
        if output and "No such file or directory" not in output:
            file_date_time = _create_date_time_obj(output)
            if current_time >= file_date_time:
                errors += "\n/etc/sonic/nvue.d/platform/immutables.yaml was not deleted"

        output = engine.run_cmd("stat /etc/sonic/nvue.d/startup.yaml | grep Birth")
        if output and "No such file or directory" not in output:
            file_date_time = _create_date_time_obj(output)
            if current_time >= file_date_time:
                errors += "\n/etc/sonic/nvue.d/startup.yaml was not deleted"

    with allure.step("Verify sonic.target stopped"):
        output = engine.run_cmd("systemctl show sonic.target | grep StateChangeTimestamp=")
        if output:
            output = output.split('=')[1].split()
            file_date_time = _create_date_time_obj("date {} {}".format(output[1], output[2]))
            if current_time >= file_date_time:
                errors += "\nsonic.target probably was not stopped"

    with allure.step("Verify new DB was created"):
        output = engine.run_cmd("stat /etc/sonic/config_db.json | grep Birth")
        if output and "No such file or directory" not in output:
            file_date_time = _create_date_time_obj(output)
            if current_time >= file_date_time:
                errors += "\nnew /etc/sonic/config_db.json was not created"

    with allure.step("Verify NVOS HOOKs were deleted"):
        output = engine.run_cmd("ls /host/mlnx/images")
        if output and "No such file or directory" not in output:
            errors += "\nNVOS Hooks were not deleted"

    with allure.step("Verify tech-support files were deleted"):
        output = engine.run_cmd("ls /var/dump")
        if output and "No such file or directory" not in output:
            errors += "\ntech-support files were not deleted"

    with allure.step("Verify history was deleted"):
        output = engine.run_cmd("ls /home/.bash_history")
        if "No such file or directory" not in output:
            errors += "\n*.bash_history files were not deleted"
        output = engine.run_cmd("ls /home/.python_history")
        if "No such file or directory" not in output:
            errors += "\n*.python_history files were not deleted"
        output = engine.run_cmd("ls /home/.viminfo")
        if "No such file or directory" not in output:
            errors += "\n*.viminfo files were not deleted"
        output = engine.run_cmd("find /home/ -maxdepth 1 -type f ")

    with allure.step("Verify utmp files were cleared"):
        output = engine.run_cmd("stat /var/log/btmp | grep Size")
        if output and "No such file or directory" not in output:
            size = int(output.split()[1])
            if size != 0:
                errors += "\n/var/log/btmp was not cleared"

        output = engine.run_cmd("stat /var/log/lastlog | grep Modify")
        if output and "No such file or directory" not in output:
            file_date_time = _create_date_time_obj(output)
            if current_time >= file_date_time:
                errors += "\n/var/log/lastlog was not created"

        output = engine.run_cmd("stat /var/log/wtmp | grep Modify")
        if output and "No such file or directory" not in output:
            file_date_time = _create_date_time_obj(output)
            if current_time >= file_date_time:
                errors += "\n/var/log/wtmp was not created"

    with allure.step("Create new user"):
        output = Tools.OutputParsingTool.parse_json_str_to_dictionary(
            engine.run_cmd("nv show system aaa user -o json")).get_returned_value()
        if username in output.keys():
            errors += "\nCreated user was not deleted"

    assert not errors, errors


def _verify_profile_and_split(selected_port):
    logging.info("Verify the breakup mode is disabled and selected port is not split any more")
    with allure.step("Check profile"):
        logging.info("Check current profile")
        logging.warning("Currently not supported")

    with allure.step("Verify port {} in not in split mode".format(selected_port.name)):
        logging.info("Verify port {} in not in split mode".format(selected_port.name))
        logging.warning("Currently not supported")


def _verify_the_setup_is_functional(system, engines):
    logging.info("Verify the setup is functional")

    with allure.step("Start OpenSM"):
        OpenSmTool.start_open_sm(engines.dut).verify_result()

    with allure.step("Run show commands"):
        system.message.show()
        system.version.show()
        platform = Platform()
        platform.show()

    with allure.step("Run set and apply"):
        system.message.set("new_post_login_msg", engines.dut, SystemConsts.POST_LOGIN_MESSAGE).verify_result()

    with allure.step("Run unset and apply"):
        system.message.unset(engines.dut, SystemConsts.POST_LOGIN_MESSAGE).verify_result()


@pytest.mark.system
@pytest.mark.checklist
def test_error_flow_reset_factory_with_params(engines, devices, topology_obj):
    """
    This test is a temporary test - will be changed for GA
    :return:
    """
    with allure.step("Create system object"):
        system = System(None)

    with allure.step("Run reset factory with params - expect failure"):
        logging.info("Run reset factory with params - expect failure")
        output = engines.dut.run_cmd("nv action reset system factory-default only-config")
        assert "Invalid Command" in output, "Reset factory with param should fail"
        # system.factory_default.action_reset(param="only-config").verify_result(should_succeed=False)


# ------------ Open API tests -----------------

@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.checklist
def test_error_flow_reset_factory_with_params_openapi(engines, devices, topology_obj):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_error_flow_reset_factory_with_params(engines, devices, topology_obj)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.checklist
def test_reset_factory_without_params_openapi(engines, devices, topology_obj):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_reset_factory_without_params(engines, devices, topology_obj)
