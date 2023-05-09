from ngts.nvos_tools.system.System import System
from ngts.nvos_constants.constants_nvos import NvosConst
from ngts.nvos_tools.infra.ValidationTool import ValidationTool
from infra.tools.general_constants.constants import DefaultConnectionValues
import allure
import logging
import pytest
import time

logger = logging.getLogger()


@pytest.mark.system
def test_fw_dump_me(engines):
    """
    Test flow:
        1. Upload fw crush script to switch
        2. Copy script to syncd-ibv0 container
        3. Execute fw stuck script
        4. Validate logs and sdk dump created
        5. Try to download sdk dump to shared location
        6. Validate and delete
    """
    system = System(None)
    with allure.step('Upload sdk fw crush file to switch'):
        player_engine = engines['sonic_mgmt']
        player_engine.upload_file_using_scp(dest_username=DefaultConnectionValues.ADMIN,
                                            dest_password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                            dest_folder=NvosConst.DESTINATION_FW_SCRIPT_PATH,
                                            dest_ip=engines.dut.ip,
                                            local_file_path=NvosConst.FW_DUMP_ME_SCRIPT_PATH)

    with allure.step('Copy sxd api crash fw file to the syncd-ibv0 container'):
        engines.dut.run_cmd('sudo docker cp /var/tmp/sxd_api_crash_fw.py syncd-ibv0:/tmp/')
        cmd_output = engines.dut.run_cmd('echo $?')
        assert '0' in cmd_output, "Docker copy finished with error"

    with allure.step('Delete all sdk dumps before fw crash script'):
        engines.dut.run_cmd('sudo rm -Rf /var/log/mellanox/sdk-dumps/sai-dfw*')

    with allure.step("Rotate logs"):
        logging.info("Rotate logs")
        system.log.rotate_logs()

    with allure.step('Exec sxd api crash fw from syncd-ibv0 docker'):
        cmd_output = engines.dut.run_cmd(
            'docker exec -i syncd-ibv0 bash -c "python /tmp/sxd_api_crash_fw.py --device_id 1"')
        assert "trigger_stack_overflow" in cmd_output, "SXD API CRASH script failed"

    with allure.step("Run nv show system log command follow to view system logs"):
        logging.info("Run nv show system log command follow to view system logs")
        show_output = system.log.show_log(exit_cmd='q')

    with allure.step('Verify updated SDK message in the logs as expected'):
        logging.info('Verify updated SDK message in the logs as expected')
        ValidationTool.verify_expected_output(show_output, '[HOST_INTERFACE.NOTICE] FW test event').verify_result()

    with allure.step('Validate if sdk_fw_dump created after 15 sec timeout'):
        logging.info('Validate if sdk_fw_dump created after 15 sec timeout')
        time.sleep(15)
        cmd_output = engines.dut.run_cmd('ls {0}'.format(NvosConst.SDK_DUMP_FOLDER))
        assert 'sai-dfw' in cmd_output, "Sdk dump not created"
        sdk_dump = cmd_output.split()[0]

    with allure.step('Validate upload sdkdump to sonic-mgmt'):
        logging.info('Validate upload sdkdump to sonic-mgmt')
        player_engine = engines['sonic_mgmt']
        player_engine.run_cmd(
            'sshpass -p {0} scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no {1}@{2}:{3}{4} {5}'.
            format(engines.dut.password, engines.dut.username, engines.dut.ip, NvosConst.SDK_DUMP_FOLDER,
                   sdk_dump, NvosConst.MARS_RESULTS_FOLDER))

        cmd_output = player_engine.run_cmd('ls {0} | grep {1}'.format(NvosConst.MARS_RESULTS_FOLDER, sdk_dump))
        assert sdk_dump in cmd_output, 'sdk dump not in results folder'

        logging.info('Delete dump file in Mars directory')
        player_engine.run_cmd('rm -f {0}{1}'.format(NvosConst.MARS_RESULTS_FOLDER, sdk_dump))
