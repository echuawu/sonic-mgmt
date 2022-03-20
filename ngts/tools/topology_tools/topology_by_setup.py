from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name
from ngts.constants.constants import PlayeresAliases


def get_topology_by_setup_name_and_aliases(setup_name, slow_cli):
    topology = get_topology_by_setup_name(setup_name, slow_cli)

    return update_dut_alias(topology)


def update_dut_alias(topology):
    if 'dut' not in topology.players.keys():
        for alias in PlayeresAliases.Aliases_list:
            if alias in topology.players.keys():
                topology.players['dut'] = topology.players[alias]
                del topology.players[alias]
    return topology
