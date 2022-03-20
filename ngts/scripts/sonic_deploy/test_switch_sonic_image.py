#!/usr/bin/env python
import allure
import logging
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


logger = logging.getLogger()


@allure.title('Switch sonic image')
def test_switch_sonic_image(topology_obj, setup_name):
    """
    This script will swtich sonic image on the dut.
    :param topology_obj: topology object fixture
    :param setup_name: setup_name fixture
    :return: raise assertion error in case of script failure
    """
    try:
        dut_engine = topology_obj.players['dut']['engine']
        target_image, _ = SonicGeneralCli().get_base_and_target_images(dut_engine)
        with allure.step(f"Set {target_image} as default image"):
            delimiter = SonicGeneralCli().get_installer_delimiter(dut_engine)
            SonicGeneralCli().set_default_image(dut_engine, target_image, delimiter)
        with allure.step('Rebooting the dut'):
            dut_engine.reload(['sudo reboot'])
        with allure.step('Verifying dut booted with correct image'):
            delimiter = SonicGeneralCli().get_installer_delimiter(dut_engine)
            image_list = SonicGeneralCli().get_sonic_image_list(dut_engine, delimiter)
            assert f'Current: {target_image}' in image_list, f'Current: {target_image} not in {image_list}'
        with allure.step("Verify basic container is up"):
            SonicGeneralCli().verify_dockers_are_up(dut_engine)

    except Exception as err:
        raise AssertionError(err)
