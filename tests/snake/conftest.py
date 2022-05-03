import allure
import pytest
import time

from tests.common.platform.device_utils import fanout_switch_port_lookup

from snake_common import ssh_client, onyx_cmd, get_sku, generate_vlans, emit_sonic_config, emit_onyx_config

# Default authentication (eventually use Noga for this)

SONIC_USER = "admin"
SONIC_PASS = "YourPaSsWoRd"

ONYX_USER = "admin"
ONYX_PASS = "admin"

# Globals

SONIC_CONFIG = "/etc/sonic/config_db.json"
ONYX_CONFIG = "/var/home/root/config.bak"

def pytest_generate_tests(metafunc):
    val = metafunc.config.getoption('--sku')
    if 'sku_name' in metafunc.fixturenames and val is not None:
        metafunc.parametrize('sku_name', [val], scope="module")

@pytest.fixture(scope='module')
def generate_sku(duthost, sku_name):

    sonic, sonic_file = ssh_client(duthost.hostname, SONIC_USER, SONIC_PASS)

    allure.step("Generate SKU VLANs")
    sku_dat = get_sku(sonic, sonic_file, sku_name)
    config = generate_vlans(sku_dat)
    emit_onyx_config(sku_dat, **config)
    emit_sonic_config(sku_dat, **config)
    return max([vrf[0] for vlan, vrf in config["dut_vrf_map"].items()])

@pytest.fixture(scope='module')
def configure_switches(duthost, localhost, fanouthosts, generate_sku):

    fanout, fanout_port = fanout_switch_port_lookup(fanouthosts, duthost.hostname, "Ethernet0")

    sonic, sonic_file = ssh_client(duthost.hostname, SONIC_USER, SONIC_PASS)
    onyx, onyx_file = ssh_client(fanout.hostname, ONYX_USER, ONYX_PASS)

    # Backup running configurations
    allure.step("Back up running configurations")
    sonic.exec_command("sudo config save -y")
    sonic_file.get(SONIC_CONFIG)

    onyx_cmd(onyx, ["en", "con term", "con upload active scp://{}:{}@localhost:{}".format(ONYX_USER, ONYX_PASS, ONYX_CONFIG)])
    onyx_file.get(ONYX_CONFIG)

    allure.step("Deploy configuration to DUT")
    sonic_file.put("sku.json", "/home/{}/sku.json".format(SONIC_USER))
    stdin, stdout, stderr = sonic.exec_command("sudo cp /home/{}/sku.json {}".format(SONIC_USER, SONIC_CONFIG))
    stdout.readline()
    stdin, stdout, stderr = sonic.exec_command("sudo config reload -y")
    stdout.readline()


    allure.step("Deploy configuration to Fanout")
    onyx_cmd(onyx, ["en", "con term", "con delete snake"])
    onyx_cmd(onyx, ["en", "con term", "con new snake", "con switch snake"])
    onyx.close()
    time.sleep(300)

    localhost.wait_for(host=fanout.hostname, port=22, state='started', delay=10, timeout=300)
    onyx, onyx_file = ssh_client(fanout.hostname, ONYX_USER, ONYX_PASS)

    # Work around calcmgrd rules
    sonic.exec_command("sudo iptables -D INPUT -d 10.5.0.1/32 -j DROP")

    onyx_file.put("onyx-config", "/var/home/root/sku-config")
    onyx_cmd(onyx, ["en", "con term", "con text file sku-config delete"])
    onyx_cmd(onyx, ["en", "con term", "con text fetch scp://{}:{}@localhost/var/home/root/sku-config".format(ONYX_USER, ONYX_PASS)])
    onyx_cmd(onyx, ["en", "con term", "con text file sku-config apply"])
    time.sleep(60)

    yield generate_sku

    allure.step("Restore DUT configuration backup")
    sonic_file.put("config_db.json", "/home/{}/config_db.json".format(SONIC_USER))
    stdin, stdout, stderr = sonic.exec_command("sudo cp /home/{}/config_db.json {}".format(SONIC_USER, SONIC_CONFIG))
    stdout.readline()
    stdin, stdout, stderr = sonic.exec_command("sudo reboot")

    allure.step("Restore Fanout configuration backup")
    onyx_file.put("config.bak", ONYX_CONFIG)
    onyx_cmd(onyx, ["en", "con term", "con delete config.bak"])
    onyx_cmd(onyx, ["en", "con term", "con fetch scp://{}:{}@localhost:{}".format(ONYX_USER, ONYX_PASS, ONYX_CONFIG)])
    onyx_cmd(onyx, ["en", "con term", "con switch config.bak"])

    localhost.wait_for(host=duthost.hostname, port=22, state='started', delay=10, timeout=300)
    localhost.wait_for(host=fanout.hostname, port=22, state='started', delay=10, timeout=300)

