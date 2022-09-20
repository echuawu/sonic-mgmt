
class InternalNvosConsts:
    # Output dictionary
    OPERATIONAL_INDEX = 0
    APPLIED_INDEX = 1
    DEFAULT_TIMEOUT = 120   # in MS
    IB_TRAFFIC_SENDER_INTERFACE = "h1p1"
    IB_TRAFFIC_RECEIVER_INTERFACE = "h2p1"
    IB_TRAFFIC_LAT_TYPE = "ib_send_lat"
    IB_TRAFFIC_IPOIB_TYPE = "ping_over_ib"


class NvosConsts:
    LINK_STATE_UP = "up"
    LINK_STATE_DOWN = "down"
    LINK_LOG_STATE_ACTIVE = 'Active'


class IbInterfaceConsts:
    INTERFACE_NAME = "name"
    DESCRIPTION = "description"
    DHCP_STATE = 'state'
    DHCP_SET_HOSTNAME = 'set-hostname'
    TYPE = "type"
    LINK = "link"
    IP = "ip"
    IFINDEX = "ifindex"
    PLUGGABLE = "pluggable"
    PLUGGABLE_IDENTIFIER = "identifier"
    PLUGGABLE_CABLE_LENGTH = "cable-length"
    PLUGGABLE_VENDOR_NAME = "vendor-name"
    PLUGGABLE_VENDOR_PN = "vendor-pn"
    PLUGGABLE_VENDOR_REV = "vendor-rev"
    PLUGGABLE_VENDOR_SN = "vendor-sn"
    LINK_LOGICAL_PORT_STATE = "logical-state"
    LINK_PHYSICAL_PORT_STATE = "physical-state"
    LINK_STATE = "state"
    LINK_BREAKOUT = "breakout"
    LINK_IB_SPEED = "ib-speed"
    LINK_SUPPORTED_IB_SPEEDS = "supported-ib-speed"
    LINK_SPEED = "speed"
    LINK_MAC = "mac"
    LINK_DUPLEX = "duplex"
    LINK_AUTO_NEGOTIATE = "auto-negotiate"
    LINK_SUPPORTED_SPEEDS = "supported-speed"
    LINK_SUPPORTED_LANES = "supported-lanes"
    LINK_LANES = "lanes"
    LINK_MAX_SUPPORTED_MTU = "max-supported-mtu"
    LINK_MTU = "mtu"
    LINK_VL_ADMIN_CAPABILITIES = "vl-capabilities"
    LINK_OPERATIONAL_VLS = "op-vls"
    LINK_IB_SUBNET = "ib-subnet"
    LINK_STATS = "stats"
    LINK_STATS_CARRIER_TRANSITION = "carrier-transitions"
    LINK_STATS_IN_BYTES = "in-bytes"
    LINK_STATS_IN_DROPS = "in-drops"
    LINK_STATS_IN_ERRORS = "in-errors"
    LINK_STATS_IN_SYMBOL_ERRORS = "in-symbol-errors"
    LINK_STATS_IN_PKTS = "in-pkts"
    LINK_STATS_OUT_BYTES = "out-bytes"
    LINK_STATS_OUT_DROPS = "out-drops"
    LINK_STATS_OUT_ERRORS = "out-errors"
    LINK_STATS_OUT_PKTS = "out-pkts"
    LINK_STATS_OUT_WAIT = "out-wait"
    IP_VRF = "vrf"
    IP_ADDRESS = "address"
    IP_GATEWAY = "gateway"
    IP_DHCP = "dhcp-client"
    IP_DHCP6 = "dhcp-client6"
    NAME = "name"
    IB_PORT_TYPE = "ib"
    LOOPBACK_PORT_TYPE = "loopback"
    ETH_PORT_TYPE = "eth"
    MTU_VALUES = [256, 512, 1024, 2048, 4096]
    DEFAULT_MTU = 4096
    SPEED_LIST = {'xdr': '800G', 'ndr': '400G', 'hdr': '200G', 'edr': '100G', 'fdr': '56G', 'qdr': '40G', 'sdr': '10G'}
    SUPPORTED_LANES = ['1X', '1X,2X', '1X,4X', '1X,2X,4X']
    DEFAULT_LANES = '1X,2X,4X'
    SUPPORTED_VLS = ['VL0', 'VL0-VL1', 'VL0-VL3', 'VL0-VL7']
    DEFAULT_VLS = 'VL0-VL7'


class DataBaseNames:
    CONFIG_DB = "ConfigDb"
    STATE_DB = 'StateDb'
