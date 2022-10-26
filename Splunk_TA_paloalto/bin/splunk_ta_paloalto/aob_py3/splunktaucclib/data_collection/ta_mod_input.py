#!/usr/bin/python

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

"""
This is the main entry point for My TA
"""

import os.path as op
import sys
import time

import splunktalib.common.util as utils
import splunktalib.file_monitor as fm
import splunktalib.modinput as modinput
import splunktalib.orphan_process_monitor as opm

import splunktaucclib.common.log as stulog
from splunktaucclib.common import load_schema_file as ld
from splunktaucclib.data_collection import ta_checkpoint_manager as cpmgr
from splunktaucclib.data_collection import ta_config as tc
from splunktaucclib.data_collection import ta_data_client as tdc
from splunktaucclib.data_collection import ta_data_loader as dl

utils.remove_http_proxy_env_vars()


def do_scheme(ta_short_name, ta_name, schema_para_list=None, single_instance=True):
    """
    Feed splunkd the TA's scheme

    """
    param_str = ""
    builtsin_names = {"name", "index", "sourcetype", "host", "source", "disabled"}

    schema_para_list = schema_para_list or ()
    for param in schema_para_list:
        if param in builtsin_names:
            continue
        param_str += """<arg name="{param}">
          <title>{param}</title>
          <required_on_create>0</required_on_create>
          <required_on_edit>0</required_on_edit>
        </arg>""".format(
            param=param
        )

    print(
        """
    <scheme>
    <title>Splunk Add-on for {ta_short_name}</title>
    <description>Enable data inputs for {ta_name}</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>xml</streaming_mode>
    <use_single_instance>{}</use_single_instance>
    <endpoint>
      <args>
        <arg name="name">
          <title>{ta_name} Data Input Name</title>
        </arg>
        {param_str}
      </args>
    </endpoint>
    </scheme>
    """.format(
            (str(single_instance)).lower(),
            ta_short_name=ta_short_name,
            ta_name=ta_name,
            param_str=param_str,
        )
    )


def _setup_signal_handler(data_loader, ta_short_name):
    """
    Setup signal handlers
    :data_loader: data_loader.DataLoader instance
    """

    def _handle_exit(signum, frame):
        stulog.logger.info(f"{ta_short_name} receives exit signal")
        if data_loader is not None:
            data_loader.tear_down()

    utils.handle_tear_down_signals(_handle_exit)


def _handle_file_changes(data_loader):
    """
    :reload conf files and exit
    """

    def _handle_refresh(changed_files):
        stulog.logger.info(f"Detect {changed_files} changed, reboot itself")
        data_loader.tear_down()

    return _handle_refresh


def _get_conf_files(local_file_list):
    cur_dir = op.dirname(op.dirname(op.dirname(op.dirname(op.abspath(__file__)))))
    files = []
    for f in local_file_list:
        files.append(op.join(cur_dir, "local", f))
    return files


def run(collector_cls, settings, checkpoint_cls=None, config_cls=None, log_suffix=None):
    """
    Main loop. Run this TA forever
    """
    # This is for stdout flush
    utils.disable_stdout_buffer()

    # http://bugs.python.org/issue7980
    time.strptime("2016-01-01", "%Y-%m-%d")

    tconfig = tc.create_ta_config(settings, config_cls or tc.TaConfig, log_suffix)
    stulog.set_log_level(tconfig.get_log_level())
    task_configs = tconfig.get_task_configs()

    if not task_configs:
        stulog.logger.debug("No task and exiting...")
        return
    meta_config = tconfig.get_meta_config()

    if tconfig.is_shc_but_not_captain():
        # In SHC env, only captain is able to collect data
        stulog.logger.debug("This search header is not captain, will exit.")
        return

    loader = dl.create_data_loader(meta_config)

    jobs = [
        tdc.create_data_collector(
            loader,
            tconfig,
            meta_config,
            task_config,
            collector_cls,
            checkpoint_cls=checkpoint_cls or cpmgr.TACheckPointMgr,
        )
        for task_config in task_configs
    ]

    # handle signal
    _setup_signal_handler(loader, settings["basic"]["title"])

    # monitor files to reboot
    if settings["basic"].get("monitor_file"):
        monitor = fm.FileMonitor(
            _handle_file_changes(loader),
            _get_conf_files(settings["basic"]["monitor_file"]),
        )
        loader.add_timer(monitor.check_changes, time.time(), 10)

    # add orphan process handling, which will check each 1 second
    orphan_checker = opm.OrphanProcessChecker(loader.tear_down)
    loader.add_timer(orphan_checker.check_orphan, time.time(), 1)

    loader.run(jobs)


def validate_config():
    """
    Validate inputs.conf
    """

    _, configs = modinput.get_modinput_configs_from_stdin()
    return 0


def usage():
    """
    Print usage of this binary
    """

    hlp = "%s --scheme|--validate-arguments|-h"
    print(hlp % sys.argv[0], file=sys.stderr)
    sys.exit(1)


def main(
    collector_cls,
    schema_file_path,
    log_suffix="modinput",
    checkpoint_cls=None,
    configer_cls=None,
    schema_para_list=None,
    single_instance=True,
):
    """
    Main entry point
    """
    assert collector_cls, "ucc modinput collector is None."
    assert schema_file_path, "ucc modinput schema file is None"

    stulog.reset_logger(log_suffix)
    settings = ld(schema_file_path)
    ta_short_name = settings["basic"]["title"]
    ta_desc = settings["basic"]["description"]

    args = sys.argv
    if len(args) > 1:
        if args[1] == "--scheme":
            do_scheme(ta_short_name, ta_desc, schema_para_list, single_instance)
        elif args[1] == "--validate-arguments":
            sys.exit(validate_config())
        elif args[1] in ("-h", "--h", "--help"):
            usage()
        else:
            usage()
    else:
        stulog.logger.info(f"Start {ta_short_name} task")
        try:
            run(
                collector_cls,
                settings,
                checkpoint_cls=checkpoint_cls,
                config_cls=configer_cls,
                log_suffix=log_suffix,
            )
        except Exception as e:
            stulog.logger.exception(f"{ta_short_name} task encounter exception")
        stulog.logger.info(f"End {ta_short_name} task")
    sys.exit(0)
