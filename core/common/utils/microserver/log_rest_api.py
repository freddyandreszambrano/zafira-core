import json
import logging
import re
import time
from datetime import datetime

from ua_parser import user_agent_parser

logger = logging.getLogger("zafira")


def mobile(request):
    """Return True if the request comes from a mobile device."""

    MOBILE_AGENT_RE = re.compile(r".*(iphone|mobile|androidtouch)", re.IGNORECASE)

    if MOBILE_AGENT_RE.match(request.META.get("HTTP_USER_AGENT", "")):
        return True
    else:
        return False


def get_client_ip(django_request):
    x_forwarded_for = django_request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = django_request.META.get("REMOTE_ADDR")
    return ip


class ZafiraLogging:
    def __init__(self, request, status=200, message=""):
        self.request = request
        self.status = status
        self.message = message
        self.data = ""
        self.device = user_agent_parser.Parse(request.META.get("HTTP_USER_AGENT", ""))
        self.source = "mobile" if mobile(request) else "web"

    def make_dict(self):
        dictionary_helper = dict()
        dictionary_helper["status"] = self.status
        dictionary_helper["message"] = self.message
        dictionary_helper["data"] = self.message
        dictionary_helper["ip"] = get_client_ip(self.request)
        dictionary_helper["app_version"] = self.request.META.get("HTTP_APP_VERSION", None)
        dictionary_helper["app_source"] = self.request.META.get("HTTP_APP_SOURCE", None)
        dictionary_helper["user"] = (
            self.request.user.__repr__() if self.request.user.is_authenticated else "Anonymous"
        )
        dictionary_helper["time"] = "{0}".format(datetime.now().strftime("%Y/%m/%d %H:%M:%S %Z"))
        dictionary_helper["timestamp"] = time.time()
        dictionary_helper["url"] = self.request.get_full_path()
        dictionary_helper["method"] = self.request.method
        dictionary_helper["source"] = self.source
        dictionary_helper["device"] = self.device["device"]
        dictionary_helper["os"] = self.device["os"]
        dictionary_helper["body"] = self.request.data
        dictionary_helper["query_params"] = self.request.query_params
        dictionary_helper["files"] = self.request.FILES
        return dictionary_helper

    def log_info(self):
        dictionary_helper = self.make_dict()
        return dictionary_helper

    def print(self, data=None):
        if data is None:
            dictionary_helper = self.make_dict()
            logger.info(dictionary_helper)
        else:
            logger.info(json.dumps(data))

    def change_status(self, status):
        self.status = status

    def change_message(self, message):
        self.message = message

    def set_data(self, data):
        self.data = data
