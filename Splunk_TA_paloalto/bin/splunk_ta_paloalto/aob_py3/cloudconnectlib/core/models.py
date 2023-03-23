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
import base64
import json
import sys
import traceback

from ..common.log import get_cc_logger
from .ext import lookup_method
from .template import compile_template

_logger = get_cc_logger()


class _Token:
    """Token class wraps a template expression"""

    def __init__(self, source):
        """Constructs _Token from source. A rendered template
        will be created if source is string type because Jinja
        template must be a string."""
        self._source = source
        self._value_for = compile_template(source) if isinstance(source, str) else None

    def render(self, variables):
        """Render value with variables if source is a string.
        Otherwise return source directly."""
        if self._value_for is None:
            return self._source
        try:
            return self._value_for(variables)
        except Exception as ex:
            _logger.warning(
                'Unable to render template "%s". Please make sure template is'
                " a valid Jinja2 template and token is exist in variables. "
                "message=%s cause=%s",
                self._source,
                ex,
                traceback.format_exc(),
            )
        return self._source


class DictToken:
    """DictToken wraps a dict which value is template expression"""

    def __init__(self, template_expr):
        self._tokens = {k: _Token(v) for k, v in (template_expr or {}).items()}

    def render(self, variables):
        return {k: v.render(variables) for k, v in self._tokens.items()}


class BaseAuth:
    """A base class for all authorization classes"""

    def __call__(self, headers, context):
        raise NotImplementedError("Auth must be callable.")


class BasicAuthorization(BaseAuth):
    """BasicAuthorization class implements basic auth"""

    def __init__(self, options):
        if not options:
            raise ValueError("Options for basic auth unexpected to be empty")

        username = options.get("username")
        if not username:
            raise ValueError("Username is mandatory for basic auth")
        password = options.get("password")
        if not password:
            raise ValueError("Password is mandatory for basic auth")

        self._username = _Token(username)
        self._password = _Token(password)

    def to_native_string(self, string, encoding="ascii"):
        """
        According to rfc7230:
            Historically, HTTP has allowed field content with text in the
            ISO-8859-1 charset [ISO-8859-1], supporting other charsets only
            through use of [RFC2047] encoding.  In practice, most HTTP header
            field values use only a subset of the US-ASCII charset [USASCII].
            Newly defined header fields SHOULD limit their field values to
            US-ASCII octets.  A recipient SHOULD treat other octets in field
            content (obs-text) as opaque data.
        """
        is_py2 = sys.version_info[0] == 2
        if isinstance(string, str):
            out = string
        else:
            if is_py2:
                out = string.encode(encoding)
            else:
                out = string.decode(encoding)

        return out

    def __call__(self, headers, context):
        username = self._username.render(context)
        password = self._password.render(context)
        headers["Authorization"] = (
            "Basic %s"
            % self.to_native_string(
                base64.b64encode((username + ":" + password).encode("latin1"))
            ).strip()
        )


class RequestParams:
    def __init__(self, url, method, header=None, auth=None, body=None):
        self._header = DictToken(header)
        self._url = _Token(url)
        self._method = method.upper()
        self._auth = auth
        self._body = DictToken(body)

    @property
    def header(self):
        return self._header

    @property
    def url(self):
        return self._url

    @property
    def method(self):
        return self._method

    @property
    def auth(self):
        return self._auth

    @property
    def body(self):
        return self._body

    def render(self, ctx):
        return Request(
            url=self._url.render(ctx),
            method=self._method,
            headers=self.normalize_headers(ctx),
            body=self.body.render(ctx),
        )

    def normalize_url(self, context):
        """Normalize url"""
        return self._url.render(context)

    def normalize_headers(self, context):
        """Normalize headers which must be a dict which keys and values are
        string."""
        header = self.header.render(context)
        return {k: str(v) for k, v in header.items()}

    def normalize_body(self, context):
        """Normalize body"""
        return self.body.render(context)


class Request:
    def __init__(self, method, url, headers, body):
        self.method = method
        self.url = url
        self.headers = headers
        if not body:
            body = None
        elif not isinstance(body, str):
            body = json.dumps(body)
        self.body = body


class _Function:
    def __init__(self, inputs, function):
        self._inputs = tuple(_Token(expr) for expr in inputs or [])
        self._function = function

    @property
    def inputs(self):
        return self._inputs

    def inputs_values(self, context):
        """
        Get rendered input values.
        """
        for arg in self._inputs:
            yield arg.render(context)

    @property
    def function(self):
        return self._function


class Task(_Function):
    """Task class wraps a task in processor pipeline"""

    def __init__(self, inputs, function, output=None):
        super().__init__(inputs, function)
        self._output = output

    @property
    def output(self):
        return self._output

    def execute(self, context):
        """Execute task with arguments which rendered from context"""
        args = [arg for arg in self.inputs_values(context)]
        caller = lookup_method(self.function)
        output = self._output

        _logger.info(
            "Executing task method: [%s], input size: [%s], output: [%s]",
            self.function,
            len(args),
            output,
        )

        if output is None:
            caller(*args)
            return {}

        return {output: caller(*args)}


class Condition(_Function):
    """A condition return the value calculated from input and function"""

    def calculate(self, context):
        """Calculate condition with input arguments rendered from context
        and method which expected return a bool result.
        :param context: context contains key value pairs
        :return A bool value returned from the corresponding method
        """
        args = [arg for arg in self.inputs_values(context)]
        callable_method = lookup_method(self.function)

        _logger.debug(
            "Calculating condition with method: [%s], input size: [%s]",
            self.function,
            len(args),
        )

        result = callable_method(*args)

        _logger.debug("Calculated result: %s", result)

        return result


class _Conditional:
    """A base class for all conditional action"""

    def __init__(self, conditions):
        self._conditions = conditions or []

    @property
    def conditions(self):
        return self._conditions

    def passed(self, context):
        """Determine if any condition is satisfied.
        :param context: variables to render template
        :return: `True` if all passed else `False`
        """
        return any(condition.calculate(context) for condition in self._conditions)


class Processor(_Conditional):
    """Processor class contains a conditional data process pipeline"""

    def __init__(self, skip_conditions, pipeline):
        super().__init__(skip_conditions)
        self._pipeline = pipeline or []

    @property
    def pipeline(self):
        return self._pipeline

    def should_skipped(self, context):
        """Determine processor if should skip process"""
        return self.passed(context)


class IterationMode(_Conditional):
    def __init__(self, iteration_count, conditions):
        super().__init__(conditions)
        self._iteration_count = iteration_count

    @property
    def iteration_count(self):
        return self._iteration_count

    @property
    def conditions(self):
        return self._conditions


class Checkpoint:
    """A checkpoint includes a namespace to determine the checkpoint location
    and a content defined the format of content stored in checkpoint."""

    def __init__(self, namespace, content):
        """Constructs checkpoint with given namespace and content template."""
        if not content:
            raise ValueError("Checkpoint content must not be empty")

        self._namespace = tuple(_Token(expr) for expr in namespace or ())
        self._content = DictToken(content)

    @property
    def namespace(self):
        return self._namespace

    def normalize_namespace(self, ctx):
        """Normalize namespace with context used to render template."""
        return [token.render(ctx) for token in self._namespace]

    @property
    def content(self):
        return self._content

    def normalize_content(self, ctx):
        """Normalize checkpoint with context used to render template."""
        return self._content.render(ctx)
