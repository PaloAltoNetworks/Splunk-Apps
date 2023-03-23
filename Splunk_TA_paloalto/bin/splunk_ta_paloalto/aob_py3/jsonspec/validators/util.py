"""
    jsonspec.validators.util
    ~~~~~~~~~~~~~~~~~~~~~~~~

"""

from __future__ import absolute_import

import logging
import re
import time
from copy import deepcopy
from decimal import Decimal
from datetime import tzinfo, timedelta, datetime, date
from six import text_type
from six import integer_types
from six.moves.urllib.parse import urlparse
from .exceptions import ValidationError

__all__ = []

number_types = (integer_types, float, Decimal)

logger = logging.getLogger(__name__)

HOSTNAME_TOKENS = re.compile('(?!-)[a-z\d-]{1,63}(?<!-)$', re.IGNORECASE)
HOSTNAME_LAST_TOKEN = re.compile('[a-z]+$', re.IGNORECASE)
EMAIL = re.compile('[^@]+@[^@]+\.[^@]+')

CSS_COLORS = set([
    'aliceblue', 'antiquewhite', 'aqua', 'aquamarine', 'azure', 'beige',
    'bisque', 'black', 'blanchedalmond', 'blue', 'blueviolet', 'brown',
    'burlywood', 'cadetblue', 'chartreuse', 'chocolate', 'coral',
    'cornflowerblue', 'cornsilk', 'crimson', 'darkblue', 'darkcyan',
    'darkgoldenrod', 'darkgray', 'darkgreen', 'darkkhaki', 'darkmagenta',
    'darkolivegreen', 'darkorange', 'darkorchid', 'darkred', 'darksalmon',
    'darkseagreen', 'darkslateblue', 'darkslategray', 'darkturquoise',
    'darkviolet', 'deeppink', 'deepskyblue', 'dimgray', 'dodgerblue',
    'feldspar', 'firebrick', 'floralwhite', 'forestgreen', 'fuchsia',
    'gainsboro', 'ghostwhite', 'gold', 'goldenrod', 'gray', 'green',
    'greenyellow', 'honeydew', 'hotpink', 'indianred', 'indigo', 'ivory',
    'khaki', 'lavender', 'lavenderblush', 'lawngreen', 'lemonchiffon',
    'lightblue', 'lightcoral', 'lightcyan', 'lightgoldenrodyellow',
    'lightgreen', 'lightgrey', 'lightpink', 'lightsalmon', 'lightseagreen',
    'lightskyblue', 'lightslateblue', 'lightslategray', 'lightsteelblue',
    'lightyellow', 'lime', 'limegreen', 'linen', 'maroon', 'mediumaquamarine',
    'mediumblue', 'mediumorchid', 'mediumpurple', 'mediumseagreen',
    'mediumslateblue', 'mediumspringgreen', 'mediumturquoise',
    'mediumvioletred', 'midnightblue', 'mintcream', 'mistyrose', 'moccasin',
    'navajowhite', 'navy', 'oldlace', 'olive', 'olivedrab', 'orange',
    'orangered', 'orchid', 'palegoldenrod', 'palegreen', 'paleturquoise',
    'palevioletred', 'papayawhip', 'peachpuff', 'peru', 'pink', 'plum',
    'powderblue', 'purple', 'red', 'rosybrown', 'royalblue', 'saddlebrown',
    'salmon', 'sandybrown', 'seagreen', 'seashell', 'sienna', 'silver',
    'skyblue', 'slateblue', 'slategray', 'snow', 'springgreen', 'steelblue',
    'tan', 'teal', 'thistle', 'tomato', 'turquoise', 'violetred', 'wheat',
    'white', 'whitesmoke', 'yellow', 'yellowgreen'])


def uncamel(name):
    """converts camelcase to underscore
    >>> uncamel('fooBar')
    'foo_bar'
    >>> uncamel('FooBar')
    'foo_bar'
    >>> uncamel('_fooBar')
    '_foo_bar'
    >>> uncamel('_FooBar')
    '__foo_bar'
    """
    response, name = name[0].lower(), name[1:]
    for n in name:
        if n.isupper():
            response += '_' + n.lower()
        else:
            response += n
    return response


class offset(tzinfo):
    def __init__(self, value):
        self.value = value

    def utcoffset(self, dt):
        hours, minutes = self.value.split(':', 1)
        return timedelta(hours=int(hours), minutes=int(minutes))

    def tzname(self, dt):
        return '{}'.format(self.value)


def rfc3339_to_datetime(data):
    """convert a rfc3339 date representation into a Python datetime"""
    try:
        ts = time.strptime(data, '%Y-%m-%d')
        return date(*ts[:3])
    except ValueError:
        pass

    try:
        dt, _, tz = data.partition('Z')
        if tz:
            tz = offset(tz)
        else:
            tz = offset('00:00')
        if '.' in dt and dt.rsplit('.', 1)[-1].isdigit():
            ts = time.strptime(dt, '%Y-%m-%dT%H:%M:%S.%f')
        else:
            ts = time.strptime(dt, '%Y-%m-%dT%H:%M:%S')
        return datetime(*ts[:6], tzinfo=tz)
    except ValueError:
        raise ValueError('date-time {!r} is not a valid rfc3339 date representation'.format(data))  # noqa


def validate_css_color(obj):
    color = obj.lower()
    if len(color) == 7 and re.match('^#[0-9a-f]{6}$', color):
        return obj
    elif len(color) == 4 and re.match('^#[0-9a-f]{3}$', color):
        return obj
    elif color not in CSS_COLORS:
        raise ValidationError('Not a css color {!r}'.format(obj))
    return obj


def validate_rfc3339_datetime(obj):
    try:
        rfc3339_to_datetime(obj)
    except ValueError:
        raise ValidationError('{!r} is not a valid datetime', obj)
    return obj


def validate_utc_datetime(obj):
    if not obj.endswith('Z'):
        raise ValidationError('{!r} is not a valid datetime', obj)
    obj = obj[:-1]
    if '.' in obj:
        obj, milli = obj.split('.', 1)
        if not milli.isdigit():
            raise ValidationError('{!r} is not a valid datetime', obj)

    try:
        time.strptime(obj, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        raise ValidationError('{!r} is not a valid datetime', obj)
    return obj


def validate_utc_date(obj):
    try:
        time.strptime(obj, '%Y-%m-%d')
    except (TypeError, ValueError):
        raise ValidationError('{!r} is not a valid date', obj)
    return obj


def validate_utc_time(obj):
    try:
        time.strptime(obj, '%H:%M:%S')
    except (TypeError, ValueError):
        raise ValidationError('{!r} is not a valid time', obj)
    return obj


def validate_utc_millisec(obj):
    try:
        if not isinstance(obj, number_types):
            raise TypeError
        datetime.utcfromtimestamp(obj / 1000)
    except (TypeError, ValueError):
        raise ValidationError('{!r} is not a valid utc millis', obj)
    return obj


def validate_email(obj):
    if not EMAIL.match(obj):
        raise ValidationError('{!r} is not defined')
    return obj


def validate_hostname(obj):
    try:
        host = deepcopy(obj)
        if len(host) > 255:
            raise ValueError
        if host[-1] == '.':
            host = host[:-1]
        tokens = host.split('.')
        if not all(HOSTNAME_TOKENS.match(x) for x in tokens):
            raise ValueError
        if not HOSTNAME_LAST_TOKEN.search(tokens[-1]):
            raise ValueError
    except ValueError:
        raise ValidationError('{!r} is not a valid hostname'.format(obj))
    return obj


def validate_ipv4(obj):
    try:
        import ipaddress
        obj = text_type(obj)
        ipaddress.IPv4Address(obj)
    except ImportError:
        raise ValidationError('IPv4 relies on ipaddress package', obj)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
        raise ValidationError('{!r} does not appear to '
                              'be an IPv4 address'.format(obj))
    return obj


def validate_ipv6(obj):
    try:
        import ipaddress
        obj = text_type(obj)
        ipaddress.IPv6Address(obj)
    except ImportError:
        raise ValidationError('IPv6 relies on ipaddress package', obj)
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
        raise ValidationError('{!r} does not appear to '
                              'be an IPv6 address'.format(obj))
    return obj


def validate_regex(obj):
    # TODO implement ECMA 262 regex
    import re
    try:
        re.compile(obj)
    except:
        raise ValidationError('Not a regex', obj)
    return obj


def validate_uri(obj):
    try:
        if ':' not in obj:
            raise ValueError('missing scheme')
        urlparse(obj)
    except Exception as error:
        logger.exception(error)
        raise ValidationError('{!r} is not an uri'.format(obj))
    return obj
