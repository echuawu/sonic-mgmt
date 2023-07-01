import allure
import logging
import pytest


logger = logging.getLogger()


@pytest.mark.disable_loganalyzer
@allure.title('Verify secure boot is enabled')
def test_verify_secure_is_enabled(topology_obj):
    """
    This script will verify secure boot is enabled on the dut.
    :param topology_obj: topology object fixture
    :return: raise assertion error in case of script failure
    """

    logger.info("Check the secure boot status")
    engine = topology_obj.players['dut']['engine']
    secure_boot_state = engine.run_cmd('mokutil --sb-state')
    assert 'enabled' in secure_boot_state, "Secure boot not enabled as expected"

    logger.info("Check the secure boot is dev or prod")
    mst_info = engine.run_cmd('sudo flint -d /dev/mst/mt53120_pciconf0 q full')
    assert "Security Attributes:   secure-fw, dev" in mst_info, "Secure boot not enabled as dev"
