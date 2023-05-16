import pytest
import time

from ngts.nvos_constants.constants_nvos import ApiType, StatsConsts
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.OutputParsingTool import OutputParsingTool
from ngts.nvos_tools.infra.RandomizationTool import RandomizationTool
from ngts.nvos_tools.infra.RedisTool import RedisTool
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils.allure_utils import allure_step


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_configuration(engines, devices):
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
    system = System()
    engine = engines.dut
    system.stats.category.categoryName['cpu'].action_clear().verify_result()
    category_list = devices.dut.CATEGORY_LIST
    category_disabled_dict = devices.dut.CATEGORY_DISABLED_DICT

    try:
        with allure_step("Disable system stats feature"):
            system.stats.set(op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.DISABLED.value,
                             apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.DISABLED.value, \
                "stats state parameter is expected to be 'disabled'"

        with allure_step("Disable all categories stats"):
            for name in category_list:
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.DISABLED.value).verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            apply_config, TestToolkit.engines.dut, False).verify_result()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.category.show()).\
                get_returned_value()
            ValidationTool.compare_dictionary_content(stats_category_show, category_disabled_dict).verify_result()

        with allure_step("Clear all system stats and delete stats files"):
            for name in category_list:
                system.stats.category.categoryName[name].action_clear().verify_result()
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            if stats_files_show != {}:
                for file in stats_files_show.keys():
                    system.stats.files.action_delete(file).verify_result()

        with allure_step("Check both internal and external paths"):
            output = engine.run_cmd("ls /var/stats")
            assert not output or "No such file or directory" in output, "Category internal files were not cleared"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure_step("Select a random category and unset its configuration"):
            name = RandomizationTool.select_random_value(list(category_disabled_dict.keys())).\
                get_returned_value()
            system.stats.category.categoryName[name].unset(op_param=StatsConsts.INTERVAL).verify_result()
            system.stats.category.categoryName[name].unset(op_param=StatsConsts.HISTORY_DURATION).verify_result()
            system.stats.category.categoryName[name].unset(op_param=StatsConsts.STATE, apply=True).verify_result()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                system.stats.category.categoryName[name].show()).get_returned_value()
            ValidationTool.compare_dictionary_content(stats_category_show, StatsConsts.CATEGORY_DEFAULT_DICT).\
                verify_result()

        with allure_step("Update cache duration to 1 minute"):
            RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 1)

        with allure_step("Update category configuration"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=StatsConsts.HISTORY_DURATION_MIN).\
                verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=StatsConsts.INTERVAL_MIN, apply=True).verify_result()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                system.stats.category.categoryName[name].show()).get_returned_value()
            ValidationTool.compare_dictionary_content(stats_category_show, StatsConsts.CATEGORY_MIN_DICT).\
                verify_result()

        with allure_step("Wait 1 minute..."):
            time.sleep(StatsConsts.SLEEP_1_MINUTE)

        with allure_step("Check no files created when feature state is disabled"):
            output = engine.run_cmd("ls /var/stats")
            assert not output or "No such file or directory" in output, "Category internal files were not cleared"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure_step("Enable feature and disable category"):
            system.stats.set(op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value).\
                verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.DISABLED.value, apply=True).\
                verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                system.stats.category.categoryName[name].show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"
            assert stats_category_show[StatsConsts.STATE] == StatsConsts.State.DISABLED.value, \
                "stats state parameter is expected to be 'disabled'"

        with allure_step("Wait 1 minute..."):
            time.sleep(StatsConsts.SLEEP_1_MINUTE)

        with allure_step("Check no files created when category state is disabled"):
            output = engine.run_cmd("ls /var/stats")
            assert not output or "No such file or directory" in output, "Category internal files were not cleared"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure_step("Update cache duration to 3 minutes"):
            RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 3)

        with allure_step("Enable category"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value, apply=True).\
                verify_result()
            stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                system.stats.category.categoryName[name].show()).get_returned_value()
            assert stats_category_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"

        with allure_step("Wait 2 minutes..."):
            time.sleep(StatsConsts.SLEEP_2_MINUTES)

        with allure_step("Check both internal and external paths"):
            # TODO: check if file "stats_<selected_category>_<switch_name>_date_time" exist in the internal path:
            #  "/var/stats", assert if not (should be exists only with header but without any samples).
            output = engine.run_cmd("ls /var/stats")
            assert not output or name in output, "Category internal file not exists"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure_step("Wait another 1 minute..."):
            time.sleep(StatsConsts.SLEEP_1_MINUTE)

        with allure_step("Check both internal and external paths"):
            # TODO: check if file "stats_<selected_category>_<switch_name>_date_time" exist in the internal path:
            #  "/var/stats", assert if not (should be exists with header and samples).
            output = engine.run_cmd("ls /var/stats")
            assert not output or name in output, "Category internal file not exists"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

    finally:
        set_system_stats_to_default(system, category_list)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_generation(engines, devices):
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
    system = System()
    engine = engines.dut
    category_list = devices.dut.CATEGORY_LIST
    category_disabled_dict = devices.dut.CATEGORY_DISABLED_DICT

    try:
        with allure_step("Set Stats feature to default"):
            system.stats.unset(op_param=StatsConsts.STATE, apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"

        with allure_step("Update cache duration to 3 minutes"):
            RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 3)

        with allure_step("Update all categories stats states"):
            for name in category_list:
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value).verify_result()
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.INTERVAL, op_param_value=StatsConsts.INTERVAL_MIN).verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            apply_config, TestToolkit.engines.dut, False).verify_result()

        with allure_step("Wait 3 minutes and check internal path"):
            time.sleep(StatsConsts.SLEEP_3_MINUTES)
            output = engine.run_cmd("ls /var/stats")
            # TODO: update comparison (all 6 categories internal files should be exist).
            ValidationTool.compare_dictionary_content(output, category_list).verify_result()

        with allure_step("Generate system stats category"):
            name = RandomizationTool.select_random_value(list(category_disabled_dict.keys())). \
                get_returned_value()
            system.stats.files.action_generate(name + '.csv').verify_result()
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show != {}, "External stats file should be exists"

        with allure_step("Validate file content"):
            stats_file_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show('<file_name>')).\
                get_returned_value()
            # TODO: Validate file content as expected:
            #  Host name: switch name
            #  Stats group: selected category
            #  Export time: current time
            #  Num of samples: 4
            #  Num of col. As expected (per sensor and per device)
            #  Timestamp diff = 1 min

        with allure_step("Upload stats file to URL"):
            system.stats.files.action_upload('<file_name>', '<remote_url>').verify_result()
            # TODO: check if file exists in <remote_url>, assert if not
            #  output = engine.run_cmd("ls <remote_url>/<file>")
            #  assert not output or name in output, "Category internal file not exists"

        with allure_step("Delete stats external file"):
            system.stats.files.action_delete('<file_name>').verify_result()
            # TODO: check if file "stats_<selected_category>_<switch_name>_date_time" exist in the internal path:
            #  "/var/stats", assert if not (should be exists).
            #  output = engine.run_cmd("ls /var/stats/stats_<selected_category>_<switch_name>_date_time")
            #  assert not output or name in output, "Category internal file not exists"

            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure_step("Clear system stats specific category"):
            clear_time = time.time()
            system.stats.category.categoryName['<category_name>'].action_clear().verify_result()
            # TODO: check if file "stats_<selected_category>_<switch_name>_date_time" exist in the internal path:
            #  "/var/stats", assert if so (should not be exists).
            #  output = engine.run_cmd("ls /var/stats/stats_<selected_category>_<switch_name>_date_time")
            #  assert not output or name in output, "Category internal file not exists"

        with allure_step("Wait another 3 minutes..."):
            time.sleep(StatsConsts.SLEEP_3_MINUTES)

        with allure_step("Check both internal and external paths"):
            # TODO: check if file "stats_<selected_category>_<switch_name>_date_time" exist in the internal path:
            #  "/var/stats", assert if not (should be exists).
            #  output = engine.run_cmd("ls /var/stats/stats_<selected_category>_<switch_name>_date_time")
            #  assert not output or name in output, "Category internal file not exists"
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            assert stats_files_show == {}, "External stats files should not exist"

        with allure_step("Validate sample timestamps"):
            stats_file_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show('<file_name>')).\
                get_returned_value()
            # TODO: verify samples timestamps should be higher than clear command timestamp (clear_time),
            #  assert otherwise.

    finally:
        set_system_stats_to_default(system, category_list)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_performance(engines, devices):
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
    5. Clear selected category stats
    6. Create category internal file with old samples
    7. Restart stats process
    8. Wait 1 minute
    9. Verify cleanup after reboot
    10.	Update all categories stats states
    11.	Wait 1 minute
    12.	Generate all system files and verify action time
    13.	Upload stats file to URL
    14.	Validate file content
    """
    system = System()
    engine = engines.dut
    category_list = devices.dut.CATEGORY_LIST
    category_disabled_dict = devices.dut.CATEGORY_DISABLED_DICT

    try:
        with allure_step("Set Stats feature to default"):
            system.stats.unset(op_param=StatsConsts.STATE, apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"

        with allure_step("Update cache duration to 1 minute"):
            RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 1)

        with allure_step("Select a random category"):
            name = RandomizationTool.select_random_value(list(category_disabled_dict.keys())). \
                get_returned_value()

        with allure_step("Update selected category stats config"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=StatsConsts.INTERVAL_MIN).verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=StatsConsts.HISTORY_DURATION_DEFAULT).\
                verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value, apply=True).\
                verify_result()

        with allure_step("Clear selected category stats"):
            system.stats.category.categoryName[name].action_clear().verify_result()

#        with allure_step("Create category internal file with old samples"):
            # TODO: copy csv file for <selected> category with old samples (timestamp more than a year ago)
            #  to “/var/stats” path

#        with allure_step("Restart stats process"):
            # TODO: Restart stats process command

        with allure_step("Wait 1 minute..."):
            time.sleep(StatsConsts.SLEEP_1_MINUTE)

#        with allure_step("Verify cleanup after restart process"):
            # TODO: verify <selected> internal file and expect old samples have been removed from file.

        with allure_step("Wait 1 minute and check internal file"):
            time.sleep(StatsConsts.SLEEP_1_MINUTE)
            output = engine.run_cmd("ls /var/stats")
            # TODO: update comparison (all 6 categories internal files should be exist).
            ValidationTool.compare_dictionary_content(output, category_list).verify_result()

        with allure_step("Generate all system files and verify action time"):
            start_time = time.time()
            system.stats.files.action_generate('all').verify_result()
            end_time = time.time()
            diff_time = end_time - start_time
            stats_files_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.files.show()).\
                get_returned_value()
            # TODO: verify stats_files_show contain only single TAR file
            assert diff_time < StatsConsts.GENERATE_ALL_TIME_MAX, "Generate all time is higher than allowed"

        with allure_step("Upload stats file to URL"):
            system.stats.files.action_upload('<file_name>', '<remote_url>').verify_result()
            # TODO: check if file exists in <remote_url>, assert if not
            #  output = engine.run_cmd("ls <remote_url>/<file>")
            #  assert not output or name in output, "Category internal file not exists"

#        with allure_step("Validate file content"):
            # TODO: Extract the file and check that all 6 categories file exist

    finally:
        set_system_stats_to_default(system, category_list)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_stats_reliability(engines, devices):
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
    system = System()
    engine = engines.dut
    category_list = devices.dut.CATEGORY_LIST
    try:
        with allure_step("Set Stats feature to default"):
            system.stats.unset(op_param=StatsConsts.STATE, apply=True).verify_result()

        with allure_step("Update cache duration to 1 minute"):
            RedisTool.redis_cli_hset(engine, 4, "STATS_CONFIG|GENERAL", "cache_duration", 1)

        with allure_step("Update all categories stats states"):
            for name in category_list:
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value).verify_result()
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.INTERVAL, op_param_value=StatsConsts.INTERVAL_MIN).verify_result()
                system.stats.category.categoryName[name].set(
                    op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=StatsConsts.HISTORY_DURATION_MIN).\
                    verify_result()
            SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                            apply_config, TestToolkit.engines.dut, False).verify_result()
            # TODO: run command: nv config save

        with allure_step("Wait 1 minute and check internal path"):
            time.sleep(StatsConsts.SLEEP_1_MINUTE)
            output = engine.run_cmd("ls /var/stats")
            # TODO: update comparison (all 6 categories internal files should be exist).
            ValidationTool.compare_dictionary_content(output, category_list).verify_result()

        with allure_step("Perform system reboot"):
            system.reboot.action_reboot(params='force').verify_result()

        with allure_step("Check feature and categories configurations"):
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"
            for name in category_list:
                stats_category_show = OutputParsingTool.parse_json_str_to_dictionary(
                    system.stats.category.categoryName[name].show()).get_returned_value()
                ValidationTool.compare_dictionary_content(stats_category_show, StatsConsts.CATEGORY_MIN_DICT).\
                    verify_result()

        with allure_step("Check internal path"):
            output = engine.run_cmd("ls /var/stats")
            # TODO: update comparison (all 6 categories internal files should be exist).
            ValidationTool.compare_dictionary_content(output, category_list).verify_result()

        with allure_step("Configuring the feature to default in the loop"):
            for x in range(10):
                system.stats.unset(op_param=StatsConsts.STATE, apply=True).verify_result()
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"

        with allure_step("Remove sampled data from DB"):
            # TODO: delete a sampled parameter from DB
            stats_show = OutputParsingTool.parse_json_str_to_dictionary(system.stats.show()).get_returned_value()
            assert stats_show[StatsConsts.STATE] == StatsConsts.State.ENABLED.value, \
                "stats state parameter is expected to be 'enabled'"
            system.log.rotate_logs()
            show_output = system.log.show_log(exit_cmd='q')
            ValidationTool.verify_expected_output(show_output, StatsConsts.LOG_MSG_ERROR_DB).verify_result()

    finally:
        set_system_stats_to_default(system, category_list)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_log(devices):
    """
    validate:
    - Configuring commands are logged to system log

    Test flow:
    1. Unset stats feature state and check log file
    2. Set category stats configuration and check log file
    """
    system = System()
    category_list = devices.dut.CATEGORY_LIST

    try:
        with allure_step("Unset stats feature state and check log file"):
            system.log.rotate_logs()
            system.stats.unset(op_param=StatsConsts.STATE, apply=True).verify_result()
            show_output = system.log.show_log(exit_cmd='q')
            ValidationTool.verify_expected_output(show_output, StatsConsts.LOG_MSG_UNSET_STATS).verify_result()

        with allure_step("Set category stats configuration and check log file"):
            name = RandomizationTool.select_random_value(category_list).get_returned_value()
            system.log.rotate_logs()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=StatsConsts.INTERVAL_MIN).verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=StatsConsts.HISTORY_DURATION_DEFAULT).\
                verify_result()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.ENABLED.value, apply=True).\
                verify_result()
            show_output = system.log.show_log(exit_cmd='q')
            ValidationTool.verify_expected_output(show_output, StatsConsts.LOG_MSG_SET_CATEGORY_STATS).verify_result()

    finally:
        set_system_stats_to_default(system, category_list)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_invalid_values(devices):
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
    system = System()
    category_list = devices.dut.CATEGORY_LIST

    try:
        with allure_step("Validate set system stats unknown category"):
            system.stats.category.categoryName[StatsConsts.INVALID_CATEGORY_NAME].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.State.DISABLED.value).\
                verify_result(should_succeed=False)

        with allure_step("Validate set system stats category invalid state"):
            name = RandomizationTool.select_random_value(category_list).get_returned_value()
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.STATE, op_param_value=StatsConsts.INVALID_STATE).\
                verify_result(should_succeed=False)

        with allure_step("Validate set system stats category invalid low interval"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=StatsConsts.INVALID_INTERVAL_LOW).\
                verify_result(should_succeed=False)

        with allure_step("Validate set system stats category invalid high interval"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.INTERVAL, op_param_value=StatsConsts.INVALID_INTERVAL_HIGH).\
                verify_result(should_succeed=False)

        with allure_step("Validate set system stats category invalid low history-duration"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=StatsConsts.INVALID_HISTORY_DURATION_LOW).\
                verify_result(should_succeed=False)

        with allure_step("Validate set system stats category invalid high history-duration"):
            system.stats.category.categoryName[name].set(
                op_param_name=StatsConsts.HISTORY_DURATION, op_param_value=StatsConsts.INVALID_HISTORY_DURATION_HIGH).\
                verify_result(should_succeed=False)

        with allure_step("Validate show system stats invalid category"):
            system.stats.category.categoryName[StatsConsts.INVALID_CATEGORY_NAME].show().\
                verify_result(should_succeed=False)

        with allure_step("Validate clear system stats invalid category"):
            system.stats.category.categoryName[StatsConsts.INVALID_CATEGORY_NAME].action_clear().\
                verify_result(should_succeed=False)

        with allure_step("Validate delete system stats file not exists"):
            system.stats.files.action_delete(StatsConsts.INVALID_FILE_NAME).verify_result(should_succeed=False)

        with allure_step("Validate upload system stats file not exists"):
            # TODO: update <remote-url>
            system.stats.files.action_upload(StatsConsts.INVALID_FILE_NAME, '<remote_url>').\
                verify_result(should_succeed=False)

        with allure_step("Validate upload system stats file to invalid URL"):
            # TODO: update <file_name>
            system.stats.files.action_upload('<file_name>', StatsConsts.INVALID_REMOTE_URL).\
                verify_result(should_succeed=False)

        with allure_step("Validate generate system stats invalid category"):
            system.stats.files.action_generate(StatsConsts.INVALID_CATEGORY_NAME).verify_result(should_succeed=False)

    finally:
        set_system_stats_to_default(system, category_list)


@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_on_skynet():
    """
    (Dedicated test will be added later to skynet to check some of the functionalities once a month)

    Test flow:
    1. ...
    """


# ------------ Open API tests -----------------
@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_configuration_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_system_stats_configuration(engines)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_generation_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_system_stats_generation(engines, devices)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_performance_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_system_stats_performance(engines, devices)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_stats_reliability_openapi(engines, devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_stats_reliability(engines, devices)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_log_openapi(devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_system_stats_log(devices)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_invalid_values_openapi(devices):
    TestToolkit.tested_api = ApiType.OPENAPI
    test_system_stats_invalid_values(devices)


@pytest.mark.openapi
@pytest.mark.system
@pytest.mark.stats
@pytest.mark.simx
def test_system_stats_on_skynet_openapi():
    TestToolkit.tested_api = ApiType.OPENAPI
    test_system_stats_on_skynet()


# ---------------------------------------------
def set_system_stats_to_default(system, category_list):
    with allure_step("Set Stats feature to default"):
        system.stats.unset(op_param=StatsConsts.STATE).verify_result()
        for name in category_list:
            system.stats.category.categoryName[name].unset(op_param=StatsConsts.INTERVAL).verify_result()
            system.stats.category.categoryName[name].unset(op_param=StatsConsts.HISTORY_DURATION).verify_result()
            system.stats.category.categoryName[name].unset(op_param=StatsConsts.STATE, apply=True).verify_result()
        SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].
                                        apply_config, TestToolkit.engines.dut, False).verify_result()
