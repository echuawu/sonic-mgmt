from ngts.nvos_constants.constants_nvos import IpConsts
from ngts.nvos_tools.ib.InterfaceConfiguration.IbInterfaceDecorators import *
import random
import allure

logger = logging.getLogger()


class IpTool:
    @staticmethod
    def select_random_ipv4_address():
        """
        generate random ip, no multicast, no loopback, changed func to generate ip, not related to NVOS  Lab ip's,
        details in https://redmine.mellanox.com/issues/3242156
        :return: IP as a string (all the fields are 1-254)
        """
        with allure.step('Select random ipv4_address'):
            result_obj = ResultObj(True, "")
            msb_list = list(range(14, 127)) + list(range(128, 200))
            msb = random.choice(msb_list)
            result_obj.returned_value = ('{0}.{1}.{2}.{3}/{4}'.format(msb, random.randint(1, 254),
                                                                      random.randint(1, 254), random.randint(1, 254),
                                                                      random.randint(8, 32)))
            return result_obj

    @staticmethod
    def select_random_ipv6_address():
        """
        generate random ip, no multicast, no loopback
        :return: IP as a string (all the fields are 1-254)
        """
        with allure.step('Select random ipv4_address'):
            result_obj = ResultObj(True, "")
            ip_addr = ':'.join('{:x}'.format(random.
                                             randint(IpConsts.MIN_IPV6_GROUP_VALUE, IpConsts.MAX_IPV6_GROUP_VALUE))
                               for _ in range(8))

            result_obj.returned_value = ip_addr + ('/{0}'.format(random.randint(1, 128)))
            return result_obj
