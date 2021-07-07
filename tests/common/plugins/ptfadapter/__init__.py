"""This module provides ptfadapter fixture to be used by tests to send/receive traffic via PTF ports"""
import os
import pytest

from ptfadapter import PtfTestAdapter
import ptf.testutils


DEFAULT_PTF_NN_PORT = 10900
DEFAULT_DEVICE_NUM = 0
ETH_PFX = 'eth'


def pytest_addoption(parser):
    parser.addoption("--keep_payload", action="store_true", default=False,
                     help="Keep the original packet payload, do not update payload to default pattern")


def override_ptf_functions():
    # Below code is to override the 'send' function in the ptf.testutils module. Purpose of this change is to insert
    # code for updating the packet pattern before send it out. Generally we want to make the payload part of injected
    # packet to have string of current test module and case name. While inspecting the captured packets, it is easier
    # to fiture out which packets are injected by which test case.
    def _send(test, port_id, pkt, count=1):
        update_payload = getattr(test, "update_payload", None)
        if update_payload and callable(update_payload):
            pkt = test.update_payload(pkt)

        return ptf.testutils.send_packet(test, port_id, pkt, count=count)
    setattr(ptf.testutils, "send", _send)


    # Below code is to override the 'dp_poll' function in the ptf.testutils module. This function is called by all
    # the other functions for receiving packets in the ptf.testutils module. Purpose of this overriding is to update
    # the payload of received packet using the same method to match the updated injected packets.
    def _dp_poll(test, device_number=0, port_number=None, timeout=-1, exp_pkt=None):
        update_payload = getattr(test, "update_payload", None)
        if update_payload and callable(update_payload):
            exp_pkt = test.update_payload(exp_pkt)

        result = test.dataplane.poll(
            device_number=device_number, port_number=port_number,
            timeout=timeout, exp_pkt=exp_pkt, filters=ptf.testutils.FILTERS
        )
        if isinstance(result, test.dataplane.PollSuccess):
            test.at_receive(result.packet, device_number=result.device, port_number=result.port)
        return result
    setattr(ptf.testutils, "dp_poll", _dp_poll)


def get_ifaces(netdev_output):
    """ parse /proc/net/dev content
    :param netdev_output: content of /proc/net/dev
    :return: interface names list
    """

    ifaces = []
    for line in netdev_output.split('\n'):
        # Skip a header
        if ':' not in line:
            continue

        iface = line.split(':')[0].strip()

        # Skip not FP interfaces
        if ETH_PFX not in iface:
            continue

        ifaces.append(iface)

    return ifaces


def get_ifaces_map(ifaces):
    """Get interface map."""
    sub_ifaces = []
    iface_map = {}
    for iface in ifaces:
        iface_suffix = iface.lstrip(ETH_PFX)
        if "." in iface_suffix:
            iface_index = int(iface_suffix.split(".")[0])
            sub_ifaces.append((iface_index, iface))
        else:
            iface_index = int(iface_suffix)
            iface_map[iface_index] = iface

    # override those interfaces that has sub interface
    for i, si in sub_ifaces:
        iface_map[i] = si
    return iface_map


@pytest.fixture(scope='module')
def ptfadapter(ptfhost, tbinfo, request):
    """return ptf test adapter object.
    The fixture is module scope, because usually there is not need to
    restart PTF nn agent and reinitialize data plane thread on every
    test class or test function/method. Session scope should also be Ok,
    however if something goes really wrong in one test module it is safer
    to restart PTF before proceeding running other test modules
    """

    # get the eth interfaces from PTF and initialize ifaces_map
    res = ptfhost.command('cat /proc/net/dev')
    ifaces = get_ifaces(res['stdout'])
    ifaces_map = get_ifaces_map(ifaces)

    # generate supervisor configuration for ptf_nn_agent
    ptfhost.host.options['variable_manager'].extra_vars.update({
        'device_num': DEFAULT_DEVICE_NUM,
        'ptf_nn_port': DEFAULT_PTF_NN_PORT,
        'ifaces_map': ifaces_map,
    })

    current_file_dir = os.path.dirname(os.path.realpath(__file__))

    ptfhost.template(src=os.path.join(current_file_dir, 'templates/ptf_nn_agent.conf.ptf.j2'),
                     dest='/etc/supervisor/conf.d/ptf_nn_agent.conf')

    # reread configuration and update supervisor
    ptfhost.command('supervisorctl reread')
    ptfhost.command('supervisorctl update')

    # Force a restart of ptf_nn_agent to ensure that it is in good status.
    ptfhost.command('supervisorctl restart ptf_nn_agent')

    with PtfTestAdapter(tbinfo['ptf_ip'], DEFAULT_PTF_NN_PORT, 0, ifaces_map.keys(), ptfhost) as adapter:
        if not request.config.option.keep_payload:
            override_ptf_functions()
            node_id = request.module.__name__
            adapter.payload_pattern = node_id + " "

        yield adapter
