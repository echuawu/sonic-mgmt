import pytest
import logging

logger = logging.getLogger()


@pytest.fixture(scope='session', autouse=True)
def install_gnmi_on_sonic_mgmt(engines):
    """
    enable rsyslog on sonic-mgmt container
    """
    gnmic_install_output = engines.sonic_mgmt.run_cmd("bash -c \"$(curl -sL https://get-gnmic.openconfig.net)\"")
    assert 'gnmic installed into /usr/local/bin/gnmic' in gnmic_install_output \
           or 'gnmic is already at latest' in gnmic_install_output, f"gnmic installation failed with: {gnmic_install_output}"
