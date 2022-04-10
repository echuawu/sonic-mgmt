from ngts.cli_wrappers.nvue.nvue_ib_interface_clis import NvueIbInterfaceCli
from ngts.cli_wrappers.nvue.nvue_general_clis import NvueGeneralCli
from ngts.cli_wrappers.nvue.nvue_interface_show_clis import NvueInterfaceShowClis


class InternalNvosConsts:
    # Output dictionary
    OPERATIONAL_INDEX = 0
    APPLIED_INDEX = 1
    DEFAULT_TIMEOUT = 120   # in MS


class NvosConsts:
    LINK_STATE_UP = "up"
    LINK_STATE_DOWN = "down"


class ApiType:
    NVUE = "nvue"
    REST = "rest"
    NVUE_IB = 0
    REST_IB = 1
    NVUE_GENERAL = 3
    REST_GENERAL = 4
    NVUE_SHOW_CMDS = 5
    REST_SHOW_CMDS = 6


ApiObject = {ApiType.NVUE_IB: NvueIbInterfaceCli,
             ApiType.REST_IB: None,
             ApiType.NVUE_GENERAL: NvueGeneralCli,
             ApiType.REST_GENERAL: None,
             ApiType.NVUE_SHOW_CMDS: NvueInterfaceShowClis,
             ApiType.REST_SHOW_CMDS: None}


class IbInterfaceConsts:
    INTERFACE_NAME = "name"
    DESCRIPTION = "description"
    TYPE = "type"
    LINK = "link"
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
    LINK_SUPPORTED_SPEEDS = "supported-speed"
    LINK_SUPPORTED_LANES = "supported-lanes"
    LINK_LANES = "lanes"
    LINK_MAX_SUPPORTED_MTU = "max-supported-mtu"
    LINK_MTU = "mtu"
    LINK_VL_ADMIN_CAPABILITIES = "vl-capabilities"
    LINK_OPERATIONAL_VLS = "vl"
    LINK_IB_SUBNET = "ib-subnet"
    LINK_STATS = "stats"
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
    NAME = "name"
    IB_PORT_TYPE = "ib"
    LOOPBACK_PORT_TYPE = "loopback"
    ETH_PORT_TYPE = "eth"


class DataBaseNames:
    CONFIG_DB = "ConfigDb"
    STATE_DB = 'StateDb'
