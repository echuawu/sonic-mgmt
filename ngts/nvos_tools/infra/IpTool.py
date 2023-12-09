from ngts.nvos_constants.constants_nvos import IpConsts
from ngts.nvos_tools.infra.ResultObj import ResultObj
import logging
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

    @staticmethod
    def send_ufm_mad(host_obj, directory, lid, hca):
        """
        @Summary: This function will send a MAD from the host to the wanted asic by LID
        @param host_obj: Host object.
        @param directory: location to run nvmad
        @param lid: LID assigned by SM. The mad will be sent to this lid value.
        @param hca: card to host - e.g., mlx5_8
            Host object.
        @return: The MAD's output - > example:
            -I- received response length:256
            LID                                               : 1
            QPN                                               : 0x000001
            MAD.base_version                                  : 0x01
            MAD.mgmt_class                                    : 0x0a
            MAD.class_version                                 : 0x01
            MAD.method                                        : 0x81
            MAD.status                                        : 0x0000
            MAD.tid                                           : 0x00009e5500000002
            MAD.attr_id                                       : 0x0053
            MAD.modifier                                      : 0x00000000
            MAD.Vend_Key                                      : 0x0000000000000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv4[0].ipv4         : 0x00000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv4[0].netmask      : 0x00000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv4[1].ipv4         : 0x00000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv4[1].netmask      : 0x00000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv4[2].ipv4         : 0x00000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv4[2].netmask      : 0x00000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv4[3].ipv4         : 0x00000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv4[3].netmask      : 0x00000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv6[0].ipv6         : 0x00000000000000000000000000000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv6[0].netmask      : 0x00000000000000000000000000000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv6[1].ipv6         : 0x00000000000000000000000000000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv6[1].netmask      : 0x00000000000000000000000000000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv6[2].ipv6         : 0x00000000000000000000000000000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv6[2].netmask      : 0x00000000000000000000000000000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv6[3].ipv6         : 0x00000000000000000000000000000000
            MAD.GMP.VS.SwitchNetworkInfo.IPv6[3].netmask      : 0x00000000000000000000000000000000
        """
        host_obj.chdir(directory)
        with allure.step("Sending MAD to lid: {}".format(lid)):
            mad_output = host_obj.run_cmd(IpConsts.MAD_TO_GET_IP_TEMPLATE.format(lid=lid, card=hca),
                                          return_output=True)
        return mad_output
