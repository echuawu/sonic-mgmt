from ngts.nvos_tools.infra.BaseComponent import BaseComponent


class Hardware(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/hardware')
        self.transceiver = BaseComponent(self, path='/transceiver')

    def unset(self, op_param=""):
        raise Exception("unset is not implemented")

    def set(self, op_param_name="", op_param_value={}):
        raise Exception("set is not implemented")
