#!/usr/bin/env python

import logging

logger = logging.getLogger()


# key - package, value - install set of: 0 - detect cmd, 1 - detect output, 2 - list of install cmds
PACKAGES_DICT = {"natsort": ("pip2 show natsort",
                             "/usr/local/lib/python2.7/dist-packages",
                             ['sudo curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py',
                              'sudo python get-pip.py',
                              'sudo pip2 install natsort']),
                 "ipaddr": ("pip2 show ipaddr",
                            "/usr/local/lib/python2.7/dist-packages",
                            ['sudo curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py',
                             'sudo python get-pip.py',
                             'sudo pip2 install ipaddr']),
                 "lxml": ("pip2 show lxml",
                          "/usr/local/lib/python2.7/dist-packages",
                          ['sudo curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py',
                           'sudo python get-pip.py',
                           'sudo pip2 install lxml'])
                 }


def test_extend_python_packages(topology_obj):
    """
    This function will check and install missed python packages.
    :param topology_obj: topology object fixture
    """
    detect_cmd_index = 0
    detect_output_index = 1
    install_cmd_set_index = 2
    install_cmd_index = 2
    pip_updated = False

    dut_engine = topology_obj.players['dut']['engine']
    dut_engine.run_cmd('sudo config bgp shutdown all')

    try:
        for pkg, install_set in PACKAGES_DICT.items():
            if required_instalation(dut_engine, install_set[detect_cmd_index], install_set[detect_output_index]):
                logger.info("Install {} package on dut".format(pkg))
                if not pip_updated:
                    dut_engine.run_cmd_set(install_set[install_cmd_set_index])
                    pip_updated = True
                else:
                    dut_engine.run_cmd(install_set[install_cmd_set_index][install_cmd_index])
    except Exception as e:
        logger.error("Not all required packages were installed.\n{}".format(e))

    finally:
        dut_engine.run_cmd('sudo config bgp startup all')


def required_instalation(dut_engine, detect_cmd, detect_output):
    output = dut_engine.run_cmd(detect_cmd)
    if detect_output not in output:
        return True
    return False
