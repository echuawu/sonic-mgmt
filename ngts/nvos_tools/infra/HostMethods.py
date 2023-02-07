import logging
import allure

logger = logging.getLogger()


class HostMethods:

    @staticmethod
    def host_snmp_get(host_engine, ip_address, community='qwerty12', port='', get_param='sysName.0'):
        with allure.step("Running snmpget command"):
            logging.info("Running snmpget command")
            return host_engine.run_cmd('snmpget -v 2c -c {community} {ip_address}{port} {get_param}'.format(community,
                                                                                                            ip_address,
                                                                                                            port,
                                                                                                            get_param))

    @staticmethod
    def host_snmp_walk(host_engine, ip_address, community='qwerty12', param=''):
        with allure.step("Running snmpwalk command"):
            logging.info("Running snmpwalk command")
            return host_engine.run_cmd('snmpwalk -v 1 -c {0} {1} {2}'.format(community, ip_address, param))
