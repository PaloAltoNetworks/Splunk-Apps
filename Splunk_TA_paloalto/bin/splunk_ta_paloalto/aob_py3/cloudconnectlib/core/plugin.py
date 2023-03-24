#
# Copyright 2021 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import importlib
import sys
import traceback
from os import path as op
from os import walk

from ..common import log
from .ext import _extension_functions

logger = log.get_cc_logger()


def cce_pipeline_plugin(func):
    """
    Decorator for pipeline plugin functions.

    This docorator helps to register user defined pipeline function into CCE
    engine so that it could be looked up when executing jobs.

    :param func: User defined function object
    :type func: ``function``

    Usage::
        >>> @cce_pipeline_plugin
        >>> def my_function(arg):
        >>>     do_work()
    """
    if not callable(func):
        logger.debug(
            "Function %s is not callable, don't add it as a pipeline function",
            func.__name__,
        )
    else:
        if func.__name__ in list(_extension_functions.keys()):
            logger.warning(
                "Pipeline function %s already exists, please rename it!",
                func.__name__,
            )
        else:
            _extension_functions[func.__name__] = func
            logger.debug("Added function %s to pipeline plugin system", func.__name__)

    def pipeline_func(*args, **kwargs):
        return func(*args, **kwargs)

    return pipeline_func


def import_plugin_file(file_name):
    """
    Import a module.
    1. If the module with the same name already in sys.modules, then log a
    warning and exit without reloading it.
    2. If failed to import the file, then log a warning and exit
    """
    if file_name.endswith(".py"):
        module_name = file_name[:-3]
    else:
        logger.warning(
            "Plugin file %s is with unsupported extension, the supported are py",
            file_name,
        )
        return

    if module_name in list(sys.modules.keys()):
        logger.debug(
            "Module %s already exists and it won't be reload, "
            "please rename your plugin module if it is required.",
            module_name,
        )
        return

    try:
        importlib.import_module(module_name)
    except Exception:
        logger.warning(f"Failed to load module {module_name}, {traceback.format_exc()}")
        return

    logger.info("Module %s is imported", module_name)
    return


def init_pipeline_plugins(plugin_dir):
    """
    Initialize the pipeline plugins which triggers the auto registering of user
    defined pipeline functions.
    1. Add the plugin_dir into sys.path.
    2. Import the file under plugin_dir that starts with "cce_plugin_" and ends
    with ".py"
    """
    if not op.isdir(plugin_dir):
        logger.warning(
            "%s is not a directory! Pipeline plugin files won't be loaded.", plugin_dir
        )
        return

    if plugin_dir not in sys.path:
        sys.path.append(plugin_dir)

    for file_name in next(walk(plugin_dir))[2]:
        if file_name == "__init__.py" or not file_name.startswith("cce_plugin_"):
            continue
        if file_name.endswith(".py"):
            import_plugin_file(file_name)
