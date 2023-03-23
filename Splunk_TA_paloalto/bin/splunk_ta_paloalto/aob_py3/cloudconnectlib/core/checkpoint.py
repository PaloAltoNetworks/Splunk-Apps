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
import cloudconnectlib.splunktacollectorlib.data_collection.ta_checkpoint_manager as tacm
from cloudconnectlib.common.log import get_cc_logger
from cloudconnectlib.core.models import DictToken, _Token

logger = get_cc_logger()


class CheckpointManagerAdapter(tacm.TACheckPointMgr):
    """Wrap TACheckPointMgr for custom usage"""

    def __init__(self, namespaces, content, meta_config, task_config):
        super().__init__(meta_config, task_config)
        if isinstance(namespaces, (list, tuple)):
            self.namespaces = (_Token(t) for t in namespaces)
        else:
            self.namespaces = [_Token(namespaces)]
        self.content = DictToken(content)

    def _namespaces_for(self, ctx):
        return [item.render(ctx) for item in self.namespaces]

    def save(self, ctx):
        """Save checkpoint"""
        super().update_ckpt(
            ckpt=self.content.render(ctx), namespaces=self._namespaces_for(ctx)
        )

    def load(self, ctx):
        """Load checkpoint"""
        namespaces = self._namespaces_for(ctx)
        checkpoint = super().get_ckpt(namespaces)
        if checkpoint is None:
            logger.info("No existing checkpoint found")
            checkpoint = {}
        return checkpoint
