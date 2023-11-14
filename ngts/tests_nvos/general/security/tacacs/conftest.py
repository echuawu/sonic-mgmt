import pytest


@pytest.fixture(scope='session', autouse=True)
def prepare_scp_test(prepare_scp):
    return
