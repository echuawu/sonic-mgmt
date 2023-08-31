import random

import pytest

from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_tools.infra.SendCommandTool import SendCommandTool
from ngts.nvos_tools.system.System import System
from ngts.tests_nvos.general.security.authentication_restrictions.constants import RestrictionsConsts
from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts
from ngts.tests_nvos.general.security.security_test_tools.security_test_utils import set_local_users
from ngts.tools.test_utils import allure_utils as allure


@pytest.fixture(scope='function')
def test_user(engines):
    """
    @summary: Configure a test user
    @return: Test user info
        * as a dictionary { username: str, password: str, role: <admin/monitor> }
    """
    with allure.step('Configure test user'):
        user_details = random.choice(RestrictionsConsts.TEST_USERS).copy()
        user_details[AaaConsts.USERNAME] += str(random.randint(0, 9999))
        set_local_users(engines, [user_details], apply=True)

    yield user_details

    with allure.step(f'Clear user {user_details[AaaConsts.USERNAME]}'):
        System().aaa.user.unset(user_details[AaaConsts.USERNAME], apply=True)


@pytest.fixture(scope='function')
def test_users(engines):
    """
    @summary: Configure two test users
    @return: list of Test users info
        * as a dictionary { username: str, password: str, role: <admin/monitor> }
    """
    users = []
    with allure.step('Configure test users'):
        for _ in range(2):
            user_details = random.choice(RestrictionsConsts.TEST_USERS).copy()
            user_details[AaaConsts.USERNAME] += str(random.randint(0, 9999))
            set_local_users(engines, [user_details], apply=True)
            users.append(user_details)

    yield users

    for user_details in users:
        with allure.step(f'Clear user {user_details[AaaConsts.USERNAME]}'):
            System().aaa.user.unset(user_details[AaaConsts.USERNAME])

    with allure.step('Apply users unset'):
        SendCommandTool.execute_command(TestToolkit.GeneralApi[TestToolkit.tested_api].apply_config, engines.dut, True)


@pytest.fixture(scope='function', autouse=True)
def clear_users(engines):
    """
    @summary: Clear blocked users before and after test
    """
    yield

    with allure.step('Clear all configurations after test'):
        System().aaa.authentication.restrictions.action_clear()
