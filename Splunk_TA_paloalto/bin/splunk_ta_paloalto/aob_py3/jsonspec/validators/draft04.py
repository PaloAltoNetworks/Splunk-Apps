"""
    jsonspec.validators.draft04
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Implements JSON Schema draft04.
"""

from __future__ import absolute_import

import logging
import re
from copy import deepcopy
from decimal import Decimal
from six import integer_types, string_types
from six.moves.urllib.parse import urljoin
from .bases import ReferenceValidator, Validator
from .exceptions import CompilationError
from .factorize import register
from jsonspec.validators.exceptions import ValidationError
from jsonspec.validators.util import uncamel
from jsonspec.validators.pointer_util import pointer_join
from jsonspec import driver as json

__all__ = ['compile', 'Draft04Validator']

sequence_types = (list, set, tuple)
number_types = (integer_types, float, Decimal)
logger = logging.getLogger(__name__)


@register(spec='http://json-schema.org/draft-04/schema#')
def compile(schema, pointer, context, scope=None):
    """
    Compiles schema with `JSON Schema`_ draft-04.

    :param schema: obj to compile
    :type schema: Mapping
    :param pointer: uri of the schema
    :type pointer: Pointer, str
    :param context: context of this schema
    :type context: Context

    .. _`JSON Schema`: http://json-schema.org
    """

    schm = deepcopy(schema)

    scope = urljoin(scope or str(pointer), schm.pop('id', None))

    if '$ref' in schema:
        return ReferenceValidator(urljoin(scope, schema['$ref']), context)

    attrs = {}

    if 'additionalItems' in schm:
        subpointer = pointer_join(pointer, 'additionalItems')
        attrs['additional_items'] = schm.pop('additionalItems')
        if isinstance(attrs['additional_items'], dict):
            compiled = compile(attrs['additional_items'],
                               subpointer,
                               context,
                               scope)
            attrs['additional_items'] = compiled
        elif not isinstance(attrs['additional_items'], bool):
            raise CompilationError('wrong type for {}'.format('additional_items'), schema)  # noqa

    if 'additionalProperties' in schm:
        subpointer = pointer_join(pointer, 'additionalProperties')
        attrs['additional_properties'] = schm.pop('additionalProperties')
        if isinstance(attrs['additional_properties'], dict):
            compiled = compile(attrs['additional_properties'],
                               subpointer,
                               context,
                               scope)
            attrs['additional_properties'] = compiled
        elif not isinstance(attrs['additional_properties'], bool):
            raise CompilationError('wrong type for {}'.format('additional_properties'), schema)  # noqa

    if 'allOf' in schm:
        subpointer = pointer_join(pointer, 'allOf')
        attrs['all_of'] = schm.pop('allOf')
        if isinstance(attrs['all_of'], (list, tuple)):
            attrs['all_of'] = [compile(element, subpointer, context, scope) for element in attrs['all_of']]  # noqa
        else:
            # should be a boolean
            raise CompilationError('wrong type for {}'.format('allOf'), schema)  # noqa

    if 'anyOf' in schm:
        subpointer = pointer_join(pointer, 'anyOf')
        attrs['any_of'] = schm.pop('anyOf')
        if isinstance(attrs['any_of'], (list, tuple)):
            attrs['any_of'] = [compile(element, subpointer, context, scope) for element in attrs['any_of']]  # noqa
        else:
            # should be a boolean
            raise CompilationError('wrong type for {}'.format('anyOf'), schema)  # noqa

    if 'default' in schm:
        attrs['default'] = schm.pop('default')

    if 'dependencies' in schm:
        attrs['dependencies'] = schm.pop('dependencies')
        if not isinstance(attrs['dependencies'], dict):
            raise CompilationError('dependencies must be an object', schema)
        for key, value in attrs['dependencies'].items():
            if isinstance(value, dict):
                subpointer = pointer_join(pointer, 'dependencies', key)
                attrs['dependencies'][key] = compile(value,
                                                     subpointer,
                                                     context,
                                                     scope)
            elif not isinstance(value, sequence_types):
                raise CompilationError('dependencies must be an array or object', schema)  # noqa

    if 'enum' in schm:
        attrs['enum'] = schm.pop('enum')
        if not isinstance(attrs['enum'], sequence_types):
            raise CompilationError('enum must be a sequence', schema)

    if 'exclusiveMaximum' in schm:
        attrs['exclusive_maximum'] = schm.pop('exclusiveMaximum')
        if not isinstance(attrs['exclusive_maximum'], bool):
            raise CompilationError('exclusiveMaximum must be a boolean', schema)  # noqa

    if 'exclusiveMinimum' in schm:
        attrs['exclusive_minimum'] = schm.pop('exclusiveMinimum')
        if not isinstance(attrs['exclusive_minimum'], bool):
            raise CompilationError('exclusiveMinimum must be a boolean', schema)  # noqa

    if 'format' in schm:
        attrs['format'] = schm.pop('format')
        if not isinstance(attrs['format'], string_types):
            raise CompilationError('format must be a string', schema)

    if 'items' in schm:
        subpointer = pointer_join(pointer, 'items')
        attrs['items'] = schm.pop('items')
        if isinstance(attrs['items'], (list, tuple)):
            # each value must be a json schema
            attrs['items'] = [compile(element, subpointer, context, scope) for element in attrs['items']]  # noqa
        elif isinstance(attrs['items'], dict):
            # value must be a json schema
            attrs['items'] = compile(attrs['items'], subpointer, context, scope)  # noqa
        else:
            # should be a boolean
            raise CompilationError('wrong type for {}'.format('items'), schema)  # noqa

    if 'maximum' in schm:
        attrs['maximum'] = schm.pop('maximum')
        if not isinstance(attrs['maximum'], number_types):
            raise CompilationError('maximum must be a number', schema)

    if 'maxItems' in schm:
        attrs['max_items'] = schm.pop('maxItems')
        if not isinstance(attrs['max_items'], integer_types):
            raise CompilationError('maxItems must be integer', schema)

    if 'maxLength' in schm:
        attrs['max_length'] = schm.pop('maxLength')
        if not isinstance(attrs['max_length'], integer_types):
            raise CompilationError('maxLength must be integer', schema)

    if 'maxProperties' in schm:
        attrs['max_properties'] = schm.pop('maxProperties')
        if not isinstance(attrs['max_properties'], integer_types):
            raise CompilationError('maxProperties must be integer', schema)

    if 'minimum' in schm:
        attrs['minimum'] = schm.pop('minimum')
        if not isinstance(attrs['minimum'], number_types):
            raise CompilationError('minimum must be a number', schema)

    if 'minItems' in schm:
        attrs['min_items'] = schm.pop('minItems')
        if not isinstance(attrs['min_items'], integer_types):
            raise CompilationError('minItems must be integer', schema)

    if 'minLength' in schm:
        attrs['min_length'] = schm.pop('minLength')
        if not isinstance(attrs['min_length'], integer_types):
            raise CompilationError('minLength must be integer', schema)

    if 'minProperties' in schm:
        attrs['min_properties'] = schm.pop('minProperties')
        if not isinstance(attrs['min_properties'], integer_types):
            raise CompilationError('minProperties must be integer', schema)

    if 'multipleOf' in schm:
        attrs['multiple_of'] = schm.pop('multipleOf')
        if not isinstance(attrs['multiple_of'], number_types):
            raise CompilationError('multipleOf must be a number', schema)

    if 'not' in schm:
        attrs['not'] = schm.pop('not')
        if not isinstance(attrs['not'], dict):
            raise CompilationError('not must be an object', schema)
        subpointer = pointer_join(pointer, 'not')
        attrs['not'] = compile(attrs['not'], subpointer, context, scope)

    if 'oneOf' in schm:
        subpointer = pointer_join(pointer, 'oneOf')
        attrs['one_of'] = schm.pop('oneOf')
        if isinstance(attrs['one_of'], (list, tuple)):
            # each value must be a json schema
            attrs['one_of'] = [compile(element, subpointer, context, scope) for element in attrs['one_of']]  # noqa
        else:
            # should be a boolean
            raise CompilationError('wrong type for {}'.format('oneOf'), schema)

    if 'pattern' in schm:
        attrs['pattern'] = schm.pop('pattern')
        if not isinstance(attrs['pattern'], string_types):
            raise CompilationError('pattern must be a string', schema)

    if 'properties' in schm:
        attrs['properties'] = schm.pop('properties')
        if not isinstance(attrs['properties'], dict):
            raise CompilationError('properties must be an object', schema)
        for subname, subschema in attrs['properties'].items():
            subpointer = pointer_join(pointer, subname)
            compiled = compile(subschema, subpointer, context, scope)
            attrs['properties'][subname] = compiled

    if 'patternProperties' in schm:
        attrs['pattern_properties'] = schm.pop('patternProperties')
        if not isinstance(attrs['pattern_properties'], dict):
            raise CompilationError('patternProperties must be an object', schema)  # noqa
        for subname, subschema in attrs['pattern_properties'].items():
            subpointer = pointer_join(pointer, 'patternProperties', subname)
            compiled = compile(subschema, subpointer, context, scope)
            attrs['pattern_properties'][subname] = compiled

    if 'required' in schm:
        attrs['required'] = schm.pop('required')
        if not isinstance(attrs['required'], list):
            raise CompilationError('required must be a list', schema)
        if len(attrs['required']) < 1:
            raise CompilationError('required cannot be empty', schema)

    if 'type' in schm:
        attrs['type'] = schm.pop('type')
        if isinstance(attrs['type'], string_types):
            attrs['type'] = [attrs['type']]
        elif not isinstance(attrs['type'], sequence_types):
            raise CompilationError('type must be string or sequence', schema)

    if 'uniqueItems' in schm:
        attrs['unique_items'] = schm.pop('uniqueItems')
        if not isinstance(attrs['unique_items'], bool):
            raise CompilationError('type must be boolean', schema)

    return Draft04Validator(attrs, str(pointer), context.formats)


class Draft04Validator(Validator):
    """
    Implements `JSON Schema`_ draft-04 validation.

    :ivar attrs: attributes to validate against
    :ivar uri: uri of the current validator
    :ivar formats: mapping of available formats

    >>> validator = Draft04Validator({'min_length': 4})
    >>> assert validator('this is sparta')

    .. _`JSON Schema`: http://json-schema.org
    """

    def __init__(self, attrs, uri=None, formats=None):
        attrs = {uncamel(k): v for k, v in attrs.items()}

        self.formats = formats or {}
        self.attrs = attrs
        self.attrs.setdefault('additional_items', True)
        self.attrs.setdefault('additional_properties', True)
        self.attrs.setdefault('exclusive_maximum', False),
        self.attrs.setdefault('exclusive_minimum', False),
        self.attrs.setdefault('pattern_properties', {})
        self.attrs.setdefault('properties', {})
        self.uri = uri
        self.default = self.attrs.get('default', None)
        self.fail_fast = True
        self.errors = []

    def validate(self, obj, pointer=None):
        """
        Validate object against validator

        :param obj: the object to validate
        """

        pointer = pointer or '#'

        validator = deepcopy(self)
        validator.errors = []
        validator.fail_fast = False

        obj = deepcopy(obj)
        obj = validator.validate_enum(obj, pointer)
        obj = validator.validate_type(obj, pointer)
        obj = validator.validate_not(obj, pointer)
        obj = validator.validate_all_of(obj, pointer)
        obj = validator.validate_any_of(obj, pointer)
        obj = validator.validate_one_of(obj, pointer)

        if self.is_array(obj):
            obj = validator.validate_items(obj, pointer)
            obj = validator.validate_max_items(obj, pointer)
            obj = validator.validate_min_items(obj, pointer)
            obj = validator.validate_unique_items(obj, pointer)
        elif self.is_number(obj):
            obj = validator.validate_maximum(obj, pointer)
            obj = validator.validate_minimum(obj, pointer)
            obj = validator.validate_multiple_of(obj, pointer)
        elif self.is_object(obj):
            obj = validator.validate_required(obj, pointer)
            obj = validator.validate_max_properties(obj, pointer)
            obj = validator.validate_min_properties(obj, pointer)
            obj = validator.validate_dependencies(obj, pointer)
            obj = validator.validate_properties(obj, pointer)
            obj = validator.validate_default_properties(obj, pointer)
        elif self.is_string(obj):
            obj = validator.validate_max_length(obj, pointer)
            obj = validator.validate_min_length(obj, pointer)
            obj = validator.validate_pattern(obj, pointer)
            obj = validator.validate_format(obj, pointer)

        if validator.errors:
            raise ValidationError('multiple errors',
                                  obj,
                                  errors=validator.errors)

        return obj

    def is_array(self, obj):
        return isinstance(obj, sequence_types)

    def is_boolean(self, obj):
        return isinstance(obj, bool)

    def is_integer(self, obj):
        return isinstance(obj, integer_types) and not isinstance(obj, bool)

    def is_number(self, obj):
        return isinstance(obj, number_types) and not isinstance(obj, bool)

    def is_object(self, obj):
        return isinstance(obj, dict)

    def is_string(self, obj):
        return isinstance(obj, string_types)

    def has_default(self):
        return 'default' in self.attrs

    def validate_all_of(self, obj, pointer=None):
        for validator in self.attrs.get('all_of', []):
            obj = validator(obj)
        return obj

    def validate_any_of(self, obj, pointer=None):
        if 'any_of' in self.attrs:
            for validator in self.attrs['any_of']:
                try:
                    obj = validator(obj)
                    return obj
                except ValidationError:
                    pass
            self.fail('Not in any_of', obj, pointer)
        return obj

    def validate_default_properties(self, obj, pointer=None):
        # Reinject defaults from properties.
        for name, validator in self.attrs.get('properties', {}).items():
            if name not in obj and validator.has_default():
                obj[name] = deepcopy(validator.default)
        return obj

    def validate_dependencies(self, obj, pointer=None):
        for key, dependencies in self.attrs.get('dependencies', {}).items():
            if key in obj:
                if isinstance(dependencies, sequence_types):
                    for name in set(dependencies) - set(obj.keys()):
                        self.fail('Missing property', obj, pointer_join(pointer, name))  # noqa
                else:
                    dependencies(obj)
        return obj

    def validate_enum(self, obj, pointer=None):
        if 'enum' in self.attrs:
            if obj not in self.attrs['enum']:
                self.fail('Forbidden value', obj, pointer)
        return obj

    def validate_format(self, obj, pointer=None):
        """
        ================= ============
        Expected draft04  Alias of
        ----------------- ------------
        date-time         rfc3339.datetime
        email             email
        hostname          hostname
        ipv4              ipv4
        ipv6              ipv6
        uri               uri
        ================= ============

        """
        if 'format' in self.attrs:
            substituted = {
                'date-time': 'rfc3339.datetime',
                'email': 'email',
                'hostname': 'hostname',
                'ipv4': 'ipv4',
                'ipv6': 'ipv6',
                'uri': 'uri',
            }.get(self.attrs['format'], self.attrs['format'])
            logger.debug('use %s', substituted)
            try:
                return self.formats[substituted](obj)
            except ValidationError as error:
                logger.error(error)
                self.fail('Forbidden value', obj, pointer)
        return obj

    def validate_items(self, obj, pointer=None):
        if 'items' in self.attrs:
            items = self.attrs['items']
            if isinstance(items, Validator):
                validator = items
                for index, element in enumerate(obj):
                    with self.catch_fail():
                        obj[index] = validator(element, pointer_join(pointer, index))  # noqa
                return obj
            elif isinstance(items, (list, tuple)):
                additionals = self.attrs['additional_items']
                validators = items

                validated = list(obj)
                for index, element in enumerate(validated):
                    with self.catch_fail():
                        try:
                            validator = validators[index]
                        except IndexError:
                            if additionals is True:
                                return obj
                            elif additionals is False:
                                self.fail('Forbidden value',
                                          obj,
                                          pointer=pointer_join(self.uri, index))  # noqa
                                continue
                            validator = additionals
                        validated[index] = \
                            validator(element, pointer_join(pointer, index))  # noqa
                obj = obj.__class__(validated)
                return obj
            else:
                raise NotImplementedError(items)
        return obj

    def validate_maximum(self, obj, pointer=None):
        if 'maximum' in self.attrs:
            m = self.attrs['maximum']
            if obj < m:
                return obj
            exclusive = self.attrs['exclusive_maximum']
            if not exclusive and (obj == m):
                return obj
            self.fail('Exceeded maximum', obj, pointer)
        return obj

    def validate_max_items(self, obj, pointer=None):
        if 'max_items' in self.attrs:
            count = len(obj)
            if count > self.attrs['max_items']:
                self.fail('Too many elements', obj, pointer)
        return obj

    def validate_max_length(self, obj, pointer=None):
        if 'max_length' in self.attrs:
            length = len(obj)
            if length > self.attrs['max_length']:
                self.fail('Too long', obj, pointer)
        return obj

    def validate_max_properties(self, obj, pointer=None):
        if 'max_properties' in self.attrs:
            count = len(obj)
            if count > self.attrs['max_properties']:
                self.fail('Too many properties', obj, pointer)
        return obj

    def validate_minimum(self, obj, pointer=None):
        if 'minimum' in self.attrs:
            m = self.attrs['minimum']
            if obj > m:
                return obj
            exclusive = self.attrs['exclusive_minimum']
            if not exclusive and (obj == m):
                return obj
            self.fail('Too small', obj, pointer)
        return obj

    def validate_min_items(self, obj, pointer=None):
        if 'min_items' in self.attrs:
            count = len(obj)
            if count < self.attrs['min_items']:
                self.fail('Too few elements', obj, pointer)
        return obj

    def validate_min_length(self, obj, pointer=None):
        if 'min_length' in self.attrs:
            length = len(obj)
            if length < self.attrs['min_length']:
                self.fail('Too short', obj, pointer)
        return obj

    def validate_min_properties(self, obj, pointer=None):
        if 'min_properties' in self.attrs:
            count = len(obj)
            if count < self.attrs['min_properties']:
                self.fail('Too few properties', obj, pointer)
        return obj

    def validate_multiple_of(self, obj, pointer=None):
        if 'multiple_of' in self.attrs:
            factor = Decimal(str(self.attrs['multiple_of']))
            orig = Decimal(str(obj))
            if orig % factor != 0:
                self.fail('Forbidden value', obj, pointer)
        return obj

    def validate_not(self, obj, pointer=None):
        if 'not' in self.attrs:
            try:
                validator = self.attrs['not']
                validator(obj)
            except ValidationError:
                return obj
            else:
                self.fail('Forbidden value', obj, pointer)
        return obj

    def validate_one_of(self, obj, pointer=None):
        if 'one_of' in self.attrs:
            validated = 0
            for validator in self.attrs['one_of']:
                try:
                    validated_obj = validator(obj)
                    validated += 1
                except ValidationError:
                    pass
            if not validated:
                self.fail('Validates noone', obj)
            elif validated == 1:
                return validated_obj
            else:
                self.fail('Validates more than once', obj)
        return obj

    def validate_pattern(self, obj, pointer=None):
        if 'pattern' in self.attrs:
            pattern = self.attrs['pattern']
            if re.search(pattern, obj):
                return obj
            self.fail('Forbidden value', obj, pointer)
        return obj

    def validate_properties(self, obj, pointer=None):
        validated = set()
        pending = set(obj.keys())
        response = {}

        if not obj:
            return response

        for name, validator in self.attrs['properties'].items():
            if name in obj:
                with self.catch_fail():
                    pending.discard(name)
                    obj[name] = validator(obj[name], pointer_join(pointer, name))  # noqa
                    validated.add(name)

        for pattern, validator in self.attrs['pattern_properties'].items():
            for name in sorted(obj.keys()):
                if re.search(pattern, name):
                    with self.catch_fail():
                        pending.discard(name)
                        obj[name] = validator(obj[name], pointer_join(pointer, name))  # noqa
                        validated.add(name)

        if not pending:
            return obj

        additionals = self.attrs['additional_properties']
        if additionals is True:
            return obj

        if additionals is False:
            for name in pending:
                self.fail('Forbidden property', obj, pointer_join(pointer, name))  # noqa
            return obj

        validator = additionals
        for name in sorted(pending):
            obj[name] = validator(obj.pop(name), pointer_join(pointer, name))  # noqa
            validated.add(name)
        return obj

    def validate_required(self, obj, pointer=None):
        if 'required' in self.attrs:
            for name in self.attrs['required']:
                if name not in obj:
                    self.fail('Missing property', obj, pointer_join(pointer, name))  # noqa
        return obj

    def validate_type(self, obj, pointer=None):
        if 'type' in self.attrs:
            types = self.attrs['type']
            if isinstance(types, string_types):
                types = [types]

            for t in types:
                if t == 'array' and self.is_array(obj):
                    return obj
                if t == 'boolean' and self.is_boolean(obj):
                    return obj
                if t == 'integer' and self.is_integer(obj):
                    return obj
                if t == 'number' and self.is_number(obj):
                    return obj
                if t == 'null' and obj is None:
                    return obj
                if t == 'object' and self.is_object(obj):
                    return obj
                if t == 'string' and self.is_string(obj):
                    return obj

            self.fail('Wrong type', obj, pointer)
        return obj

    def validate_unique_items(self, obj, pointer=None):
        if self.attrs.get('unique_items'):
            if len(obj) > len(set(json.dumps(element) for element in obj)):
                self.fail('Elements must be unique', obj, pointer)
        return obj

    def is_optional(self):
        """
        Returns True, beceause it is meaningless in draft04.
        """
        logger.warn('asking for is_optional')
        return True

    def fail(self, reason, obj, pointer=None):
        """
        Called when validation fails.
        """
        pointer = pointer_join(pointer)
        err = ValidationError(reason, obj, pointer)
        if self.fail_fast:
            raise err
        else:
            self.errors.append(err)
        return err

    def catch_fail(self):
        return FailCatcher(self)


class FailCatcher(object):
    def __init__(self, validator):
        self.validator = validator

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        if isinstance(value, ValidationError) and not self.validator.fail_fast:
            self.validator.errors.append(value)
            return True
        return False
