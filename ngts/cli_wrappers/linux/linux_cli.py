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
logger = logging.getLogger()


class LinuxCli:
    def __init__(self, engine):
        self.engine = engine

        self._ip = None
        self._lldp = None
        self._lag = None
        self._interface = None
        self._vlan = None
        self._route = None
        self._vrf = None
        self._mac = None
        self._chassis = None
        self._general = None
        self._dhcp = None
        self._ifconfig = None
        self._vxlan = None
        self._frr = None
        self._bgp = None
        self._counterpoll = None

    @property
    def ip(self):
        if self._ip is None:
            self._ip = LinuxIpCli(engine=self.engine)
        return self._ip

    @property
    def lldp(self):
        if self._lldp is None:
            self._lldp = LinuxLldpCli(engine=self.engine)
        return self._lldp

    @property
    def lag(self):
        if self._lag is None:
            self._lag = LinuxLagLacpCli(engine=self.engine, cli_obj=self)
        return self._lag

    @property
    def interface(self):
        if self._interface is None:
            self._interface = LinuxInterfaceCli(engine=self.engine)
        return self._interface

    @property
    def vlan(self):
        if self._vlan is None:
            self._vlan = LinuxVlanCli(engine=self.engine, cli_obj=self)
        return self._vlan

    @property
    def route(self):
        if self._route is None:
            self._route = LinuxRouteCli(engine=self.engine)
        return self._route

    @property
    def vrf(self):
        if self._vrf is None:
            self._vrf = LinuxVrfCli()
        return self._vrf

    @property
    def mac(self):
        if self._mac is None:
            self._mac = LinuxMacCli(engine=self.engine)
        return self._mac

    @property
    def chassis(self):
        if self._chassis is None:
            self._chassis = LinuxChassisCli(engine=self.engine)
        return self._chassis

    @property
    def general(self):
        if self._general is None:
            self._general = LinuxGeneralCli(engine=self.engine)
        return self._general

    @property
    def dhcp(self):
        if self._dhcp is None:
            self._dhcp = LinuxDhcpCli(engine=self.engine)
        return self._dhcp

    @property
    def ifconfig(self):
        if self._ifconfig is None:
            self._ifconfig = LinuxIfconfigCli(engine=self.engine)
        return self._ifconfig

    @property
    def vxlan(self):
        if self._vxlan is None:
            self._vxlan = LinuxVxlanCli(engine=self.engine, cli_obj=self)
        return self._vxlan

    @property
    def frr(self):
        if self._frr is None:
            self._frr = LinuxFrrCli(engine=self.engine)
        return self._frr

    @property
    def bgp(self):
        if self._bgp is None:
            self._bgp = LinuxBgpCli()
        return self._bgp

    def counterpoll(self):
        if self._counterpoll is None:
            self._counterpoll = LinuxCounterpollCli()
        return self._counterpoll


class LinuxCliStub(LinuxCli):
    def __init__(self, engine):
        super().__init__(StubEngine())
