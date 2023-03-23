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

import json
import os
import os.path as op
import threading
import time

import splunktalib.kv_client as kvc
from splunktalib.common import log, util


def get_state_store(
    meta_configs,
    appname,
    collection_name="talib_states",
    use_kv_store=False,
    use_cached_store=False,
):
    if util.is_true(use_kv_store):
        return StateStore(meta_configs, appname, collection_name)
    elif util.is_true(use_cached_store):
        return CachedFileStateStore(meta_configs, appname)
    else:
        return FileStateStore(meta_configs, appname)


class BaseStateStore:
    def __init__(self, meta_configs, appname):
        self._meta_configs = meta_configs
        self._appname = appname

    def update_state(self, key, states):
        pass

    def get_state(self, key):
        pass

    def delete_state(self, key):
        pass

    def close(self, key=None):
        pass


class StateStore(BaseStateStore):
    def __init__(self, meta_configs, appname, collection_name="talib_states"):
        """
        :meta_configs: dict like and contains checkpoint_dir, session_key,
         server_uri etc
        :app_name: the name of the app
        :collection_name: the collection name to be used.
        Don"t use other method to visit the collection if you are using
         StateStore to visit it.
        """
        super().__init__(meta_configs, appname)

        # State cache is a dict from _key to value
        self._states_cache = {}
        self._kv_client = None
        self._collection = collection_name
        self._kv_client = kvc.KVClient(
            meta_configs["server_uri"], meta_configs["session_key"]
        )
        kvc.create_collection(self._kv_client, self._collection, self._appname)
        self._load_states_cache()

    def update_state(self, key, states):
        """
        :state: Any JSON serializable
        :return: None if successful, otherwise throws exception
        """

        if key not in self._states_cache:
            self._kv_client.insert_collection_data(
                self._collection,
                {"_key": key, "value": json.dumps(states)},
                self._appname,
            )
        else:
            self._kv_client.update_collection_data(
                self._collection, key, {"value": json.dumps(states)}, self._appname
            )
        self._states_cache[key] = states

    def get_state(self, key=None):
        if key:
            return self._states_cache.get(key, None)
        return self._states_cache

    def delete_state(self, key=None):
        if key:
            self._delete_state(key)
        else:
            [self._delete_state(_key) for _key in list(self._states_cache.keys())]

    def _delete_state(self, key):
        if key not in self._states_cache:
            return

        self._kv_client.delete_collection_data(self._collection, key, self._appname)
        del self._states_cache[key]

    def _load_states_cache(self):
        states = self._kv_client.get_collection_data(
            self._collection, None, self._appname
        )
        if not states:
            return

        for state in states:
            if "value" in state:
                value = state["value"]
            else:
                value = state

            try:
                value = json.loads(value)
            except Exception:
                pass

            self._states_cache[state["_key"]] = value


class FileStateStore(BaseStateStore):
    def __init__(self, meta_configs, appname):
        """
        :meta_configs: dict like and contains checkpoint_dir, session_key,
        server_uri etc
        """

        super().__init__(meta_configs, appname)

    def update_state(self, key, states):
        """
        :state: Any JSON serializable
        :return: None if successful, otherwise throws exception
        """

        fname = op.join(self._meta_configs["checkpoint_dir"], key)
        with open(fname + ".new", "w") as jsonfile:
            json.dump(states, jsonfile)

        if op.exists(fname):
            os.remove(fname)

        os.rename(fname + ".new", fname)
        # commented this to disable state cache for local file
        # if key not in self._states_cache:
        # self._states_cache[key] = {}
        # self._states_cache[key] = states

    def get_state(self, key):
        fname = op.join(self._meta_configs["checkpoint_dir"], key)
        if op.exists(fname) and op.isfile(fname):
            with open(fname) as jsonfile:
                state = json.load(jsonfile)
                # commented this to disable state cache for local file
                # self._states_cache[key] = state
                return state
        else:
            return None

    def delete_state(self, key):
        fname = op.join(self._meta_configs["checkpoint_dir"], key)
        if op.exists(fname):
            os.remove(fname)


class CachedFileStateStore(BaseStateStore):
    def __init__(self, meta_configs, appname, max_cache_seconds=5):
        """
        :meta_configs: dict like and contains checkpoint_dir, session_key,
        server_uri etc
        """

        super().__init__(meta_configs, appname)
        self._states_cache = {}  # item: time, dict
        self._states_cache_lmd = {}  # item: time, dict
        self.max_cache_seconds = max_cache_seconds
        self._lock = threading.RLock()

    def update_state(self, key, states):
        with self._lock:
            now = time.time()
            if key in self._states_cache:
                last = self._states_cache_lmd[key][0]
                if now - last >= self.max_cache_seconds:
                    self.update_state_flush(now, key, states)
            else:
                self.update_state_flush(now, key, states)
            self._states_cache[key] = (now, states)

    def update_state_flush(self, now, key, states):
        """
        :state: Any JSON serializable
        :return: None if successful, otherwise throws exception
        """
        for i in range(3):
            try:
                with self._lock:
                    self._states_cache_lmd[key] = (now, states)
                    fname = op.join(self._meta_configs["checkpoint_dir"], key)
                    with open(fname + ".new", "w") as jsonfile:
                        json.dump(states, jsonfile)

                    if op.exists(fname):
                        os.remove(fname)

                    os.rename(fname + ".new", fname)
            except Exception:
                log.logger.exception("Failed to update checkpoint:")
                time.sleep(1)
                continue
            else:
                return
        raise Exception("Failed to update checkpoint")

    def get_state(self, key):
        with self._lock:
            if key in self._states_cache:
                return self._states_cache[key][1]

            fname = op.join(self._meta_configs["checkpoint_dir"], key)
            if op.exists(fname):
                with open(fname) as jsonfile:
                    state = json.load(jsonfile)
                    now = time.time()
                    self._states_cache[key] = now, state
                    self._states_cache_lmd[key] = now, state
                    return state
            else:
                return None

    def delete_state(self, key):
        with self._lock:
            fname = op.join(self._meta_configs["checkpoint_dir"], key)
            if op.exists(fname):
                os.remove(fname)

            if self._states_cache.get(key):
                del self._states_cache[key]
            if self._states_cache_lmd.get(key):
                del self._states_cache_lmd[key]

    def close(self, key=None):
        for i in range(3):
            try:
                with self._lock:
                    if not key:
                        for k, (t, s) in self._states_cache.items():
                            self.update_state_flush(t, k, s)
                        self._states_cache.clear()
                        self._states_cache_lmd.clear()
                    elif key in self._states_cache:
                        self.update_state_flush(
                            self._states_cache[key][0], key, self._states_cache[key][1]
                        )
                        del self._states_cache[key]
                        del self._states_cache_lmd[key]
            except Exception:
                log.logger.exception("Failed to close checkpoint:")
                time.sleep(1)
                continue
            else:
                return
