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
"""Default config for cloud connect"""

timeout = 120  # request timeout is two minutes

disable_ssl_cert_validation = False  # default enable SSL validation

success_statuses = (200, 201)  # statuses be treated as success.

# response status which need to retry.
retry_statuses = (429, 500, 501, 502, 503, 504, 505, 506, 507,
                  509, 510, 511)

# response status which need print a warning log.
warning_statuses = (203, 204, 205, 206, 207, 208, 226,
                    300, 301, 302, 303, 304, 305, 306, 307, 308)
retries = 3  # Default maximum retry times.

max_iteration_count = 100  # maximum iteration loop count

charset = 'utf-8'  # Default response charset if not found in response header
