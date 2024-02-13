import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.infra.NvosTestToolkit import TestToolkit
from ngts.nvos_constants.constants_nvos import ApiType, AclConsts


logger = logging.getLogger()


class Match(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/match')
        self.ip = Ip(self)


class Ip(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/ip')
        self.source_port = SourcePort(self)
        self.dest_port = DestPort(self)
        self.ecn = Ecn(self)
        self.udp = UDP(self)
        self.tcp = TCP(self)
        self.state = BaseComponent(self, path='/state')
        self.recent_list = RecentList(self)
        self.hashlimit = Hashlimit(self)

    def set_source_ip(self, source_ip):
        return self.set(AclConsts.SOURCE_IP, source_ip)

    def set_dest_ip(self, dest_ip):
        return self.set(AclConsts.DEST_IP, dest_ip)

    def set_protocol(self, protocol):
        return self.set(AclConsts.PROTOCOL, protocol)

    def set_icmp_type(self, icmp_type):
        return self.set(AclConsts.ICMP_TYPE, icmp_type)

    def set_icmpv6_type(self, icmpv6_type):
        return self.set(AclConsts.ICMPV6_TYPE, icmpv6_type)

    def set_fragment(self):
        return self.set(AclConsts.FRAGMENT)


class SourcePort(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/source-port')
        self.ports_dict = {}

    def set(self, port_id, expected_str='', apply=False, ask_for_confirmation=False):
        port_value = {} if TestToolkit.tested_api == ApiType.OPENAPI else ""
        result_obj = BaseComponent.set(self, op_param_name=port_id, op_param_value=port_value, expected_str=expected_str,
                                       apply=apply, ask_for_confirmation=ask_for_confirmation)
        if result_obj.result:
            port_id_obj = PortID(port_id=port_id, parent_obj=self)
            self.ports_dict.update({port_id: port_id_obj})
        return result_obj

    def unset(self, port_id="", expected_str='', apply=False, ask_for_confirmation=False):
        if port_id:
            result_obj = BaseComponent.unset(self.ports_dict[port_id], expected_str=expected_str, apply=apply,
                                             ask_for_confirmation=ask_for_confirmation)
            if result_obj.result:
                self.ports_dict.pop(port_id)
        else:
            result_obj = BaseComponent.unset(self, expected_str=expected_str, apply=apply,
                                             ask_for_confirmation=ask_for_confirmation)
            if result_obj.result:
                self.ports_dict = {}
        return result_obj


class DestPort(SourcePort):

    def __init__(self, parent_obj=None):
        super().__init__(parent_obj=parent_obj)
        self._resource_path = '/dest-port'
        self.ports_dict = {}


class PortID(BaseComponent):

    def __init__(self, port_id, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path=f'/{port_id}')


class UDP(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/udp')


class TCP(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/tcp')
        self.flags = BaseComponent(parent=self, path='/flags')
        self.mask = BaseComponent(self, path='/mask')

    def set_tcpmss(self, tcpmss):
        return self.set(AclConsts.TCPMSS, tcpmss)

    def set_all_tcpmss_except(self, tcpmss):
        return self.set(AclConsts.ALL_TCPMSS_EXCEPT, tcpmss)


class Ecn(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/ecn')
        self.flags = BaseComponent(parent=self, path='/flags')

    def set_ecn_ip_ect(self, ip_ect):
        return self.set(AclConsts.IP_ECT, ip_ect)


class RecentList(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/recent-list')

    def set_name(self, name):
        return self.set('name', name)

    def set_update_interval(self, update_interval):
        return self.set('update-interval', update_interval)

    def set_hit_count(self, hit_count):
        return self.set('hit-count', hit_count)


class Hashlimit(BaseComponent):

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/hashlimit')

    def set_name(self, name):
        return self.set('name', name)

    def set_rate_limit(self, rate_limit):
        return self.set('rate', rate_limit)

    def set_burst(self, burst):
        return self.set('burst', burst)

    def set_destination_mask(self, mask):
        return self.set('destination-mask', mask)

    def set_source_mask(self, mask):
        return self.set('source-mask', mask)

    def set_expire(self, expire):
        return self.set('expire', expire)

    def set_mode(self, mode):
        return self.set('mode', mode)
