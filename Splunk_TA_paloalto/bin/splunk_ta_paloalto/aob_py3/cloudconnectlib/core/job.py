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
import threading

from ..common import log
from .exceptions import QuitJobError
from .task import BaseTask

logger = log.get_cc_logger()


class CCEJob:
    """
    One CCEJob is composed of a list of tasks. The task could be HTTP
     task or Split task(currently supported task types).
    Job is an executing unit of CCE engine.
    All tasks in one job will be run sequentially but different jobs
    could be run concurrently.
    So if there is no dependency among tasks, then suggest to create
    different Job for them to improve performance.
    """

    def __init__(self, context, tasks=None):
        self._context = context
        self._rest_tasks = []

        self._stop_signal_received = False
        self._stopped = threading.Event()

        if tasks:
            self._rest_tasks.extend(tasks)
        self._running_task = None
        self._proxy_info = None

    def set_proxy(self, proxy_setting):
        """
        Setup the proxy setting.

        :param proxy_setting: Proxy setting should include the following fields
            "proxy_enabled": ,
            "proxy_url":,
            "proxy_port": ,
            "proxy_username": ,
            "proxy_password": ,
            "proxy_rdns": ,
            "proxy_type": ,
        :type proxy_setting: ``dict``
        """
        self._proxy_info = proxy_setting
        logger.debug(
            "CCEJob proxy info: proxy_enabled='%s', proxy_url='%s', "
            "proxy_port='%s', proxy_rdns='%s', proxy_type='%s', "
            "proxy_username='%s'",
            proxy_setting.get("proxy_enabled"),
            proxy_setting.get("proxy_url"),
            proxy_setting.get("proxy_port"),
            proxy_setting.get("proxy_rdns"),
            proxy_setting.get("proxy_type"),
            proxy_setting.get("proxy_username"),
        )

    def add_task(self, task):
        """
        Add a task instance into a job.

        :param task: TBD
        :type task: TBD
        """
        if not isinstance(task, BaseTask):
            raise ValueError(f"Unsupported task type: {type(task)}")
        if callable(getattr(task, "set_proxy", None)) and self._proxy_info:
            task.set_proxy(self._proxy_info)
        self._rest_tasks.append(task)

    def _check_if_stop_needed(self):
        if self._stop_signal_received:
            logger.info("Stop job signal received, stopping job.")
            self._stopped.set()
            return True
        return False

    def run(self):
        """
        Run current job, which executes tasks in it sequentially.
        """
        logger.debug("Start to run job")

        if not self._rest_tasks:
            logger.info("No task found in job")
            return

        if self._check_if_stop_needed():
            return

        self._running_task = self._rest_tasks[0]
        self._rest_tasks = self._rest_tasks[1:]

        try:
            contexts = list(self._running_task.perform(self._context) or ())
        except QuitJobError:
            logger.info("Quit job signal received, exiting job")
            return

        if self._check_if_stop_needed():
            return

        if not self._rest_tasks:
            logger.info("No more task need to perform, exiting job")
            return

        count = 0

        for ctx in contexts:
            count += 1
            yield CCEJob(context=ctx, tasks=self._rest_tasks)

            if self._check_if_stop_needed():
                break

        logger.debug("Generated %s job in total", count)
        logger.debug("Job execution finished successfully.")
        self._stopped.set()

    def stop(self, block=False, timeout=30):
        """
        Stop current job.
        """
        if self._stopped.is_set():
            logger.info("Job is not running, cannot stop it.")
            return
        self._stop_signal_received = True

        if self._running_task:
            self._running_task.stop(block, timeout)
        if not block:
            return

        if not self._stopped.wait(timeout):
            logger.info("Waiting for stop job timeout")

    def __str__(self):
        if self._running_task:
            return f"Job(running task={self._running_task})"
        return "Job(no running task)"

    def __repr__(self):
        return self.__str__()
