import pytest
from infra.tools.general_constants.constants import DefaultConnectionValues
from ngts.nvos_constants.constants_nvos import MultiPlanarConsts
from ngts.nvos_tools.system.System import System
from ngts.tools.test_utils import allure_utils as allure
import subprocess


@pytest.fixture(scope='session', autouse=True)
def install_and_uninstall_platform_file(engines, devices):
    """
    install/uninstall xdr simulation on switch.
    """
    # TBD remove after new system arrived
    system = System(devices_dut=devices.dut)

    with allure.step("install xdr simulation on switch"):
        override_platform_file(system, engines, MultiPlanarConsts.SIMULATION_PATH)

    yield

    with allure.step("uninstall xdr simulation on switch"):
        override_platform_file(system, engines, MultiPlanarConsts.ORIGIN_FILES_PATH)


def override_platform_file(system, engines, path):
    """
    override platform file on switch.
    """
    player = engines['sonic_mgmt']
    engine = engines.dut

    # in case of installing xdr simulation, save the origin file in order to restore at the end of the test
    if path == MultiPlanarConsts.SIMULATION_PATH:
        with allure.step("Save the origin platform.json file"):
            file = MultiPlanarConsts.PLATFORM_PATH + MultiPlanarConsts.SIMULATION_FILE
            engine.run_cmd("sudo scp {} {}".format(file, MultiPlanarConsts.ORIGIN_FILES_PATH))  # TBD update command

    with allure.step("Override platform.json file"):
        file_path = path + MultiPlanarConsts.A_PORT_SPLIT_SIMULATION_FILE
        player.upload_file_using_scp(dest_username=DefaultConnectionValues.ADMIN,
                                     dest_password=DefaultConnectionValues.DEFAULT_PASSWORD,
                                     dest_folder=MultiPlanarConsts.INTERNAL_PATH,
                                     dest_ip=engine.ip,
                                     local_file_path=file_path)
        engine.run_cmd("sudo cp /tmp/{} {}".format(MultiPlanarConsts.A_PORT_SPLIT_SIMULATION_FILE,
                                                   MultiPlanarConsts.PLATFORM_PATH + MultiPlanarConsts.SIMULATION_FILE))

    with allure.step("Remove config_db.json and port_mapping.json files"):
        engine.run_cmd("sudo rm -f /etc/sonic/config_db.json")
        engine.run_cmd("sudo rm -f /etc/sonic/port_mapping.json")

    with allure.step("Perform system reboot"):
        system.reboot.action_reboot(params='force').verify_result()
