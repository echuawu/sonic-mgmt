from abc import ABC, abstractmethod


class IpCliInterface(ABC):

    @abstractmethod
    def add_ip_to_interface(self, interface, ip, mask):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @abstractmethod
    def del_ip_from_interface(self, interface, ip, mask):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
