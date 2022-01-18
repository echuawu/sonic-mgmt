import shutil
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class ImageHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    @summary: HTTP request handler class, for serving SONiC image files over HTTP.
    """
    served_files = {}

    def do_GET(self):
        """
        @summary: Handling HTTP GET requests.
        """
        if self.path == "/favicon.ico":
            self.send_error(404, "No /favicon.ico")
            return None

        if self.path not in self.served_files.keys():
            self.send_error(404, "Requested URL is not found")
            return None

        f = self.send_head(self.path)
        if f:
            shutil.copyfileobj(f, self.wfile)
            f.close()

    def send_head(self, request_path):
        """
        @summary: Send HTTP header
        @param request_path: Path of the HTTP Request
        """
        served_file = self.served_files[request_path]
        if not os.path.isfile(served_file):
            self.send_error(404, "File %s not found for /%s" % (served_file, request_path))
            return None

        try:
            f = open(served_file, "rb")
        except IOError:
            self.send_error(404, "Read file %s failed" % served_file)
            return None
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.end_headers()
        return f
