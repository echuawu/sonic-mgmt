from abc import ABC, abstractmethod


class VxlanCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def configure_vxlan(engine, vxlan_info):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def delete_vxlan(engine, vxlan_info):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
