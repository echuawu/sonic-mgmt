from ngts.nvos_tools.infra.BaseComponent import BaseComponent


class PSRedundancy(BaseComponent):
    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/ps-redundancy')
