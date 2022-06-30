import pytest
import os
import logging
import allure

START_SCRIPT = 'tcpdump_start.sh'
STOP_SCRIPT = 'tcpdump_stop.sh'
FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
START_SCRIPT_PATH = os.path.join(FOLDER_PATH, START_SCRIPT)
STOP_SCRIPT_PATH = os.path.join(FOLDER_PATH, STOP_SCRIPT)

logger = logging.getLogger()


@pytest.fixture()
def tcpdump_debug(engines, interfaces):

    interfaces_dict = {
        engines.dut: [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_hb_2],
        engines.ha: [interfaces.ha_dut_1, interfaces.ha_dut_2],
        engines.hb: [interfaces.hb_dut_1, interfaces.hb_dut_2]
    }

    dumps_result_dict = {}

    for engine, interfaces_list in interfaces_dict.items():
        # Copy tcpdump start/stop script
        engine.copy_file(source_file=START_SCRIPT_PATH, file_system='/tmp', dest_file=START_SCRIPT)
        engine.run_cmd(f'sudo chmod +x /tmp/{START_SCRIPT}')
        engine.copy_file(source_file=STOP_SCRIPT_PATH, file_system='/tmp', dest_file=STOP_SCRIPT)
        engine.run_cmd(f'sudo chmod +x /tmp/{STOP_SCRIPT}')

        dumps_result_dict[engine] = []
        for interface in interfaces_list:
            pcap_dump_path = f'/tmp/dump_{interface}.pcap'
            engine.run_cmd(f'sudo /tmp/{START_SCRIPT} "-i {interface} -e -n -w {pcap_dump_path}" tcpdump_{interface}')
            dumps_result_dict[engine].append(pcap_dump_path)

        engine.run_cmd('sudo ps -aux')

    yield

    for engine, interfaces_list in interfaces_dict.items():
        for interface in interfaces_list:
            engine.run_cmd(f'sudo /tmp/{STOP_SCRIPT} tcpdump_{interface}')

        engine.run_cmd('sudo ps -aux')

    for engine, dumps_list in dumps_result_dict.items():
        for dump_file_path in dumps_list:
            dump_file_name = dump_file_path.split('/tmp/')[1]
            dst_file = os.path.join(FOLDER_PATH, dump_file_name)
            try:
                engine.copy_file(source_file=dump_file_name, dest_file=dst_file, file_system='/tmp/', direction='get')
                allure.attach.file(dst_file, dump_file_name, allure.attachment_type.PCAP)
            except Exception as err:
                logger.error(f'Can not attach file to Allure report. Got error: {err}')
