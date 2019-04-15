#!/usr/bin/env python
"""Entry point for LUMExt application.

Run this script as a daemon (or in console mode for debug).
"""
# Standard imports
import logging, logging.config
import signal
import os
import ssl

# PIP imports
from vcdextmessageworker import Connection, MessageWorker
import simplejson as json

# Local imports
from .utils import signal_handler, configuration_manager as cm, add_log_level, validate_configuration_path

logger = logging.getLogger(__name__)


def logger_init():
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


def main():
    """Execute the API worker.
    """
    validate_configuration_path("LUMEXT_CONFIGURATION_FILE_PATH")
    logger_init()

    # Catch interruption signal to leave quietly
    signal.signal(signal.SIGINT, signal_handler)
    logger.info("Starting API server")

    # Start AMQP connection
    rmq_conf = cm().rabbitmq
    amqp_url = f"amqp://{rmq_conf.user}:{rmq_conf.password}"
    amqp_url += f"@{rmq_conf.server}:{rmq_conf.port}/%2F"
    if rmq_conf.use_ssl:
        amqp_url += "?ssl=1"
    with Connection(amqp_url, heartbeat=4) as conn:
        MessageWorker(
            conn,
            exchange=rmq_conf.exchange,
            queue=rmq_conf.queue,
            routing_key=rmq_conf.routing_key,
            sub_worker="lumext_api.lumext.MessageWorker",
            thread_support=True).run()


if __name__ == '__main__':
    main()
