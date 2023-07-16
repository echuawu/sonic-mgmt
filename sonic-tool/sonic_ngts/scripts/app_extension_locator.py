#!/usr/bin/python3

import json
import os
import sys

import requests
import argparse

requests.urllib3.disable_warnings()


class AppSdk:
    def __init__(self, app_extension_version, app_extension_sdk):
        self.app_extension = app_extension_version
        self.sdk = app_extension_sdk

    def __str__(self):
        return json.dumps(self.__dict__)


def _send_aql_request_to_artifactory(data):
    auth_token = os.environ.get('ARTIFACTORY_TOKEN')

    if auth_token is None:
        sys.exit('Please provide API key to the JFrog Artifactory. Set to Environment Variable - ARTIFACTORY_TOKEN')

    headers = {
        'Content-Type': 'text/plain',
    }

    response = requests.post(
        'https://urm.nvidia.com/artifactory/api/search/aql',
        headers=headers,
        data=data,
        verify=False,
        auth=('', auth_token),
    )

    if response.status_code != requests.codes.ok:
        sys.exit(f'Failed to retrieve labels from server - {response}: {response.content}')

    return json.loads(response.content)


def _send_rest_query_artifacts_with_matching_sdk(sdk, app_extension='sonic-wjh'):
    find_query = {
        "repo": "sw-nbu-sws-sonic-docker-local",
        "path": {"$match": f"{app_extension}*"},
        "name": {"$eq": "manifest.json"},
        "@docker.label.nvidia-sdk": {"$match": sdk}
    }

    data = f'items.find({json.dumps(find_query)}).include("@docker.label.nvidia-sdk")'

    content = _send_aql_request_to_artifactory(data)
    return content['results']


def find_artifacts_with_matching_sdk(sdk, app_extension='sonic-wjh'):
    artifactory_response = _send_rest_query_artifacts_with_matching_sdk(sdk, app_extension)

    artifacts_list = []
    for res in artifactory_response:
        artifacts_list.append(AppSdk(res['path'], res['properties'][0]['value']))

    return artifacts_list


def get_sdk_from_version(app_version, app_extension='sonic-wjh'):
    find_query = {
        "repo": "sw-nbu-sws-sonic-docker-local",
        "path": {"$match": f"{app_extension}/{app_version}"},
        "name": {"$eq": "manifest.json"}
    }

    data = f'items.find({json.dumps(find_query)}).include("@docker.label.nvidia-sdk")'
    content = _send_aql_request_to_artifactory(data)
    return AppSdk(f'{app_extension}/{app_version}', content['results'][0]['properties'][0]['value']) if \
        content['range']['total'] > 0 else None


if __name__ == '__main__':
    server = 'sw-nbu-sws-sonic-docker-local'

    parser = argparse.ArgumentParser(description='')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-s', '--sdk', help='Find App Extensions with a matching SDK', required=False)
    group.add_argument('-v', '--app_ext_version', help='Find SDK of a given App Extensions Version', required=False)
    parser.add_argument('-a', '--app', help='Which App Extensions to search', required=False, default='sonic-wjh')
    parser.add_argument('-j', '--json', action="store_true", help='Output as Json')

    args = vars(parser.parse_args())

    sdk = args['sdk']
    return_results_as_json = args['json']
    version = args['app_ext_version']
    app_extension = args['app']

    if sdk is not None:
        if not return_results_as_json:
            print(f'Searching for versions of {app_extension} with SDK {sdk}')
        matching_artifacts = find_artifacts_with_matching_sdk(sdk, app_extension)

        if not return_results_as_json:
            for res in matching_artifacts:
                print(f"Found SDK {res.sdk} in {res.app_extension}")
            if not matching_artifacts:
                print('Found No matching versions.')
        else:
            print(json.dumps(matching_artifacts, default=lambda x: x.__dict__))

    if version is not None:
        matching_artifact = get_sdk_from_version(version, app_extension)
        if not return_results_as_json:
            if matching_artifact:
                print(f'SDK on version {version} of {app_extension}:\n{matching_artifact.sdk}')
            else:
                print(f'Version {version} was not found')
        else:
            print(matching_artifact)
