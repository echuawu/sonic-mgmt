VLAN_SUB_INTERFACE_SEPARATOR = "."
# default port mapping mode for storage backend testbeds
PTF_PORT_MAPPING_MODE_DEFAULT = "use_sub_interface"
TOPO_KEY = "topo"
NAME_KEY = "name"
# field in mg_facts to flag whether it's a backend topology or not
IS_BACKEND_TOPOLOGY_KEY = "is_backend_topology"
# a topology whos name contains the indicator 'backend' will be considered as a backend topology
BACKEND_TOPOLOGY_IND = "backend"
# ssh connect default username and password
DEFAULT_SSH_CONNECT_PARAMS = {
    "public": {"username": "admin",
               "password": "YourPaSsWoRd"}
}
# resolv.conf expected nameservers
RESOLV_CONF_NAMESERVERS = {
    "public": ["10.211.0.124", "10.211.0.121", "10.7.77.135"]
}
KVM_PLATFORM = 'x86_64-kvm_x86_64-r0'
