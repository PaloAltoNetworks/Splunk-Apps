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
Copyright (C) 2005-2019 Splunk Inc. All Rights Reserved.

Commonly used design partten for python user, includes:
  - singleton (Decorator function used to build singleton)
"""
import warnings
from functools import wraps


def singleton(class_):
    """
    Singleton decoorator function.
    """
    warnings.warn(
        "This function is deprecated. "
        "Please see https://github.com/splunk/addonfactory-ta-library-python/issues/38",
        DeprecationWarning,
        stacklevel=2,
    )
    instances = {}

    @wraps(class_)
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance


class Singleton(type):
    """
    Singleton meta class
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
            print(cls)
        return cls._instances[cls]
