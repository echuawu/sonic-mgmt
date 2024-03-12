import os
import pytest
import allure
import logging
from tests.common.utilities import wait_until
from test_techsupport import extract_file_from_tar_file
from tests.common import config_reload

logger = logging.getLogger(__name__)


SDK_DUMP_DIR = '/var/log/bluefield/sdk-dumps/'
SDK_DUMP_FILES = ["acls.log", "enis.log", "general.log", "routing.log", "sai_nasa_dump.txt", "stats.log"]
SAI_SDK_DUMP_FOLDER_NAME = 'sai_sdk_dump'

pytestmark = [
    pytest.mark.topology('any')
]


@pytest.fixture(scope='module', autouse=True)
def skip_test_on_non_dpu_platform(duthosts, enum_rand_one_per_hwsku_frontend_hostname):
    duthost = duthosts[enum_rand_one_per_hwsku_frontend_hostname]
    config_facts = duthost.config_facts(host=duthost.hostname, source="running")['ansible_facts']
    if config_facts['DEVICE_METADATA']['localhost'].get('switch_type', '') != 'dpu':
        pytest.skip("Skip the test, as it is supported only on DPU.")


@pytest.fixture(scope='function', autouse=False)
def recover_dut(duthosts, enum_rand_one_per_hwsku_frontend_hostname):
    duthost = duthosts[enum_rand_one_per_hwsku_frontend_hostname]

    yield

    logger.info("Recover dut by config reload -y")
    config_reload(duthost)


@pytest.mark.disable_loganalyzer
def test_fw_stuck_dump(duthosts, enum_rand_one_per_hwsku_frontend_hostname, recover_dut):
    """
    This test is to check triggering fw stuck will generate dump file
    1. Get DUT current time (time_before_trigger_fw_stuck) before triggering fw stuck
    2. Trigger fw stuck by running command: echo 1 > /sys/bus/pci/devices/0000\: 03\:00.0/remove ;
       cho 1 > /sys/bus/pci/devices/0000\:03\:00.1/remove ; sleep 5 ; echo 1 > /sys/bus/pci/rescan
    3. Check one new SAI/SDK dump file is generated in /var/log/bluefield/sdk-dumps/,
       and the created time for the new dump file should be later than time_before_trigger_fw_stuck
    4. Check sai-dfw-xxxxx.tar.gz include acls.log, enis.log, general.log, routing.log, sai_nasa_dump.txt, stats.log
    5. Recover DUT by config reload -y
    :param duthosts: DUT host
    """
    duthost = duthosts[enum_rand_one_per_hwsku_frontend_hostname]

    with allure.step("Get initial time before trigger fw stuck"):
        time_before_trigger_fw_stuck = duthost.shell("date")['stdout']

    with allure.step("Trigger fw stuck "):
        trigger_fw_stuck_cmd = "echo 1 > /sys/bus/pci/devices/0000\:03\:00.0/remove ; " \
                               "echo 1 > /sys/bus/pci/devices/0000\:03\:00.1/remove ;" \
                               " sleep 5 ; echo 1 > /sys/bus/pci/rescan"
        duthost.shell(trigger_fw_stuck_cmd)

    with allure.step("Check new dump file is generated"):
        sdk_dump_list_after_trigger_fw_stuck = []

        def _check_new_dump_file_is_generated():
            nonlocal sdk_dump_list_after_trigger_fw_stuck
            get_new_dump_file_cmd = f" find {SDK_DUMP_DIR}sai-dfw*.tar -newermt  '{time_before_trigger_fw_stuck}'"
            sdk_dump_list_after_trigger_fw_stuck = duthost.shell(get_new_dump_file_cmd)['stdout_lines']
            # show dump file info for debug
            show_dump_file_info = f"ls -lh {SDK_DUMP_DIR}"
            duthost.shell(show_dump_file_info)
            return sdk_dump_list_after_trigger_fw_stuck

        assert wait_until(120, 5, 0, _check_new_dump_file_is_generated),\
            "FW stuck doesn't trigger dump files generated in 120s"
        techsupport_dump_list_num = len(sdk_dump_list_after_trigger_fw_stuck)
        assert techsupport_dump_list_num == 1,\
            f"Expect one dump file, actual {techsupport_dump_list_num} techsupport dump file are generated "

    with allure.step(f"Check  sai-dfw includes {SDK_DUMP_FILES}"):
        _, extracted_sai_dfw_folder_path = extract_file_from_tar_file(
            duthost, sdk_dump_list_after_trigger_fw_stuck[0], True)
        get_sai_dump_file_cmd = f"find {extracted_sai_dfw_folder_path} -regex '.*\(.txt\|.log\)'"
        sai_dump_file_list = duthost.shell(get_sai_dump_file_cmd)['stdout_lines']
        for file in SDK_DUMP_FILES:
            full_name = os.path.join(extracted_sai_dfw_folder_path, file)
            assert full_name in sai_dump_file_list,\
                f"{full_name} is not generated. Actual file list is {sai_dump_file_list}"
