import pytest
import time
import csv
import os

from datetime import datetime, timedelta
from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_constants.constants_nvos import ApiType, NvosConst, StatsConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.RedisTool import RedisTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simxl
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_system_stats_configuration(engines, devices, test_api):
    """
    validate:
    - Enable/Disable stats feature
    - Show system stats commands
    - Update stats category configuration
    - System stats actions (clear, delete)
    - Sampling interval and cache duration mechanism
    - New file (internal) is generated after clear command.

    Test flow:
    1. Disable system stats feature
    2. Disable all categories stats
    3. Clear all system stats and delete stats files
    4. Check internal and external files
    5. Select a random category and unset its configuration
    6. Update general configuration
    7. Update category configuration
    8. Wait 1 minute
    9. Check no files created when feature state is disabled
    10.	Enable feature and disable category
    11.	Wait 1 minute
    12.	Check no files created when feature state is disabled
    13.	Update general configuration
    14.	Enable category
    15.	Wait 2 minutes
    16.	Check internal and external files
    17.	Wait another 1 minute
    18.	Check internal and external files
    """

    TestToolkit.tested_api = test_api
    system = System(devices_dut=devices.dut)
    engine = engines.dut
    category_list = devices.dut.CATEGORY_LIST
    category_disabled_dict = devices.dut.CATEGORY_DISABLED_DICT
    category_list_default = devices.dut.CATEGORY_LIST_DEFAULT_DICT

    try:
        with allure.step("Set system stats feature to default"):
            system.stats.unset(apply=True).verify_result()

        with allure.step("Disable system stats feature"):
            system.stats.set(op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.DISABLED.value,
                             apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.DISABLED.value, \
                "stats state parameter is expected to be 'disabled'"

        with allure.step("Disable all categories stats"):
            for name in category_list:
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.DISABLED.value).verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            apply_config, TestToolkit.engines.dut, False).verify_result()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.category.show()). \
                get_returned_value()
            ValidationTool.compare_dictionary_content(stats_category_show, category_disabled_dict).verify_result()

        with allure.step("Clear all system stats and delete stats files"):
            clear_all_internal_and_external_files(system, category_list)

        with allure.step("Check both internal and external paths"):
            output = engine.run_cmd("ls /var/stats")
            assert not output or "No such file or directory" in output, "Category internal files were not cleared"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()). \
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure.step("Select a random category and unset its configuration"):
            name = RandomizationTool.select_random_value(category_list).get_returned_value()
            system.stats.category.categoryName[name].unset(apply=True).verify_result()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                system.stats.category.categoryName[name].show()).get_returned_value()
            ValidationTool.compare_dictionary_content(stats_category_show, category_list_default[name]). \
                verify_result()

        with allure.step("Update cache duration to 1 minute"):
            RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 1)

        with allure.step("Update category configuration"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=int(StatsConsts.HISTORY_DURATION_MIN)).\
                verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=int(StatsConsts.INTERVAL_MIN), apply=True).\
                verify_result()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                system.stats.category.categoryName[name].show()).get_returned_value()
            ValidationTool.compare_dictionary_content(stats_category_show, StatsConsts.CATEGORY_MIN_DICT).\
                verify_result()

        with allure.step("Restart process..."):
            engine.run_cmd("sudo systemctl restart stats-reportd")

        with allure.step("Check no files created when feature state is disabled"):
            output = engine.run_cmd("ls /var/stats")
            assert not output or "No such file or directory" in output, "Category internal files were not cleared"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()). \
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure.step("Enable feature and disable category"):
            system.stats.set(op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value). \
                verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.DISABLED.value, apply=True). \
                verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                system.stats.category.categoryName[name].show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"
            assert stats_category_show[StatsConsts.STATE] == StatsConsts.State.DISABLED.value, \
                "stats state parameter is expected to be 'disabled'"

        with allure.step("Wait 15 seconds..."):
            time.sleep(StatsConsts.SLEEP_15_SECONDS)

        with allure.step("Check no files created when category state is disabled"):
            output = engine.run_cmd("ls /var/stats")
            assert not output or "No such file or directory" in output, "Category internal files were not cleared"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()). \
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure.step("Enable category"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value, apply=True). \
                verify_result()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                system.stats.category.categoryName[name].show()).get_returned_value()
            assert stats_category_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"

        with allure.step("Wait another 1 minute..."):
            time.sleep(StatsConsts.SLEEP_1_MINUTE)

        with allure.step("Check both internal and external paths"):
            output = engine.run_cmd("ls /var/stats")
            assert output == name + '.csv', "Category internal file does not exist, or not the only one that exists"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()). \
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

    finally:
        set_system_stats_to_default(engine, system)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_system_stats_generation(engines, devices, test_api):
    """
    validate:
    - Enable/Disable stats feature
    - Show system stats commands
    - Update stats category configuration
    - System stats actions (generate and upload)
    - External file - name, header and content

    Test flow:
    1. Set stats feature to default
    2. Update general configuration
    3. Update all categories stats states
    4. Wait 3 minutes
    5. Generate system stats category
    6. Validate file content
    7. Upload stats file to URL
    8. Delete stats file
    9. Clear system stats specific category
    10.	Wait 3 minutes
    11.	Check internal and external files
    12.	Validate sample timestamps
    """

    TestToolkit.tested_api = test_api
    system = System(devices_dut=devices.dut)
    engine = engines.dut
    category_list = devices.dut.CATEGORY_LIST

    try:

        with allure.step("Clear all system stats and delete stats files"):
            clear_all_internal_and_external_files(system, category_list)

        with allure.step("Set Stats feature to default"):
            system.stats.unset(op_param=StatsConsts.STATE, apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"

        with allure.step("Update cache duration to 3 minutes"):
            RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 3)

        with allure.step("Update all categories interval values to minimum and states to enable"):
            for name in category_list:
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.INTERVAL, op_param_value=int(StatsConsts.INTERVAL_MIN)).verify_result()
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value).verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            apply_config, TestToolkit.engines.dut, False).verify_result()

        with allure.step("Restart process and check internal path"):
            engine.run_cmd("sudo systemctl restart stats-reportd")
            check_category_internal_files_exist(engine, category_list)

        with allure.step("Generate system stats category"):
            name = RandomizationTool.select_random_value(category_list).get_returned_value()
            system.stats.category.categoryName[name].action_general(StatsConsts.GENERATE).verify_result()
            after_generate_time = datetime.now()
            before_generate_time = after_generate_time - timedelta(minutes=5)
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            file_name = list(stats_files_show)[0]
            assert len(stats_files_show) == 1, "Expected only 1 file"
            assert name in file_name, "Expected category file does not exist"

        with allure.step("Upload stats file to URL"):
            player = validate_upload_stats_file(engines, system, file_name, False)

        with allure.step("Validate show file"):
            show_output = system.stats.files.show_file(file=file_name, exit_cmd='q')
            if 'NVUE' == TestToolkit.tested_api:
                assert name in show_output, "show file is missing category name"

        with allure.step("Validate external file header"):
            validate_external_file_header(name, file_name, before_generate_time, after_generate_time)

        with allure.step("Delete uploaded file"):
            player.run_cmd(cmd='rm -f {}{}'.format(NvosConst.MARS_RESULTS_FOLDER, file_name))

        with allure.step("Delete stats external file"):
            system.stats.files.action_file(StatsConsts.DELETE, file_name).verify_result()
            output = engine.run_cmd("ls /var/stats")
            assert name in output, "Category internal file not exists"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure.step("Clear system stats specific category"):
            clear_time = datetime.now()
            system.stats.category.categoryName[name].action_general(StatsConsts.CLEAR).verify_result()
            output = engine.run_cmd("ls /var/stats")
            assert not output or name not in output, "Category internal file was not cleared"

        with allure.step("Wait another 3 minutes..."):
            time.sleep(StatsConsts.SLEEP_3_MINUTES)

        with allure.step("Check both internal and external paths"):
            output = engine.run_cmd("ls /var/stats")
            assert name in output, "Category internal file does not exist, or not the only one that exists"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure.step("Generate and upload stats file to URL"):
            system.stats.category.categoryName[name].action_general(StatsConsts.GENERATE).verify_result()
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            file_name = list(stats_files_show)[0]
            player = validate_upload_stats_file(engines, system, file_name, False)

        with allure.step("Validate samples timestamps is older than clear time"):
            validate_external_file_timestamps(file_name, clear_time)

        with allure.step("Delete uploaded file"):
            player.run_cmd(cmd='rm -f {}{}'.format(NvosConst.MARS_RESULTS_FOLDER, file_name))

    finally:
        set_system_stats_to_default(engine, system)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_system_stats_performance(engines, devices, test_api):
    """
    validate:
    - Generate all system stats command
    - Time to generate "all" categories < 2 secs
    - Cleanup mechanism (after reboot)

    Test flow:
    1. Set stats feature to default
    2. Update general configuration
    3. Select a random category
    4. Update selected category stats config.
    5. Create category internal file with old samples
    6. Restart stats process
    7. Wait 1 minute
    8. Verify cleanup after reboot
    9.Update all categories stats states
    10.	Wait 1 minute
    11.	Generate all system files and verify action time
    12.	Upload stats file to URL
    13.	Validate file content
    """

    TestToolkit.tested_api = test_api
    system = System(devices_dut=devices.dut)
    engine = engines.dut
    category_list = devices.dut.CATEGORY_LIST
    category_disabled_dict = devices.dut.CATEGORY_DISABLED_DICT
    player_engine = engines['sonic_mgmt']

    try:
        with allure.step("Set Stats feature to default"):
            system.stats.unset(apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"

        with allure.step("Update cache duration to 1 minute"):
            RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 1)

        with allure.step("Select a random category"):
            name = RandomizationTool.select_random_value(list(category_disabled_dict.keys())). \
                get_returned_value()

        with allure.step("Update selected category stats config"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=int(StatsConsts.INTERVAL_MIN)).verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=int(StatsConsts.HISTORY_DURATION_MIN)).\
                verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value, apply=True).\
                verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            save_config, TestToolkit.engines.dut).verify_result()

        with allure.step("Create category internal file with old samples"):
            file_path = StatsConsts.OLD_SAMPLES_PATH + name + '.csv'
            player_engine.upload_file_using_scp(dest_username=DefaultConnectionValues.ADMIN,
                                                dest_password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                                dest_folder=StatsConsts.INTERNAL_PATH,
                                                dest_ip=engines.dut.ip,
                                                local_file_path=file_path)
            engine.run_cmd("sudo cp /tmp/{}.csv /var/stats".format(name))

        with allure.step("Perform system reboot"):
            system.reboot.action_reboot(params='force').verify_result()

        with allure.step("Check internal files were created"):
            check_category_internal_files_exist(engine, category_list)

        with allure.step("Clear all external files"):
            engine.run_cmd("sudo rm -f /host/stats/*.csv")

        with allure.step("Generate and upload stats file to URL"):
            system.stats.category.categoryName[name].action_general(StatsConsts.GENERATE).verify_result()
            current_time = datetime.now()
            history_time = current_time - timedelta(days=int(StatsConsts.HISTORY_DURATION_MIN))
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            file_name = list(stats_files_show)[0]
            player = validate_upload_stats_file(engines, system, file_name, False)

        with allure.step("Verify cleanup after restart process"):
            validate_external_file_timestamps(file_name, history_time)

        with allure.step("Delete uploaded file"):
            player.run_cmd(cmd='rm -f {}{}'.format(NvosConst.MARS_RESULTS_FOLDER, file_name))

        with allure.step("Clear all external files"):
            engine.run_cmd("sudo rm -f /host/stats/*.csv")

        with allure.step("Generate all system files and verify action time"):
            start_time = time.time()
            system.stats.category.categoryName[StatsConsts.ALL_CATEGORIES].action_general(StatsConsts.GENERATE).\
                verify_result()
            end_time = time.time()
            diff_time = end_time - start_time
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            file_name = list(stats_files_show)[0]
            assert len(stats_files_show) == 1, "Expected only 1 file"
            assert 'tar' in file_name, "tar file does not exist"
            assert diff_time < StatsConsts.GENERATE_ALL_TIME_MAX, "Generate all time is higher than allowed"

        with allure.step("Upload stats file to URL"):
            player = validate_upload_stats_file(engines, system, file_name, False)

        with allure.step("Extract the file and check that all categories file exist"):
            player.run_cmd("sudo tar -xf {}{}".format(NvosConst.MARS_RESULTS_FOLDER, file_name))
            file_split = file_name.split("_")
            report_path = os.path.splitext('report_{}_{}'.format(file_split[-2], file_split[-1]))[0]
            output = engine.run_cmd("ls {}{}".format(NvosConst.MARS_RESULTS_FOLDER, report_path))
            for name in category_list:
                assert name in output, f"{name} external file is missing in tar file"

        with allure.step("Delete uploaded file"):
            player.run_cmd(cmd='rm -f {}{}'.format(NvosConst.MARS_RESULTS_FOLDER, file_name))

    finally:
        set_system_stats_to_default(engine, system)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_stats_reliability(engines, devices, test_api):
    """
    validate:
    - Configuration of the feature persists through upgrade and reboot
    - Configuring/return to default the feature in the loop should be stable
    - No unexpected behavior (access violation, leak etc.) when processing malformed input
        (e.g. malformed/missing config in DB)

    Test flow:
    1. Set stats feature to default
    2. Update general configuration
    3. Update all categories stats states
    4. Wait 1 minute
    5. Check internal path
    6. Perform system reboot
    7. Check feature and categories config.
    8. Check internal path
    9. Configuring the feature to default in the loop
    10.	Remove sampled data from DB
    """

    TestToolkit.tested_api = test_api
    system = System(devices_dut=devices.dut)
    engine = engines.dut
    category_list = devices.dut.CATEGORY_LIST
    try:
        with allure.step("Set Stats feature to default"):
            system.stats.unset(apply=True).verify_result()

        with allure.step("Update cache duration to 1 minute"):
            RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 1)

        with allure.step("Update all categories stats states"):
            for name in category_list:
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value).verify_result()
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.INTERVAL, op_param_value=int(StatsConsts.INTERVAL_MIN)).verify_result()
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=int(StatsConsts.HISTORY_DURATION_MIN)).\
                    verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            apply_config, TestToolkit.engines.dut, False).verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            save_config, TestToolkit.engines.dut).verify_result()

        with allure.step("restart stats service and check internal path"):
            engine.run_cmd("sudo systemctl restart stats-reportd")
            check_category_internal_files_exist(engine, category_list)

        with allure.step("Perform system reboot"):
            system.reboot.action_reboot(params='force').verify_result()

        with allure.step("Check feature and categories configurations"):
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"
            for name in category_list:
                stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                    system.stats.category.categoryName[name].show()).get_returned_value()
                ValidationTool.compare_dictionary_content(stats_category_show, StatsConsts.CATEGORY_MIN_DICT).\
                    verify_result()

        with allure.step("Check internal path"):
            check_category_internal_files_exist(engine, category_list)

        with allure.step("Configuring the feature to default in the loop"):
            for x in range(10):
                system.stats.unset(op_param=StatsConsts.STATE, apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"

        with allure.step("Remove sampled data from DB"):
            # TODO: delete a sampled parameter from DB
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"
            system.log.rotate_logs()
            show_output = system.log.show_log(exit_cmd='q')
            # TODO: update StatsConsts.LOG_MSG_ERROR_DB
            # ValidationTool.verify_expected_output(show_output, StatsConsts.LOG_MSG_ERROR_DB).verify_result()

    finally:
        set_system_stats_to_default(engine, system)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_system_stats_log(engines, devices, test_api):
    """
    validate:
    - Configuring commands are logged to system log

    Test flow:
    1. Unset stats feature state and check log file
    2. Set category stats configuration and check log file
    """

    TestToolkit.tested_api = test_api
    system = System(devices_dut=devices.dut)
    engine = engines.dut
    category_list = devices.dut.CATEGORY_LIST

    try:
        with allure.step("Unset stats feature state and check log file"):
            system.log.rotate_logs()
            system.stats.unset(op_param=StatsConsts.STATE, apply=True).verify_result()
            show_output = system.log.show_log(exit_cmd='q')
            ValidationTool.verify_expected_output(show_output, StatsConsts.LOG_MSG_UNSET_STATS).verify_result()

        with allure.step("Set category stats configuration and check log file"):
            name = RandomizationTool.select_random_value(category_list).get_returned_value()
            log_msg = StatsConsts.LOG_MSG_PATCH_CATEGORY + name
            system.log.rotate_logs()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=int(StatsConsts.INTERVAL_MIN)).verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=int(StatsConsts.HISTORY_DURATION_DEFAULT)).\
                verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value).verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            apply_config, TestToolkit.engines.dut, False).verify_result()
            show_output = system.log.show_log(exit_cmd='q')
            ValidationTool.verify_expected_output(show_output, log_msg).verify_result()

    finally:
        set_system_stats_to_default(engine, system)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
@pytest.mark.parametrize('test_api', [ApiType.NVUE])
def test_system_stats_invalid_values(engines, devices, test_api):
    """
    validate:
    - Check all the commands that get param with invalid values

    Test flow:
    1. nv set system stats category <invalid category-name> state <state>
    2. nv set system stats category <category-name> state <invalid state>
    3. nv set system stats category <category-name> interval <less than 1>
    4. nv set system stats category <category-name> interval <higher than 1440>
    5. nv set system stats category <category-name> history-duration <less than 1>
    6. nv set system stats category <category-name> history-duration <higher than 365>
    7. nv show system stats category <invalid category-name>
    8. nv clear system stats <invalid category-name>
    9. nv action delete system stats files <file does not exist>
    10. nv action upload system stats files <file does not exist> <remote-url>
    11. nv action upload system stats files <file-name> <invalid remote-url>
    12. nv action generate system stats <invalid category-name>
    """

    TestToolkit.tested_api = test_api
    system = System(devices_dut=devices.dut)
    engine = engines.dut
    category_list = devices.dut.CATEGORY_LIST

    try:
        with allure.step("Validate set system stats unknown category"):
            system.stats.category.categoryName[StatsConsts.INVALID_CATEGORY_NAME].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.DISABLED.value, apply=True).\
                verify_result(should_succeed=False)

        with allure.step("Validate set system stats category invalid state"):
            name = RandomizationTool.select_random_value(category_list).get_returned_value()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.INVALID_STATE).\
                verify_result(should_succeed=False)

        with allure.step("Validate set system stats category invalid low interval"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=StatsConsts.INVALID_INTERVAL_LOW).\
                verify_result(should_succeed=False)

        with allure.step("Validate set system stats category invalid high interval"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=StatsConsts.INVALID_INTERVAL_HIGH).\
                verify_result(should_succeed=False)

        with allure.step("Validate set system stats category invalid low history-duration"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=StatsConsts.INVALID_HISTORY_DURATION_LOW).\
                verify_result(should_succeed=False)

        with allure.step("Validate set system stats category invalid high history-duration"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=StatsConsts.INVALID_HISTORY_DURATION_HIGH).\
                verify_result(should_succeed=False)

        with allure.step("Validate show system stats invalid category"):
            stats_show = system.stats.category.categoryName[StatsConsts.INVALID_CATEGORY_NAME].show()
            assert StatsConsts.INVALID_SHOW_CATEGORY in stats_show, "Expected error msg: requested item does not exist"

        with allure.step("Validate clear system stats invalid category"):
            system.stats.category.categoryName[StatsConsts.INVALID_CATEGORY_NAME].action_general(StatsConsts.CLEAR).\
                verify_result(should_succeed=False)

        with allure.step("Validate delete system stats file not exists"):
            system.stats.files.action_file(StatsConsts.DELETE, StatsConsts.INVALID_FILE_NAME).\
                verify_result(should_succeed=False)

        with allure.step("Validate upload system stats file not exists"):
            system.stats.files.action_file(StatsConsts.UPLOAD, StatsConsts.INVALID_FILE_NAME,
                                           StatsConsts.VALID_REMOTE_URL).verify_result(should_succeed=False)

        # with allure.step("Validate upload system stats file to invalid URL"):
        #     # TODO: update <file_name>
        #     system.stats.files.action_file(StatsConsts.UPLOAD,'<file_name>',
        #                                    StatsConsts.INVALID_REMOTE_URL).verify_result(should_succeed=False)

        with allure.step("Validate generate system stats invalid category"):
            system.stats.category.categoryName[StatsConsts.INVALID_CATEGORY_NAME].action_general(StatsConsts.GENERATE).\
                verify_result(should_succeed=False)

    finally:
        SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                        detach_config, TestToolkit.engines.dut).verify_result()
        set_system_stats_to_default(engine, system)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
@pytest.mark.parametrize('test_api', ApiType.ALL_TYPES)
def test_system_stats_on_skynet(test_api):
    """
    (Dedicated test will be added later to skynet to check some of the functionalities once a month)

    Test flow:
    1. ...
    """

    TestToolkit.tested_api = test_api


# ---------------------------------------------
def set_system_stats_to_default(engine, system):
    with allure.step("Update Stats feature to default"):
        system.stats.unset(apply=True).verify_result()

    with allure.step("Update cache general configuration to default"):
        RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 10)
        RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cleanup_interval", 1)


def clear_all_internal_and_external_files(system, category_list):
    for name in category_list:
        system.stats.category.categoryName[name].action_general(StatsConsts.CLEAR).verify_result()
    stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()). \
        get_returned_value()
    if stats_files_show != {}:
        for file in stats_files_show.keys():
            system.stats.files.action_file(StatsConsts.DELETE, file).verify_result()


def check_category_internal_files_exist(engine, category_list):
    output = engine.run_cmd("ls /var/stats")
    output_list = list(filter(None, output.split(' ')))
    assert len(output_list) == len(category_list), "Categories number of files is not as expected"
    for cat in category_list:
        assert cat in output, f"{cat} internal file is missing"


def validate_upload_stats_file(engines, system, file, delete=True):
    """
    validate upload stats file with scp and sftp
    """
    upload_protocols = ['scp', 'sftp']
    player = engines['sonic_mgmt']
    dest_path = NvosConst.MARS_RESULTS_FOLDER

    with allure.step("Upload stats file to player {} with the next protocols : {}".format(player.ip, upload_protocols)):
        for protocol in upload_protocols:
            with allure.step("Upload stats file to player with {} protocol".format(protocol)):
                upload_path = 'scp://{}:{}@{}{}'.format(player.username, player.password, player.ip, dest_path)
                system.stats.files.action_file(StatsConsts.UPLOAD, file, upload_path).verify_result()

            with allure.step("Validate file was uploaded to player"):
                assert player.run_cmd(cmd='ls {} | grep {}'.format(dest_path, file)),\
                    "Did not find the file with ls cmd"

            if delete:
                with allure.step("Delete uploaded file"):
                    player.run_cmd(cmd='rm -f {}{}'.format(dest_path, file))

        return player


def validate_external_file_header(name, file_name, start_time, end_time):
    full_path = NvosConst.MARS_RESULTS_FOLDER + file_name
    with open(full_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        next(reader)
        row = next(reader)
        assert row[0].startswith(StatsConsts.HEADER_HOSTNAME), "unexpected hostname in file header"
        row = next(reader)
        assert row[0] == StatsConsts.HEADER_GROUP + name, "unexpected group in file header"
        row = next(reader)
        assert row[0].startswith(StatsConsts.HEADER_TIME), "unexpected time in file header"

        if start_time and end_time:
            export_time = datetime.strptime(row[0].strip(StatsConsts.HEADER_TIME).split(",")[0],
                                            StatsConsts.TIMESTAMP_FORMAT)
            assert start_time < export_time < end_time,\
                "External file export time is not as expected"

        idx = 4
        start_data_idx = -1
        for row in reader:
            if row:
                if row[0].startswith("Timestamp"):
                    start_data_idx = idx + 1
                    break
            idx += 1
            if idx == StatsConsts.MAX_ROWS_TO_SCAN:
                break

        assert start_data_idx >= 0, "did not find data start line"
        assert len(row) == (start_data_idx - StatsConsts.CONST_HEADER_ROWS),\
            "mismatch between columns defined number"

        num_of_samples = 0
        for row in reader:
            num_of_samples += 1
        assert num_of_samples >= 1, "Number of samples in file are not as expected"


def validate_external_file_timestamps(file_name, clear_time):
    full_path = NvosConst.MARS_RESULTS_FOLDER + file_name
    with open(full_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        idx = 0
        start_data_idx = -1
        for row in reader:
            if row:
                if row[0].startswith("Timestamp"):
                    start_data_idx = idx + 1
                    break
            idx += 1
            if idx == StatsConsts.MAX_ROWS_TO_SCAN:
                break

        assert start_data_idx >= 0, "did not find data start line"

        for row in reader:
            sample_time = datetime.strptime(row[0].strip(StatsConsts.HEADER_TIME).split(",")[0],
                                            StatsConsts.TIMESTAMP_FORMAT)
            assert sample_time > clear_time, "Samples time is earlier than clear time"
