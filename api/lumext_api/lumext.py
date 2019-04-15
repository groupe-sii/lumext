"""Thread based Worker to proceed messages from RabbitMQ.

This module defines the way to initialize LUMEXT application and to
handle "single message per thread" incoming from vCD9.X.
"""
# Standard imports
import base64
import logging
from threading import Thread
import binascii

# PIP imports
import simplejson as json

# Local imports
from .utils import list_get, configuration_manager as cm
from . import ldap_manager as lm

logger = logging.getLogger(__name__)


class MessageWorker(Thread):
    """Thread based Worker to proceed messages from RabbitMQ.
    """

    def __init__(self, message_worker: dict, data: str, message: str):
        """Initialize a new thread based Worker.

        A new worker is created for every message from the RabbitMQ queue.

        Request in the message is proceed through the main `proceed_message` function
        and the response is sent through `proceed_response`.

        Args:
            parent_worker (:obj): instance of object that manage the RabbitMQ.
            message (str):  message content as string.
            metadata (str):  message metadata as string.
        """
        Thread.__init__(self)
        self.parent_worker = message_worker
        self.request = data[0]
        self.metadata = data[1]
        self.uri = self.request['requestUri'].split('/api/org/')[1]
        try:
            if not self.uri.split('/')[1] == "lumext":
                self.proceed_response(
                    400, "Invalid application requested. Only managing LUMExt here."
                )
            self.org_id = self.uri.split('/')[0]
        except IndexError:
            self.proceed_response(400, f"Invalid URI for request: {self.uri}")
        self.method = self.request['method'].upper()
        self.query_str = self.request.get('queryString')
        self.user = self.metadata['user'].split("urn:vcloud:user:")[1]
        self.rights = self.metadata['rights']
        self.response_properties = {
            "id": self.request['id'],
            "Accept": self.request['headers'].get('Accept', None),
            "Content-Type": "application/*+json;version={cm().vcd.api_version}",
            "correlation_id": message.properties['correlation_id'],
            "reply_to": message.properties['reply_to'],
            "replyToExchange": message.headers['replyToExchange']
        }
        try:
            data = base64.b64decode(self.request['body'])
        except binascii.Error:
            self.proceed_response(400, "Invalid base64 content for request body")
        try:
            self.body = json.loads(data)
        except json.decoder.JSONDecodeError:
            if data: # only if not empty
                logger.warning(f"Invalid JSON content for request body: {str(data)}")
            self.body = {}
        self.object_type = None

    def proceed_message(self):
        """Handle all messages received on the RabbitMQ Exchange.
        """
        logger.info(f"Proceeding request message: {self.method} {self.uri}")
        self.object_type = list_get(self.uri.split('/'), 2)
        if not self.object_type:
            self.proceed_response(404, "No object type specified.")
        if self.object_type == "user":
            self.proceed_user_message()
        # elif self.object_type == "group":
        #     self.proceed_group_message()
        else:
            self.proceed_response(
                404, f"Invalid object type specified: {self.object_type}"
            )

    def proceed_user_message(self):
        """Handle message received about user request
        """
        login = list_get(self.uri.split('/'), 3)
        code = 200
        if self.method == "GET" and login:
            logger.debug(f"Proceeding request message to get a sepcific user: {login}")
            r = lm.get_user_in_ou(self.org_id, login, as_dict=True)
            if not r:
                r = "404: Not found"
        elif self.method == "GET":
            logger.debug(f"Proceeding request message to list users.")
            r = lm.list_users_in_ou(self.org_id, as_dict=True)
        elif self.method == "POST":
            logger.debug(f"Proceeding request message to create a user.")
            r = lm.add_user_in_ou(self.org_id, self.body)
        elif self.method == "PUT" and login:
            r = lm.edit_user_in_ou(self.org_id, login, self.body)
        elif self.method == "DELETE" and login:
            logger.debug(f"Proceeding request message to delete a sepcific user: {login}")
            r = lm.del_user_in_ou(self.org_id, login)
            if not r:
                r = "404: Not found"
        else:
            logger.warning(f"Invalid request: {self.method} {self.uri}")
            r = "405: Method Not Allowed"
        self.proceed_response(r, code)

    # def proceed_user_message(self):
    #     """Handle message received about group request
    #     """
    #     #TODO

    def run(self):
        """Redirect messages to `proceed_message`.
        """
        self.proceed_message()

    def proceed_response(self, body, code: int=200):
        """Respond to the initial request
        """
        try:
            # Parse error message to get HTTP code (ex: "404: Not found")
            if isinstance(body, str):
                code = int(body.split(':')[0].strip())
                body = body.split(':')[1].strip()
        except Exception as e:
            logger.critical(f"Cannot determine response code from body: {body}/{str(e)}.")
            code = 500
            body = "Server error in response parsing."
        # Send response
        self.response_properties['statusCode'] = code
        if code >= 400: # convert str to dict
            logger.error(body)
            body = { "error_message": body }
        logger.info(f"Sending response to the request: {self.method} {self.uri}")
        self.parent_worker.publish(
            json.dumps(body),
            self.response_properties
        )


def init():
    """Initialize logger.
    """
    logger.debug("Configuring loggers...")
    # disable tracebacks in kombu
    os.environ['DISABLE_TRACEBACKS'] = "1"
    # create trivia level
    add_log_level('trivia', 9)
    # create logger
    log_config = cm().log.config_path
    with open(log_config, "r", encoding="utf-8") as fd:
        logging.config.dictConfig(json.load(fd))
    return
