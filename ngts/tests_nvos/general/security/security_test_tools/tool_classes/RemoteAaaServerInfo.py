import copy
from typing import List

from ngts.tests_nvos.general.security.security_test_tools.tool_classes.UserInfo import UserInfo


class RemoteAaaServerInfo:
    def __init__(self, hostname, priority, secret, port, timeout, users: List[UserInfo]):
        self.hostname = hostname
        self.priority = priority
        self.secret = secret
        self.port = port
        self.timeout = timeout
        self.users = users

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        else:
            return copy.copy(self)


class TacacsServerInfo(RemoteAaaServerInfo):
    def __init__(self, hostname, priority, secret, port, timeout, auth_type, users: List[UserInfo]):
        super().__init__(hostname, priority, secret, port, timeout, users)
        # self.retransmit = retransmit
        self.auth_type = auth_type


class LdapServerInfo(RemoteAaaServerInfo):
    pass  # will implement later
