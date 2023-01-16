import allure
import pytest
import json
from tests.common.dualtor.dual_tor_utils import upper_tor_host, lower_tor_host  # noqa: F401
from tests.common import config_reload

pytestmark = [
    pytest.mark.topology("dualtor"),
    pytest.mark.skip_check_dut_health,
    pytest.mark.disable_loganalyzer
]


def test_update_mux_tunnel_config(upper_tor_host, lower_tor_host):
    """
    This test is to remove the dscp remapping configurations in config db TUNNEL|MuxTunnel0.
    It's a temporary test, remove it when dscp remapping is available in the image.
    """
    with allure.step("Remove the existing MuxTunnel0 configurations:"):
        upper_tor_host.shell('redis-cli -n 4 del "TUNNEL|MuxTunnel0"')
        lower_tor_host.shell('redis-cli -n 4 del "TUNNEL|MuxTunnel0"')
    with allure.step("Add the new MuxTunnel0 configurations:"):
        upper_tor_tunnel_params = {
            'TUNNEL': {
                'MuxTunnel0': {
                    'dscp_mode': 'uniform',
                    'src_ip': '10.1.0.33',
                    'dst_ip': '10.1.0.32',
                    'ecn_mode': 'copy_from_outer',
                    'encap_ecn_mode': 'standard',
                    'ttl_mode': 'pipe',
                    'tunnel_type': 'IPINIP'
                }
            }
        }
        lower_tor_tunnel_params = {
            'TUNNEL': {
                'MuxTunnel0': {
                    'dscp_mode': 'uniform',
                    'src_ip': '10.1.0.32',
                    'dst_ip': '10.1.0.33',
                    'ecn_mode': 'copy_from_outer',
                    'encap_ecn_mode': 'standard',
                    'ttl_mode': 'pipe',
                    'tunnel_type': 'IPINIP'
                }
            }
        }
        upper_tor_host.copy(content=json.dumps(upper_tor_tunnel_params, indent=2), dest="/tmp/tunnel_params.json")
        upper_tor_host.shell("sonic-cfggen -j /tmp/tunnel_params.json --write-to-db")
        lower_tor_host.copy(content=json.dumps(lower_tor_tunnel_params, indent=2), dest="/tmp/tunnel_params.json")
        lower_tor_host.shell("sonic-cfggen -j /tmp/tunnel_params.json --write-to-db")
    with allure.step("Disable qos remapping:"):
        upper_tor_host.shell('redis-cli -n 4 hset "SYSTEM_DEFAULTS|tunnel_qos_remap" status disabled')
        lower_tor_host.shell('redis-cli -n 4 hset "SYSTEM_DEFAULTS|tunnel_qos_remap" status disabled')
    with allure.step("Save configuration and reload:"):
        upper_tor_host.shell("config save -y")
        upper_tor_host.shell("rm -f /etc/sonic/running_golden_config.json")
        config_reload(upper_tor_host, safe_reload=True)
        lower_tor_host.shell("config save -y")
        lower_tor_host.shell("rm -f /etc/sonic/running_golden_config.json")
        config_reload(lower_tor_host, safe_reload=True)
