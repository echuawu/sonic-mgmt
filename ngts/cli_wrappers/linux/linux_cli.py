import logging
from ngts.cli_wrappers.linux.linux_interface_clis import LinuxInterfaceCli
from ngts.cli_wrappers.linux.linux_lag_lacp_clis import LinuxLagLacpCli
from ngts.cli_wrappers.linux.linux_ip_clis import LinuxIpCli
from ngts.cli_wrappers.linux.linux_lldp_clis import LinuxLldpCli
from ngts.cli_wrappers.linux.linux_vlan_clis import LinuxVlanCli
from ngts.cli_wrappers.linux.linux_route_clis import LinuxRouteCli
from ngts.cli_wrappers.linux.linux_vrf_clis import LinuxVrfCli
from ngts.cli_wrappers.linux.linux_chassis_clis import LinuxChassisCli
from ngts.cli_wrappers.linux.linux_mac_clis import LinuxMacCli
from ngts.cli_wrappers.linux.linux_general_clis import LinuxGeneralCli
from ngts.cli_wrappers.linux.linux_dhcp_clis import LinuxDhcpCli
from ngts.cli_wrappers.linux.linux_ifconfig_clis import LinuxIfconfigCli
from ngts.cli_wrappers.linux.linux_vxlan_clis import LinuxVxlanCli
from ngts.cli_wrappers.linux.linux_frr_cli import LinuxFrrCli
from ngts.cli_wrappers.linux.linux_bgp_clis import LinuxBgpCli
from ngts.cli_wrappers.linux.linux_counterpoll_clis import LinuxCounterpollCli

from ngts.cli_util.stub_engine import StubEngine
from dotted_dict import DottedDict
logger = logging.getLogger()


class LinuxCli:
    def __init__(self, engine):

        self.ip = LinuxIpCli(engine=engine)
        self.lldp = LinuxLldpCli(engine=engine)
        self.lag = LinuxLagLacpCli(engine=engine)
        self.interface = LinuxInterfaceCli(engine=engine)
        self.vlan = LinuxVlanCli(engine=engine)
        self.route = LinuxRouteCli(engine=engine)
        self.vrf = LinuxVrfCli()
        self.mac = LinuxMacCli(engine=engine)
        self.chassis = LinuxChassisCli(engine=engine)
        self.general = LinuxGeneralCli()
        self.dhcp = LinuxDhcpCli(engine=engine)
        self.ifconfig = LinuxIfconfigCli()
        self.vxlan = LinuxVxlanCli(engine=engine)
        self.frr = LinuxFrrCli(engine=engine)
        self.bgp = LinuxBgpCli()
        self.counterpoll = LinuxCounterpollCli()


class LinuxCliStub(LinuxCli):
    def __init__(self, engine):
        super().__init__(StubEngine())
