from ngts.tests_nvos.general.security.constants import AaaConsts


class RestrictionsConsts:
    ENABLED = 'enabled'
    DISABLED = 'disabled'

    RESTRICTIONS = 'restrictions'

    FAIL_DELAY = 'fail-delay'
    LOCKOUT_STATE = 'lockout-state'
    LOCKOUT_ATTEMPTS = 'lockout-attempts'
    LOCKOUT_REATTEMPT = 'lockout-reattempt'

    FIELDS = [FAIL_DELAY, LOCKOUT_STATE, LOCKOUT_ATTEMPTS, LOCKOUT_REATTEMPT]

    FULL_VALID_VALUES = {
        FAIL_DELAY: list(range(0, 1000)),
        LOCKOUT_STATE: [ENABLED, DISABLED],
        LOCKOUT_ATTEMPTS: list(range(3, 10000)),
        LOCKOUT_REATTEMPT: list(range(0, 1000))
    }

    VALID_VALUES = {
        FAIL_DELAY: list(range(0, 90)),
        LOCKOUT_STATE: [ENABLED, DISABLED],
        LOCKOUT_ATTEMPTS: list(range(3, 15)),
        LOCKOUT_REATTEMPT: list(range(100, 180))
    }

    DEFAULT_VALUES = {
        FAIL_DELAY: 0,
        LOCKOUT_STATE: ENABLED,
        LOCKOUT_ATTEMPTS: 5,
        LOCKOUT_REATTEMPT: 15
    }

    TEST_ADMIN = {
        AaaConsts.USERNAME: 'test_admin',
        AaaConsts.PASSWORD: AaaConsts.STRONG_PASSWORD,
        AaaConsts.ROLE: AaaConsts.ADMIN
    }

    TEST_MONITOR = {
        AaaConsts.USERNAME: 'test_monitor',
        AaaConsts.PASSWORD: AaaConsts.STRONG_PASSWORD,
        AaaConsts.ROLE: AaaConsts.ADMIN
    }

    TEST_USERS = [TEST_ADMIN, TEST_MONITOR]

    MAX_EXPECT_TIMEOUT = 60
    PEXPECT_DELAY = 2
    ALLOWED_MARGIN = 4
    MAX_TIMEOUT = 360

    OPENAPI_AUH_ERROR = '401 Authorization Required'

    BAD_PASSWORD = 'asd'
