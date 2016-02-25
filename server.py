from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
import socket
import logging

logger = logging.getLogger(__name__)

HTML = b'''
<!DOCTYPE html>
<html>
<body>
Done. Please close this window.
<script type="text/javascript">
function extractFromHash(name, hash) {
    var match = hash.match(new RegExp(name + "=([^&]+)"));
    return !!match && match[1];
}

var hash = window.location.hash;
var token = extractFromHash("access_token", hash);

if (token){
    var redirect = window.location.origin.concat('/?', window.location.hash.substr(1));
    window.location = redirect;
}
else {
    console.log("do nothing");
}
</script>
</body>
</html>
'''

# https://github.com/fuzzysteve/CREST-Market-Downloader/
class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/favicon.ico":
            return
        parsed_path = parse.urlparse(self.path)
        parts = parse.parse_qs(parsed_path.query)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(HTML)

        self.server.callback(self.server, parts)

    def log_message(self, format, *args):
        return

# http://code.activestate.com/recipes/425210-simple-stoppable-server-using-socket-timeout/
class StoppableHTTPServer(HTTPServer):

    def server_bind(self):
        HTTPServer.server_bind(self)

        # Allow listening for x seconds
        sec = 60
        logger.debug("Running server for %d seconds", sec)

        self.socket.settimeout(0.5)
        self.max_tries = sec / self.socket.gettimeout()
        self.tries = 0
        self.run = True

    def get_request(self):
        while self.run:
            try:
                sock, addr = self.socket.accept()
                sock.settimeout(None)
                return (sock, addr)
            except socket.timeout:
                pass

    def stop(self):
        self.run = False

    def handle_timeout(self):
        #logger.debug("Number of tries: %d"%self.tries)
        self.tries += 1
        if self.tries == self.max_tries:
            logger.debug("Server timed out waiting for connection")
            self.stop()

    def serve(self, callback):
        self.callback = callback
        while self.run:
            try:
                self.handle_request()
            except TypeError:
                pass
        self.server_close()

