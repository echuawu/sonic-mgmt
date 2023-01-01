import pytest
import logging
from ngts.nvos_tools.infra.SonicMgmtContainer import SonicMgmtContainer
from ngts.nvos_constants.constants_nvos import NvosConst, SyslogConsts
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon

logger = logging.getLogger()
tmp_rsyslog_file = "/etc/rsyslog.conf.orig"


@pytest.fixture(scope='session', autouse=True)
def enable_rsyslog_on_sonic_mgmt_container(engines):
    """
    enable rsyslog on sonic-mgmt container
    """
    GeneralCliCommon(engines[NvosConst.SONIC_MGMT]).cp(SyslogConsts.RSYSLOG_CONF_FILE, tmp_rsyslog_file)
    SonicMgmtContainer.enable_rsyslog(engines[NvosConst.SONIC_MGMT], 'udp', True)

    yield

    GeneralCliCommon(engines[NvosConst.SONIC_MGMT]).cp(tmp_rsyslog_file, SyslogConsts.RSYSLOG_CONF_FILE)
    SonicMgmtContainer.restart_rsyslog(engines[NvosConst.SONIC_MGMT])
