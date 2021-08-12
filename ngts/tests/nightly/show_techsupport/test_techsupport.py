import allure
import os
import pytest
import time
from retry.api import retry_call
import re
import logging
import tarfile

logger = logging.getLogger(__name__)

SUCCESS_CODE = 0

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
FILES_DIR = os.path.join(BASE_DIR, 'files')
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
SDK_DUMP_DIR = '/var/log/mellanox/sdk-dumps'


@pytest.fixture(autouse=False)
def ignore_temp_loganalyzer_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests
    because of some expected bugs which causes exceptions in log
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "temp_log_analyzer_ignores.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)


@allure.title('Tests that DumpMeNow dump contains all the expected dumps when fw stuck occurs')
def test_techsupport_fw_stuck_dump(topology_obj, loganalyzer, engines, cli_objects, ignore_temp_loganalyzer_exceptions):
    duthost = engines.dut
    chip_type = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['chip_type']

    pre_stuck_dumps = duthost.run_cmd('ls -t {}/*.tar | wc -l'.format(SDK_DUMP_DIR))
    with allure.step('Stop all iRISICs to halt FW'):
        stop_irisics(chip_type, duthost)

    with allure.step('Wait for DumpMe dump to be created'):
        retry_call(
            verify_sdkdump_created,
            fargs=[duthost, pre_stuck_dumps],
            tries=30,
            delay=10,
            logger=logger,
        )

    with allure.step('Validate that the DumpMe dump contain all of the SDK extended dump files'):
        check_all_dumps_file_exsits(duthost)

    # with allure.step('Count number of SDK extended dumps on dut after stuck occurred'):
    #     number_of_sdk_error_after = generate_tech_support_and_count_sdk_dumps(duthost)
    #     assert number_of_sdk_error_after == pre_stuck_dumps + 1

    with allure.step('Rebooting the system - necessary to restart the iRISCs'):
        cli_objects.dut.general.reboot_flow(engines.dut, reboot_type='reboot', topology_obj=topology_obj)


@pytest.fixture(autouse=True)
def ignore_techsupport_expected_loganalyzer_exceptions(loganalyzer):
    """
    expanding the ignore list of the loganalyzer for these tests because of reboot.
    :param loganalyzer: loganalyzer utility fixture
    :return: None
    """
    if loganalyzer:
        ignore_regex_list = \
            loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                               "log_analyzer_techsupport_ignore.txt")))
        loganalyzer.ignore_regex.extend(ignore_regex_list)


def test_techsupport_mellanox_sdk_dump(engines, loganalyzer):
    duthost = engines.dut

    with allure.step('Copy to dut a script that triggers SDK health event'):
        cp_sdk_event_trigger_script_to_dut_syncd(duthost)

    logger.debug("Running show techsupport ... ")
    with allure.step('STEP1: Count number of SDK extended dumps at dut before test'):
        number_of_sdk_error_before = generate_tech_support_and_count_sdk_dumps(duthost)

    with allure.step('STEP2: Trigger SDK health event at dut'):
        duthost.run_cmd('docker exec -it syncd python mellanox_sdk_trigger_event_script.py')
        loganalyzer.expect_regex.extend(["Health event happened, severity"])

    with allure.step('STEP3: Count number of SDK extended dumps at dut after event occurred'):
        number_of_sdk_error_after = generate_tech_support_and_count_sdk_dumps(duthost)

    with allure.step('Validate that the tecsupport file contain one more SDK extended dump'):
        assert number_of_sdk_error_after == number_of_sdk_error_before + 1


def cp_sdk_event_trigger_script_to_dut_syncd(engine):
    dst = os.path.join('/tmp', 'mellanox_sdk_trigger_event_script.py')
    engine.copy_file(source_file=os.path.join(FILES_DIR, 'mellanox_sdk_trigger_event_script.py'),
                     dest_file='mellanox_sdk_trigger_event_script.py',
                     file_system='/tmp',
                     direction='put'
                     )
    engine.run_cmd('docker cp {} {}'.format(dst, 'syncd:/'))


def generate_tech_support_and_count_sdk_dumps(engine):
    sdk_dump_dir = 'sai_sdk_dump'
    sdk_file_pattern = 'sai-dfw-.*'

    output_lines = engine.run_cmd('show techsupport').split('\n')

    tar_file = output_lines[len(output_lines) - 1]
    tarball_file_name = str(tar_file.replace('/var/dump/', ''))
    tarball_dir_name = str(tarball_file_name.replace('.tar.gz', ''))

    sdk_dump_pattern = '{}/{}/{}'.format(tarball_dir_name, sdk_dump_dir, sdk_file_pattern)

    engine.copy_file(source_file=tar_file, dest_file=tarball_file_name, file_system='/tmp/', direction='get')

    t = tarfile.open(tarball_file_name, "r")

    filenames = t.getnames()
    r = re.compile(sdk_dump_pattern)

    after_list = list(filter(r.match, filenames))

    engine.run_cmd("rm -rf {}".format(tar_file))
    return len(after_list)


def verify_sdkdump_created(engine, before):
    after = engine.run_cmd('ls -t {}/*.tar | wc -l'.format(SDK_DUMP_DIR))
    assert after > before, 'Did not create DumpMe dump'


def stop_irisics(chip_type, host):
    if chip_type == 'SPC':
        host.run_cmd('sudo mcra /dev/mst/mt52100_pci_cr0 0xa01e4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt52100_pci_cr0 0xa05e4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt52100_pci_cr0 0xa07e4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt52100_pci_cr0 0xa09e4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt52100_pci_cr0 0xa0be4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt52100_pci_cr0 0xa0de4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt52100_pci_cr0 0xa0fe4 0x10')
    elif chip_type == 'SPC2':
        host.run_cmd('sudo mcra /dev/mst/mt53100_pci_cr0 0xa01e4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53100_pci_cr0 0xa05e4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53100_pci_cr0 0xa07e4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53100_pci_cr0 0xa09e4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53100_pci_cr0 0xa0be4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53100_pci_cr0 0xa0de4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53100_pci_cr0 0xa0fe4 0x10')
    elif chip_type == 'SPC3':
        host.run_cmd('sudo mcra /dev/mst/mt53104_pci_cr0 0xa01c4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53104_pci_cr0 0xa05c4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53104_pci_cr0 0xa07c4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53104_pci_cr0 0xa09c4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53104_pci_cr0 0xa0bc4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53104_pci_cr0 0xa0dc4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53104_pci_cr0 0xa0fc4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53104_pci_cr0 0xa11c4 0x10')
        host.run_cmd('sudo mcra /dev/mst/mt53104_pci_cr0 0xa11c4 0x10')
    else:
        raise ValueError("Not supported chip type: {}".format(chip_type))


def check_all_dumps_file_exsits(engine):
    # DumpMe dumps should contain the following dumps:
    # 3 CR space dumps
    # SDK dump
    # mlxtrace dump
    # FW core dump - only on FW event from level CRITICAL or ERROR

    latest_fw_dump = engine.run_cmd('ls -t {}/*.tar | head -1'.format(SDK_DUMP_DIR))
    output_fw_dump = engine.run_cmd('sudo tar -tf {}'.format(latest_fw_dump))

    # Check CR space dump:
    assert output_fw_dump.count('sdkdump_ext_cr_') == 3, 'Missing CR space dump'
    assert output_fw_dump.count('sdkdump_ext_meta_001-') == 3, 'Missing CR space metafiles'
    # Check SDK dump:
    assert 'sai_sdk_dump.txt' in output_fw_dump, 'Missing SDK dump'
    # Check mlxtrace dump:
    assert '_pci_cr0_mlxtrace.trc' in output_fw_dump, 'Missing mlxtrace'
    # Check FW core dump:
    # This should be uncomment when FW stuck event level would change to critical
    # assert 'ir_core_dump_' in output, 'Missing FW core dump'
