from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name
from ngts.constants.constants import PlayeresAliases


def get_topology_by_setup_name_and_aliases(setup_name, slow_cli):
    topology = get_topology_by_setup_name(setup_name, slow_cli)

    return update_dut_alias(topology)


def update_dut_alias(topology):
    if 'dut' not in topology.players.keys():
        # For the lower tor in dual-tor topology, the key of dut name got from noga is 'dut-b'
        # If the topology only has key 'dut-b' without key 'dut', means it is deployed as a normal setup
        # Change the 'dut-b' to 'dut' in this case
        if 'dut-b' in topology.players.keys():
            topology.players['dut'] = topology.players.pop('dut-b')
            topology.players['dut_serial'] = topology.players.pop('dut-b_serial')
            topology.players['dut']['attributes'].noga_query_data['attributes']['Common']['Description'] = 'dut'
        for alias in PlayeresAliases.Aliases_list:
            if alias in topology.players.keys():
                topology.players['dut'] = topology.players[alias]
                del topology.players[alias]
    return topology
