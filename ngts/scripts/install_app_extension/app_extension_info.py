
class AppExtensionInfo():
    def __init__(self, app_name, app_info=None):
        self.app_name = app_name
        self.sdk_version = None
        if app_info is not None:
            self.repository = self._get_repository_url(app_info)
            self.version = self._get_version(app_info)
        else:
            # TODO implement self.get_latest_app_ext_for_this_image()
            pass

    def get_latest_app_ext_for_this_image(self):
        raise NotImplementedError('This logic is not implemented yet')

    @staticmethod
    def _get_repository_url(app_url_version):
        url_position_index = 0
        return app_url_version.split(':')[url_position_index]

    @staticmethod
    def _get_version(app_url_version):
        version_position_index = 1
        return app_url_version.split(':')[version_position_index]

    def set_sdk_version(self, sdk_version):
        self.sdk_version = sdk_version
