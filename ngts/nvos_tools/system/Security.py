from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_tools.system.PasswordHardening import PasswordHardening
from ngts.nvos_tools.system.Certificate import Certificate


class Security(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/security')
        self.password_hardening = PasswordHardening(self)
        self.certificate = Certificate(self)

    def unset(self, op_param=""):
        raise Exception("unset is not implemented for /security")
