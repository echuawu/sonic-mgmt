from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.RemoteAaaResource import RemoteAaaResource


class Radius(RemoteAaaResource):
    def __init__(self, parent_obj=None):
        super().__init__(parent_obj)
        self._resource_path = '/radius'
        self.rad_hostname = RadiusHostname(self)


class RadiusHostname(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/hostname')

    def set_param(self, hostname, param, value, apply=False, ask_for_confirmation=False):
        radius_hostname = BaseComponent(self, path='/' + hostname)
        return radius_hostname.set(param, value, apply=apply, ask_for_confirmation=ask_for_confirmation)

    def unset_hostname(self, hostname, apply=False, ask_for_confirmation=False):
        radius_hostname = BaseComponent(self, path='/' + hostname)
        return radius_hostname.unset(apply=apply, ask_for_confirmation=ask_for_confirmation)

    def show_hostname(self, hostname, rev=''):
        radius_hostname = BaseComponent(self, path='/' + hostname)
        return radius_hostname.show(rev=rev)
