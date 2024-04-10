from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.tests_nvos.general.security.tpm_attestation.helpers import factory_reset_tpm_checker
from ngts.tests_nvos.system.factory_reset.helpers import *
from ngts.tools.test_utils import allure_utils as allure


def factory_reset_no_params_pre_steps(engines, platform_params, system):
    with allure.step("Check if setup had SM before test"):
        have_sm_before_test = OpenSmTool.verify_open_sm_is_running()
        logging.info(f'SM is{" not" if not have_sm_before_test else ""} running before factory reset')

    with allure.step('Create System object'):
        machine_type = platform_params['filtered_platform']

    if machine_type != 'MQM9520':
        with allure.step('Validate health status is OK'):
            system.validate_health_status(HealthConsts.OK)
            last_status_line = system.health.history.retry_get_health_history_file_summary_line()

    with allure.step('Set description to ib ports'):
        logger.info("Set description to ib ports")
        description = "test_reset_factory_without_params"
        ports = Tools.RandomizationTool.select_random_ports(requested_ports_state=None,
                                                            num_of_ports_to_select=3).get_returned_value()
        apply_and_save_port = ports[0]
        just_apply_port = ports[1]
        not_apply_port = ports[2]

    with allure.step('Set and apply description to ib port, save config after it'):
        logger.info("Set and apply description to ib port, save config after it")
        apply_and_save_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=True).verify_result()
        TestToolkit.GeneralApi[TestToolkit.tested_api].save_config(engines.dut)
        NvueGeneralCli.save_config(engines.dut)

    with allure.step('Set and apply description to ib port'):
        logger.info("Set and apply description to ib port")
        just_apply_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=True).verify_result()

    with allure.step('Set description to ib port'):
        logger.info("Set description to ib port")
        not_apply_port.ib_interface.set(NvosConst.DESCRIPTION, description, apply=False).verify_result()

    with allure.step('Validate ports description'):
        logger.info("Validate ports description")
        validate_port_description(engines.dut, apply_and_save_port, description)
        validate_port_description(engines.dut, just_apply_port, description)
        validate_port_description(engines.dut, not_apply_port, "")

    with allure.step("Add data before reset factory"):
        username = add_verification_data(engines.dut, system)

    with allure.step("Get current time"):
        update_timezone(system)
        current_time = get_current_time(engines)

    with allure.step('pre factory reset TPM related check'):
        next(factory_reset_tpm_checker)

    return apply_and_save_port, current_time, just_apply_port, last_status_line, machine_type, not_apply_port, \
        username, have_sm_before_test
