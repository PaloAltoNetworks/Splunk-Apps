from builtins import str
from builtins import range
import calendar
import json
import re
import traceback
from collections import Iterable
from datetime import datetime
import six

from jsonpath_rw import parse
from .exceptions import FuncException, StopCCEIteration, QuitJobError
from .pipemgr import PipeManager
from ..common import util, log

_logger = log.get_cc_logger()


def regex_search(pattern, source, flags=0):
    """Search substring in source through regex"""
    if not isinstance(source, six.string_types):
        _logger.warning('Cannot apply regex search on non-string: %s', type(source))
        return {}
    try:
        matches = re.search(pattern=pattern, string=source, flags=flags)
    except Exception:
        _logger.warning('Unable to search pattern=%s and flags=%s in string, error=%s',
                        pattern, flags, traceback.format_exc())
        return {}
    else:
        return matches.groupdict() if matches else {}


def regex_match(pattern, source, flags=0):
    """
    Determine whether a string is match a regex pattern.

    :param pattern: regex pattern
    :param source: candidate to match regex
    :param flags: flags for regex match
    :return: `True` if candidate match pattern else `False`
    """
    try:
        return re.match(pattern, source, flags) is not None
    except Exception:
        _logger.warning(
            'Unable to match source with pattern=%s, cause=%s',
            pattern,
            traceback.format_exc()
        )
    return False


def regex_not_match(pattern, source, flags=0):
    """
    Determine whether a string is not match a regex pattern.

    :param pattern: regex expression
    :param source: candidate to match regex
    :param flags: flags for regex match
    :return: `True` if candidate not match pattern else `False`
    """
    return not regex_match(pattern, source, flags)


def json_path(source, json_path_expr):
    """ Extract value from string with JSONPATH expression.
    :param json_path_expr: JSONPATH expression
    :param source: string to extract value
    :return: A `list` contains all values extracted
    """
    if not source:
        _logger.debug('source to apply JSONPATH is empty, return empty.')
        return ''

    if isinstance(source, six.string_types):
        _logger.debug(
            'source expected is a JSON, not %s. Attempt to'
            ' convert it to JSON',
            type(source)
        )
        try:
            source = json.loads(source)
        except Exception as ex:
            _logger.warning(
                'Unable to load JSON from source: %s. '
                'Attempt to apply JSONPATH "%s" on source directly.',
                ex,
                json_path_expr
            )

    try:
        expression = parse(json_path_expr)
        results = [match.value for match in expression.find(source)]

        _logger.debug(
            'Got %s elements extracted with JSONPATH expression "%s"',
            len(results), json_path_expr
        )

        if not results:
            return ''

        return results[0] or '' if len(results) == 1 else results
    except Exception as ex:
        _logger.warning(
            'Unable to apply JSONPATH expression "%s" on source,'
            ' message=%s cause=%s',
            json_path_expr,
            ex,
            traceback.format_exc()
        )
    return ''


def splunk_xml(candidates,
               time=None,
               index=None,
               host=None,
               source=None,
               sourcetype=None):
    """ Wrap a event with splunk xml format.
    :param candidates: data used to wrap as event
    :param time: timestamp which must be empty or a valid float
    :param index: index name for event
    :param host: host for event
    :param source: source for event
    :param sourcetype: sourcetype for event
    :return: A wrapped event with splunk xml format.
    """
    if not isinstance(candidates, (list, tuple)):
        candidates = [candidates]

    time = time or None
    if time:
        try:
            time = float(time)
        except ValueError:
            _logger.warning(
                '"time" %s is expected to be a float, set "time" to None',
                time
            )
            time = None
    xml_events = util.format_events(
        candidates,
        time=time,
        index=index,
        host=host,
        source=source,
        sourcetype=sourcetype
    )
    _logger.info(
                "[%s] events are formated as splunk stream xml",
                len(candidates)
            )
    return xml_events


def std_output(candidates):
    """ Output a string to stdout.
    :param candidates: List of string to output to stdout or a single string.
    """
    if isinstance(candidates, six.string_types):
        candidates = [candidates]

    all_str = True
    for candidate in candidates:
        if all_str and not isinstance(candidate, six.string_types):
            all_str = False
            _logger.debug(
                'The type of data needs to print is "%s" rather than %s',
                type(candidate),
                str(six.string_types)
            )
            try:
                candidate = json.dumps(candidate)
            except:
                _logger.exception('The type of data needs to print is "%s"'
                                  ' rather than %s',
                                  type(candidate),
                                  str(six.string_types))

        if not PipeManager().write_events(candidate):
            raise FuncException('Fail to output data to stdout. The event'
                                ' writer is stopped or encountered exception')

    _logger.debug('Writing events to stdout finished.')
    return True


def _parse_json(source, json_path_expr=None):
    if not source:
        _logger.debug('Unable to parse JSON from empty source, return empty.')
        return {}

    if json_path_expr:
        _logger.debug(
            'Try to extract JSON from source with JSONPATH expression: %s, ',
            json_path_expr
        )
        source = json_path(source, json_path_expr)

    elif isinstance(source, six.string_types):
        source = json.loads(source)

    return source


def json_empty(source, json_path_expr=None):
    """Check whether a JSON is empty, return True only if the JSON to
     check is a valid JSON and is empty.
    :param json_path_expr: A optional JSONPATH expression
    :param source: source to extract JSON
    :return: `True` if the result JSON is empty
    """
    try:
        data = _parse_json(source, json_path_expr)

        if isinstance(data, (list, tuple)):
            return all(len(ele) == 0 for ele in data)
        return len(data) == 0
    except Exception as ex:
        _logger.warning(
            'Unable to determine whether source is json_empty, treat it as '
            'not json_empty: %s', ex
        )
        return False


def json_not_empty(source, json_path_expr=None):
    """Check if a JSON object is not empty, return True only if the
     source is a valid JSON object and the value leading by
     json_path_expr is empty.
    :param json_path_expr: A optional JSONPATH expression
    :param source: source to extract JSON
    :return: `True` if the result JSON is not empty
    """
    try:
        data = _parse_json(source, json_path_expr)

        if isinstance(data, (list, tuple)):
            return any(len(ele) > 0 for ele in data)
        return len(data) > 0
    except Exception as ex:
        _logger.warning(
            'Unable to determine whether source is json_not_empty, '
            'treat it as not json_not_empty: %s',
            ex
        )
        return False


def set_var(value):
    """Set a variable which name should be specified in `output` with value"""
    return value


def _fix_microsecond_format(fmt, micros):
    """
    implement %Nf so that user can control the digital number of microsecond.
    If number of % is even, don't do replacement.
    If N is not in [1-6], don't do replacement.
    If time length m is less than N, convert it to 6 digitals and return N
    digitals.
    """
    micros = str(micros).zfill(6)

    def do_replacement(x, micros):
        if int(x.group(1)) in range(1, 7) and len(x.group()) % 2:
            return x.group().replace('%' + x.group(1) + 'f',
                                     micros[:min(int(x.group(1)), len(micros))])
        return x.group()

    return re.sub(r'%+([1-6])f', lambda x: do_replacement(x, micros), fmt)


def _fix_timestamp_format(fmt, timestamp):
    """Replace '%s' in time format with timestamp if the number
        of '%' before 's' is odd."""
    return re.sub(
        r'%+s',
        (
            lambda x:
            x.group() if len(x.group()) % 2 else x.group().replace('%s',
                                                                   timestamp)
        ),
        fmt
    )


def time_str2str(date_string, from_format, to_format):
    """Convert a date string with given format to another format. Return
    the original date string if it's type is not string or failed to parse or
    convert it with format."""
    if not isinstance(date_string, six.string_types):
        _logger.warning(
            '"date_string" must be a string type, found %s,'
            ' return the original date_string directly.',
            type(date_string)
        )
        return date_string

    try:
        dt = datetime.strptime(date_string, from_format)
        # Need to pre process '%s' in to_format here because '%s' is not
        # available on all platforms. Even on supported platforms, the
        # result may be different because it depends on implementation on each
        # platform. Replace it with UTC timestamp here directly.
        if to_format:
            timestamp = calendar.timegm(dt.timetuple())
            to_format = _fix_timestamp_format(to_format, str(timestamp))
            to_format = _fix_microsecond_format(to_format, str(dt.microsecond))
        return dt.strftime(to_format)
    except Exception:
        _logger.warning(
            'Unable to convert date_string "%s" from format "%s" to "%s",'
            ' return the original date_string, cause=%s',
            date_string,
            from_format,
            to_format,
            traceback.format_exc()
        )
    return date_string


def is_true(value):
    """Determine whether value is True"""
    return str(value).strip().lower() == 'true'


def exit_if_true(value):
    """Raise a StopCCEIteration exception if value is True"""
    if is_true(value):
        raise StopCCEIteration


def exit_job_if_true(value):
    """Raise a QuitJob exception if value is True"""
    if is_true(value):
        raise QuitJobError


def assert_true(value, message=None):
    """Assert value is True"""
    if not is_true(value):
        raise AssertionError(
            message or '"{value}" is not true'.format(value=value)
        )


def split_by(source, target, separator=None):
    """Split the source to multiple values by the separator"""
    try:
        if not source:
            return []
        elif isinstance(source, six.string_types) and separator:
            values = source.split(separator)
            return [{target: value.strip()} for value in values]
        elif isinstance(source, six.string_types):
            return [{target: source}]
        elif isinstance(source, Iterable):
            return [{target: value} for value in source]
        else:
            return [{target: source}]
    except Exception as ex:
        _logger.warning("split_by method encountered exception "
                        "source=%s message=%s cause=%s", source, ex,
                        traceback.format_exc())
        return []


_extension_functions = {
    'assert_true': assert_true,
    'exit_if_true': exit_if_true,
    'exit_job_if_true': exit_job_if_true,
    'is_true': is_true,
    'regex_match': regex_match,
    'regex_not_match': regex_not_match,
    'regex_search': regex_search,
    'set_var': set_var,
    'splunk_xml': splunk_xml,
    'std_output': std_output,
    'json_path': json_path,
    'json_empty': json_empty,
    'json_not_empty': json_not_empty,
    'time_str2str': time_str2str,
    'split_by': split_by
}


def lookup_method(name):
    """ Find a predefined function with given function name.
    :param name: function name.
    :return: A function with given name.
    """
    return _extension_functions.get(name)
