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
Concurrent executor provides concurrent executing function either in
a thread pool or a process pool
"""

import splunktalib.concurrent.process_pool as pp
import splunktalib.concurrent.thread_pool as tp


class ConcurrentExecutor:
    def __init__(self, config):
        """
        :param config: dict like object, contains thread_min_size (int),
                       thread_max_size (int), daemonize_thread (bool),
                       process_size (int)
        """

        self._io_executor = tp.ThreadPool(
            config.get("thread_min_size", 0),
            config.get("thread_max_size", 0),
            config.get("task_queue_size", 1024),
            config.get("daemonize_thread", True),
        )
        self._compute_executor = None
        if config.get("process_size", 0):
            self._compute_executor = pp.ProcessPool(config.get("process_size", 0))

    def start(self):
        self._io_executor.start()

    def tear_down(self):
        self._io_executor.tear_down()
        if self._compute_executor is not None:
            self._compute_executor.tear_down()

    def run_io_func_sync(self, func, args=(), kwargs=None):
        """
        :param func: callable
        :param args: free params
        :param kwargs: named params
        :return whatever the func returns
        """

        return self._io_executor.apply(func, args, kwargs)

    def run_io_func_async(self, func, args=(), kwargs=None, callback=None):
        """
        :param func: callable
        :param args: free params
        :param kwargs: named params
        :calllback: when func is done and without exception, call the callback
        :return whatever the func returns
        """

        return self._io_executor.apply_async(func, args, kwargs, callback)

    def enqueue_io_funcs(self, funcs, block=True):
        """
        run jobs in a fire and forget way, no result will be handled
        over to clients
        :param funcs: tuple/list-like or generator like object, func shall be
                      callable
        """

        return self._io_executor.enqueue_funcs(funcs, block)

    def run_compute_func_sync(self, func, args=(), kwargs={}):
        """
        :param func: callable
        :param args: free params
        :param kwargs: named params
        :return whatever the func returns
        """

        assert self._compute_executor is not None
        return self._compute_executor.apply(func, args, kwargs)

    def run_compute_func_async(self, func, args=(), kwargs={}, callback=None):
        """
        :param func: callable
        :param args: free params
        :param kwargs: named params
        :calllback: when func is done and without exception, call the callback
        :return whatever the func returns
        """

        assert self._compute_executor is not None
        return self._compute_executor.apply_async(func, args, kwargs, callback)
