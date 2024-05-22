from dataclasses import dataclass


@dataclass
class SonicMarsData:
    def __init__(self):
        session_id: 0
        setup_name: ''
        mars_key_id: ''
        name: ''
        result: ''
        allure_url: ''
        skip_reason: ''
        exception: ''
        exception_regex: ''
        la_redmine_issues: []
        dump_info: ''
        test_inserted_time: ''
