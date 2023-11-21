import logging
from ngts.nvos_tools.infra.BaseComponent import BaseComponent
from ngts.nvos_constants.constants_nvos import ComponentsConsts
logger = logging.getLogger()


class Component(BaseComponent):
    componentName = {}

    def __init__(self, parent_obj=None):
        BaseComponent.__init__(self, parent=parent_obj, path='/component')

        for name in ComponentsConsts.COMPONENTS_LIST:
            self.componentName.update({name: BaseComponent(self, path='/' + name)})
