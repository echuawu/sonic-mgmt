from ngts.nvos_tools.infra.BaseComponent import BaseComponent


class Inventory(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/inventory')

    def unset(self, op_param=""):
        raise NotImplementedError

    def set(self, op_param_name="", op_param_value={}):
        raise NotImplementedError
