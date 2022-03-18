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
from ngts.cli_wrappers.sonic.sonic_arp_clis import SonicArpCli

from ngts.cli_util.stub_engine import StubEngine
from dotted_dict import DottedDict
logger = logging.getLogger()


class SonicCli:
    def __init__(self, topology):
        branch = topology.players['dut'].get('branch')
        engine = topology.players['dut']['engine']

        self.ip = SonicIpCli(engine=engine)
        self.arp = SonicArpCli(engine=engine)
        self.lldp = SonicLldpCli(engine=engine)
        self.mac = SonicMacCli(engine=engine)
        self.vlan = SonicVlanCli(branch=branch, engine=engine)
        self.lag = SonicLagLacpCli(engine=engine)
        self.interface = SonicInterfaceCli(engine=engine)
        self.route = SonicRouteCli(engine=engine)
        self.vrf = SonicVrfCli(engine=engine)
        self.chassis = SonicChassisCli(engine=engine)
        self.general = SonicGeneralCli(branch=branch, engine=engine)
        self.dhcp_relay = SonicDhcpRelayCli(branch=branch, engine=engine)
        self.ifconfig = SonicIfconfigCli()
        self.crm = SonicCrmCli(engine=engine)
        self.acl = SonicAclCli(engine=engine)
        self.vxlan = SonicVxlanCli(engine=engine)
        self.frr = SonicFrrCli(engine=engine)
        self.bgp = SonicBgpCli(engine=engine)
        self.counterpoll = SonicCounterpollCli(engine=engine)
        self.flowcnt = SonicFlowcntCli(engine=engine)
        self.app_ext = SonicAppExtensionCli(engine=engine)


class SonicCliStub(SonicCli):
    def __init__(self, topology):
        stub_topo = DottedDict()
        stub_topo.players = {'dut': {'engine': StubEngine()}}
        super().__init__(stub_topo)
