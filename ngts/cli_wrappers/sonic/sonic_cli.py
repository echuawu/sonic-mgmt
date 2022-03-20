import logging

from ngts.cli_wrappers.sonic.sonic_ip_clis import SonicIpCli
from ngts.cli_wrappers.sonic.sonic_lag_lacp_clis import SonicLagLacpCli
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.cli_wrappers.sonic.sonic_lldp_clis import SonicLldpCli
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from ngts.cli_wrappers.sonic.sonic_vlan_clis import SonicVlanCli
from ngts.cli_wrappers.sonic.sonic_route_clis import SonicRouteCli
from ngts.cli_wrappers.sonic.sonic_vrf_clis import SonicVrfCli
from ngts.cli_wrappers.sonic.sonic_chassis_clis import SonicChassisCli
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.cli_wrappers.sonic.sonic_dhcp_relay_clis import SonicDhcpRelayCli
from ngts.cli_wrappers.sonic.sonic_ifconfig_clis import SonicIfconfigCli
from ngts.cli_wrappers.sonic.sonic_crm_clis import SonicCrmCli
from ngts.cli_wrappers.sonic.sonic_acl_clis import SonicAclCli
from ngts.cli_wrappers.sonic.sonic_vxlan_clis import SonicVxlanCli
from ngts.cli_wrappers.sonic.sonic_frr_cli import SonicFrrCli
from ngts.cli_wrappers.sonic.sonic_bgp_clis import SonicBgpCli
from ngts.cli_wrappers.sonic.sonic_counterpoll_clis import SonicCounterpollCli
from ngts.cli_wrappers.sonic.sonic_flowcnt_clis import SonicFlowcntCli
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli

logger = logging.getLogger()


class SonicCli:
    def __init__(self, topology):
        branch = topology.players['dut'].get('branch')

        self.ip = SonicIpCli()
        self.lldp = SonicLldpCli()
        self.mac = SonicMacCli()
        self.vlan = SonicVlanCli(branch=branch)
        self.lag = SonicLagLacpCli()
        self.interface = SonicInterfaceCli()
        self.route = SonicRouteCli()
        self.vrf = SonicVrfCli()
        self.chassis = SonicChassisCli()
        self.general = SonicGeneralCli(branch=branch)
        self.dhcp_relay = SonicDhcpRelayCli(branch=branch)
        self.ifconfig = SonicIfconfigCli()
        self.crm = SonicCrmCli()
        self.acl = SonicAclCli()
        self.vxlan = SonicVxlanCli()
        self.frr = SonicFrrCli()
        self.bgp = SonicBgpCli()
        self.counterpoll = SonicCounterpollCli()
        self.flowcnt = SonicFlowcntCli()
        self.app_ext = SonicAppExtensionCli()
