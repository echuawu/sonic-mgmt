from ngts.tools.infra import update_sys_path_by_community_plugins_path

update_sys_path_by_community_plugins_path()

from plugins.loganalyzer_dynamic_errors_ignore.la_dynamic_errors_ignore import \
    pytest_runtest_setup, pytest_runtest_teardown  # noqa: E402
