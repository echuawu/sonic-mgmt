import copy


class UserInfo:
    def __init__(self, username, password, role):
        assert isinstance(username, str) and isinstance(password, str) \
            and role in ['admin', 'monitor'], 'Invalid argument'
        self.username = username
        self.password = password
        self.role = role

    def copy(self, deep=False):
        if deep:
            return copy.deepcopy(self)
        else:
            return copy.copy(self)
