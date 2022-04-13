#!/usr/bin/env python
import allure
import logging


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
        cli_obj = topology_obj.players['dut']['cli']
        target_image, _ = cli_obj.general.get_base_and_target_images()
        with allure.step(f"Set {target_image} as default image"):
            delimiter = cli_obj.general.get_installer_delimiter()
            cli_obj.general.set_default_image(target_image, delimiter)
        with allure.step('Rebooting the dut'):
            dut_engine.reload(['sudo reboot'])
        with allure.step('Verifying dut booted with correct image'):
            delimiter = cli_obj.general.get_installer_delimiter()
            image_list = cli_obj.general.get_sonic_image_list(delimiter)
            assert f'Current: {target_image}' in image_list, f'Current: {target_image} not in {image_list}'
        with allure.step("Verify basic container is up"):
            cli_obj.general.verify_dockers_are_up()

    except Exception as err:
        raise AssertionError(err)
