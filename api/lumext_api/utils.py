"""Some helping functions.
"""
# Standard imports
import logging
import signal
import sys
import os

# PIP imports
import simplejson as json
from python_json_config import ConfigBuilder

logger = logging.getLogger(__name__)


def signal_handler(signal, frame):
    """Handle a Keyboard Interrupt to leave rabbitMQ connection.
    """
    sys.stdout.write('\b\b\r')  # hide the ^C
    logger.info("SIGINT signal catched -> Exiting...")
    sys.exit(0)


def add_log_level(level_name, level_value, method_name=None):
    """Add a new logging level.

    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    Arguments:
        level_name (str): becomes an attribute of the `logging` module
        level_value (int): value associated to the new log level
        method_name (str, optionnal): becomes a convenience method for both `logging`
            itself and the class returned by `logging.getLoggerClass()` (usually just
            `logging.Logger`). If `method_name` is not specified, `level_name.lower()` is
            used. (Defaults to ``None``)

    Raises:
        AttributeError: To avoid accidental clobberings of existing attributes, this
            method will raise an `AttributeError` if the level name is already an attribute of
            the `logging` module or if the method name is already present.
    """
    if not method_name:
        method_name = level_name.lower()
    if hasattr(logging, level_name):
        raise AttributeError(
            f"{level_name} is already defined in logging module")
    if hasattr(logging, level_name.upper()):
        raise AttributeError(
            f"{level_name.upper()} is already defined in logging module")
    if hasattr(logging, method_name):
        raise AttributeError(
            f"{method_name} is already defined in logging module")
    if hasattr(logging.getLoggerClass(), method_name):
        raise AttributeError(
            f"{method_name} is already defined in logger class")

    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(level_value):
            self._log(level_value, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(level_value, message, *args, **kwargs)

    logging.addLevelName(level_value, level_name)
    logging.addLevelName(level_value, level_name.upper())  # ALIAS
    setattr(logging, level_name, level_value)
    setattr(logging.getLoggerClass(), method_name, log_for_level)
    setattr(logging, method_name, log_to_root)


def validate_configuration_path(env):
    """Validate that a configuration path is set and valid.

    Args:
        env (str): Name of the environment variable.
    """
    config_path = os.environ.get(env)
    if not config_path:
        print(f"""Missing environment variable `{env}`.

Please:
1. copy the `config.sample.json` file to a new location.
2. Configure the copy with your settings.
3. Export the environment variable `{env}`

Ex:
```
mkdir -p /opt/lumext/etc
cp config.sample.json /opt/sii/lumext/etc/config.json
export {env}=/opt/sii/lumext/etc/config.json
```
        """)
        sys.exit(-1)
    # Test if path is a valid file
    if not os.path.isfile(config_path):
        print(f"""Invalid path for configuration file: {config_path}

Please check that environment variable `{env}` is
correctly setted.
        """)
        sys.exit(-1)
    with open(config_path) as json_config:
        try:
            json.load(json_config)
        except json.errors.JSONDecodeError:
            print(f"""Invalid syntax in configuration file: {config_path}

Please check that the content of the configuration file is a
valid JSON document.
        """)
            sys.exit(-1)
    return


def configuration_manager():
    """Read configuration file.

    Returns:
        A configuration object to get members when needed in code.
    """
    # Read config path from rnv settings.
    config_path = os.environ.get("LUMEXT_CONFIGURATION_FILE_PATH")
    # create config parser
    builder = ConfigBuilder()
    # parse config
    return builder.parse_config(config_path)


def list_get(arr: list, index: int, default: any = None):
    """Get a item of list. If IndexError, returns default value.

    Arguments:
        arr (list): An array object
        index (int): An index for array lookup
        default (any, optional): A default value to return in case of IndexError
            (Defaults to ``None``)

    Returns:
        any: The value to return (could be the default one)
    """
    if arr == None:
        return default
    try:
        return arr[index]
    except IndexError:
        return default