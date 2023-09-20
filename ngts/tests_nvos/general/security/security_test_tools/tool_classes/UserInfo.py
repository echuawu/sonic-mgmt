from ngts.tests_nvos.general.security.security_test_tools.constants import AaaConsts


class UserInfo:
    def __init__(self, username, password, role):
        assert isinstance(username, str) and isinstance(password, str) \
            and role in [AaaConsts.ADMIN, AaaConsts.MONITOR], f'Invalid argument'
        self.username = username
        self.password = password
        self.role = role
