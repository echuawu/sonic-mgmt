import logging
import random
from ngts.tools.test_utils import allure_utils as allure
import pytest
from infra.tools.general_constants.constants import DefaultConnectionValues


def test_grub_password(serial_engine, post_test_remote_reboot, is_secure_boot_enabled):
    '''
    @summary:
        This test case will check that entering grub command line will requires
        password, the username and password are defined at build stage.
        to enter grub cli, either you can press 'e' to 'c' when grub menu is presented.
        'e' - used to enter edit line
        'c' - grub command line
    :param serial_engine: pexpect serial engine
    '''
    with allure.step("Rebooting and entering grub cli"):
        logging.info("Rebooting and entering grub cli")
        serial_engine.serial_engine.sendline("nv action reboot system force")
        serial_engine.serial_engine.expect("select which entry is highlighted", timeout=120)

    cli_grub_activation_character = random.choice(['e', 'c'])
    with allure.step("Entering cli command-line using {} character".format(cli_grub_activation_character)):
        logging.info("Entering cli command-line using {} character".format(cli_grub_activation_character))
        serial_engine.serial_engine.send(cli_grub_activation_character)
        serial_engine.serial_engine.expect('username')

    with allure.step("Entering grub username: {}".format(DefaultConnectionValues.GRUB_USERNAME)):
        logging.info("Entering grub username: {}".format(DefaultConnectionValues.GRUB_USERNAME))
        serial_engine.serial_engine.sendline(DefaultConnectionValues.GRUB_USERNAME)
        serial_engine.serial_engine.expect('password')

    with allure.step("Entering grub password: {}".format(DefaultConnectionValues.GRUB_PASSWORD)):
        logging.info("Entering grub password: {}".format(DefaultConnectionValues.GRUB_PASSWORD))
        serial_engine.serial_engine.sendline(DefaultConnectionValues.GRUB_PASSWORD)
        serial_engine.serial_engine.expect(['grub>', 'discard edits and return to the GRUB menu'])

    with allure.step("Test is Done"):
        logging.info("Test is Done")
