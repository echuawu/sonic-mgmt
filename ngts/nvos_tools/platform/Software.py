from ngts.nvos_tools.infra.BaseComponent import BaseComponent


class Software(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/software')
        self.installed = BaseComponent(self, path='/installed')
        self.role = BaseComponent(self, path='/role')

    def unset(self, op_param=""):
        raise Exception("unset is not implemented")

    def set(self, op_param_name="", op_param_value={}):
        raise Exception("set is not implemented")
