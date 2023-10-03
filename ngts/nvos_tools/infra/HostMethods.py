import logging
import allure

from ngts.tools.test_utils.allure_utils import step as allure_step

logger = logging.getLogger()


class HostMethods:

    @staticmethod
    def host_snmp_get(host_engine, ip_address, community='qwerty12', port='', get_param='sysName.0'):
        with allure_step("Running snmpget command"):
            return host_engine.run_cmd('snmpget -v 2c -c {0} {1}{2} {3}'.format(community, ip_address, port, get_param))

    @staticmethod
    def host_snmp_walk(host_engine, ip_address, community='qwerty12', mib='', param=''):
        with allure_step("Running snmpwalk command"):
            return host_engine.run_cmd('snmpwalk -v 1 -c {0} {1} {2}'.format(community, ip_address, param))

    @staticmethod
    def host_ip_address_set(host_engine, ip_address, interface):
        with allure_step("Set ip address on host"):
            return host_engine.run_cmd('sudo ip addr add {0} dev {1}'.format(ip_address, interface))

    @staticmethod
    def host_ip_address_unset(host_engine, ip_address, interface):
        with allure_step("Unset ip address on host"):
            return host_engine.run_cmd('sudo ip addr del {0} dev {1}'.format(ip_address, interface))

    @staticmethod
    def host_ping(host_engine, ip_address, interface, count=5):
        with allure_step("Running ping from host"):
            return host_engine.run_cmd('ping -I {0} {1} -c {2}'.format(interface, ip_address, count))
