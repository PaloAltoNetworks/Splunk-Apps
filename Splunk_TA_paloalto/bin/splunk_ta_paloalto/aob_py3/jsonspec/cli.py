"""
    jsonspec.cli
    ~~~~~~~~~~~~

"""


from __future__ import print_function

import argparse
import logging
import os
import stat
import sys
import pkg_resources
from functools import wraps
from jsonspec import driver
from textwrap import dedent

try:
    from termcolor import colored
except ImportError:

    def colored(string, *args, **kwargs):
        return string


def disable_logging(func):
    return func
    """
    Temporary disable logging.
    """
    handler = logging.NullHandler()

    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger()
        logger.addHandler(handler)
        resp = func(*args, **kwargs)
        logger.removeHandler(handler)
        return resp
    return wrapper


def format_output(func):
    return func
    """
    Format output.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
        except Exception as error:
            print(colored(error, 'red'), file=sys.stderr)
            sys.exit(1)
        else:
            print(response)
            sys.exit(0)
    return wrapper


def JSONStruct(string):
    return driver.loads(string)


class JSONFile(argparse.FileType):
    def __call__(self, string):
        file = super(JSONFile, self).__call__(string)
        return driver.load(file)


def document_arguments(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--document-json',
                       type=JSONStruct,
                       help='json structure',
                       dest='document_json',
                       metavar='<doc>')
    group.add_argument('--document-file',
                       type=JSONFile('r'),
                       help='json filename',
                       dest='document_file',
                       metavar='<doc>')


def schema_arguments(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--schema-json',
                       type=JSONStruct,
                       help='json structure',
                       dest='schema_json',
                       metavar='<schema>')
    group.add_argument('--schema-file',
                       type=JSONFile('r'),
                       help='json filename',
                       dest='schema_file',
                       metavar='<schema>')


def fragment_arguments(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--fragment-json',
                       type=JSONStruct,
                       help='json structure',
                       dest='fragment_json',
                       metavar='<fragment>')
    group.add_argument('--fragment-file',
                       type=JSONFile('r'),
                       help='json filename',
                       dest='fragment_file',
                       metavar='<fragment>')


def indentation_arguments(parser):
    parser.add_argument('--indent',
                        type=int,
                        help='return an indented json',
                        metavar='<indentation>')


def pointer_arguments(parser):
    parser.add_argument('pointer',
                        type=str,
                        help='json pointer',
                        metavar='<pointer>')


def target_arguments(parser):
    parser.add_argument('-t', '--target-pointer',
                        help='target pointer',
                        dest='target',
                        metavar='<target>')


def parse_document(args):
    document = None
    if args.document_json:
        document = args.document_json
    elif args.document_file:
        document = args.document_file
    else:
        mode = os.fstat(0).st_mode
        if stat.S_ISFIFO(mode):
            # cat doc.json | cmd
            document = driver.load(sys.stdin)
        elif stat.S_ISREG(mode):
            # cmd < doc.json
            document = driver.load(sys.stdin)

    setattr(args, 'document', document)
    return args


def parse_fragment(args):
    setattr(args, 'fragment', args.fragment_json or args.fragment_file)
    return args


def parse_pointer(args):
    target = args.pointer
    if target.startswith('#'):
        target = target[1:]
    setattr(args, 'pointer', target)


def parse_schema(args):
    setattr(args, 'schema', args.schema_json or args.schema_file)
    return args


def parse_target(args):
    target = args.target
    if target.startswith('#'):
        target = target[1:]
    setattr(args, 'target', target)
    if not target:
        raise ValueError('target is required')


class Command(object):
    help = None
    description = None
    epilog = None

    def __init__(self, parser=None):
        self.parser = parser or argparse.ArgumentParser(
            description=self.description, epilog=self.epilog)
        self.parser.set_defaults(func=self)
        self.arguments(self.parser)

    def arguments(self, parser):
        return

    def run(self, args=None):
        raise NotImplementedError

    def parse_args(self, args):
        return self.parser.parse_args(args)

    @disable_logging
    @format_output
    def __call__(self, args=None):
        return self.run(args)


class AddCommand(Command):
    """Add a fragment to a json document.

    examples::

        %(prog)s '#/foo/1' --fragment-file=fragment.json --document-json='{"foo": ["bar", "baz"]}'
        echo '{"foo": ["bar", "baz"]}' | %(prog)s '#/foo/1' --fragment-file=fragment.json
        %(prog)s '#/foo/1' --fragment-file=fragment.json --document-file=doc.json
        %(prog)s '#/foo/1' --fragment-file=fragment.json < doc.json
    """

    help = 'add fragment to a document'

    def arguments(self, parser):
        pointer_arguments(parser)
        document_arguments(parser)
        fragment_arguments(parser)
        indentation_arguments(parser)

    def run(self, args):
        parse_pointer(args)
        parse_document(args)
        parse_fragment(args)

        from jsonspec.operations import add, Error
        from jsonspec.pointer import ParseError

        try:
            response = add(args.document, args.pointer, args.fragment)
            return driver.dumps(response, indent=args.indent)
        except Error as error:
            raise Exception(error)
        except ParseError as error:
            raise Exception('{} is not a valid pointer'.format(args.pointer))


class CheckCommand(Command):
    """Tests that a value at the target location is equal to a specified value.

    examples::

        %(prog)s '#/foo/1' --fragment-file=fragment.json --document-json='{"foo": ["bar", "baz"]}'
        echo '{"foo": ["bar", "baz"]}' | %(prog)s '#/foo/1' --fragment-file=fragment.json
        %(prog)s '#/foo/1' --fragment-file=fragment.json --document-file=doc.json
        %(prog)s '#/foo/1' --fragment-file=fragment.json < doc.json
    """

    help = 'check member of a document'

    def arguments(self, parser):
        pointer_arguments(parser)
        document_arguments(parser)
        fragment_arguments(parser)

    def run(self, args):
        parse_pointer(args)
        parse_document(args)
        parse_fragment(args)

        from jsonspec.operations import check, Error
        from jsonspec.pointer import ParseError

        try:
            if check(args.document, args.pointer, args.fragment):
                return 'It validates'
            else:
                raise Exception('It does not validate')
        except Error as error:
            raise Exception('It does not validate')
        except ParseError as error:
            raise Exception('{} is not a valid pointer'.format(args.pointer))


class CopyCommand(Command):
    """Copies the value at a specified location to the target location.

    examples::

        %(prog)s '#/foo/1' --target='#/foo/2' --document-json='{"foo": ["bar", "baz"]}'
        echo '{"foo": ["bar", "baz"]}' | %(prog)s '#/foo/1' --target='#/foo/2'
        %(prog)s '#/foo/1' --target='#/foo/2' --document-file=doc.json
        %(prog)s '#/foo/1' --target='#/foo/2' < doc.json
    """

    help = 'copy a member of a document'

    def arguments(self, parser):
        pointer_arguments(parser)
        document_arguments(parser)
        target_arguments(parser)
        indentation_arguments(parser)

    def run(self, args):
        parse_pointer(args)
        parse_document(args)
        parse_target(args)

        from jsonspec.operations import copy, Error
        from jsonspec.pointer import ParseError

        try:
            response = copy(args.document, args.target, args.pointer)
            return driver.dumps(response, indent=args.indent)
        except Error as error:
            raise Exception(error)
        except ParseError as error:
            raise Exception('{} is not a valid pointer'.format(args.pointer))


class ExtractCommand(Command):
    """Extract a fragment from a json document.

    examples::

        %(prog)s '#/foo/1' --document-json='{"foo": ["bar", "baz"]}'
        echo '{"foo": ["bar", "baz"]}' | %(prog)s '#/foo/1'
        %(prog)s '#/foo/1' --document-file=doc.json
        %(prog)s '#/foo/1' < doc.json
    """

    help = 'extract a member of a document'

    def arguments(self, parser):
        pointer_arguments(parser)
        document_arguments(parser)
        indentation_arguments(parser)

    def run(self, args):
        parse_pointer(args)
        parse_document(args)

        from jsonspec.pointer import extract
        from jsonspec.pointer import ExtractError, ParseError

        try:
            response = extract(args.document, args.pointer)
            return driver.dumps(response, indent=args.indent)
        except ExtractError:
            raise Exception(args)
            raise Exception('{} does not match'.format(args.pointer))
        except ParseError:
            raise Exception('{} is not a valid pointer'.format(args.pointer))


class MoveCommand(Command):
    """Removes the value at a specified location and adds it to the target location.

    examples::

        %(prog)s '#/foo/2' --target='#/foo/1' --document-json='{"foo": ["bar", "baz"]}'
        echo '{"foo": ["bar", "baz"]}' | %(prog)s '#/foo/2' --target='#/foo/1'
        %(prog)s '#/foo/2' --target='#/foo/1' --document-file=doc.json
        %(prog)s '#/foo/2' --target='#/foo/1' < doc.json
    """

    help = 'move a member of a document'

    def arguments(self, parser):
        pointer_arguments(parser)
        document_arguments(parser)
        target_arguments(parser)
        indentation_arguments(parser)

    def run(self, args):
        parse_pointer(args)
        parse_target(args)
        parse_document(args)

        from jsonspec.operations import move, Error
        from jsonspec.pointer import ParseError

        try:
            response = move(args.document, args.target, args.pointer)
            return driver.dumps(response, indent=args.indent)
        except Error as error:
            raise Exception(error)
        except ParseError as error:
            raise Exception('{} is not a valid pointer'.format(args.pointer))


class RemoveCommand(Command):
    """Replace the value of pointer.

    examples:
      %(prog)s '#/foo/1' --document-json='{"foo": ["bar", "baz"]}'
      echo '{"foo": ["bar", "baz"]}' | %(prog)s '#/foo/1'
      %(prog)s '#/foo/1' --document-file=doc.json
      %(prog)s '#/foo/1' < doc.json

    """

    help = 'remove a member of a document'

    def arguments(self, parser):
        pointer_arguments(parser)
        document_arguments(parser)
        indentation_arguments(parser)

    def run(self, args):
        parse_pointer(args)
        parse_document(args)

        from jsonspec.operations import remove, Error
        from jsonspec.pointer import ParseError

        try:
            response = remove(args.document, args.pointer)
            return driver.dumps(response, indent=args.indent)
        except Error:
            raise Exception('{} does not match'.format(args.pointer))
        except ParseError:
            raise Exception('{} is not a valid pointer'.format(args.pointer))


class ReplaceCommand(Command):
    """Replace a fragment to a json document.

    examples::

        %(prog)s '#/foo/1' --fragment-file=fragment.json --document-json='{"foo": ["bar", "baz"]}'
        echo '{"foo": ["bar", "baz"]}' | %(prog)s '#/foo/1' --fragment-file=fragment.json
        %(prog)s '#/foo/1' --fragment-file=fragment.json --document-file=doc.json
        %(prog)s '#/foo/1' --fragment-file=fragment.json < doc.json
    """

    help = 'replace a member of a document'

    def arguments(self, parser):
        pointer_arguments(parser)
        document_arguments(parser)
        fragment_arguments(parser)
        indentation_arguments(parser)

    def run(self, args):
        parse_pointer(args)
        parse_document(args)
        parse_fragment(args)

        from jsonspec.operations import replace, Error
        from jsonspec.pointer import ParseError

        try:
            response = replace(args.document, args.pointer, args.fragment)
            return driver.dumps(response, indent=args.indent)
        except Error as error:
            raise Exception(error)
        except ParseError as error:
            raise Exception('{} is not a valid pointer'.format(args.pointer))


class ValidateCommand(Command):
    """Validate document against a schema.

    examples::

        %(prog)s --schema-file=schema.json --document-json='{"foo": ["bar", "baz"]}'
        echo '{"foo": ["bar", "baz"]}' | %(prog)s --schema-file=schema.json
        %(prog)s --schema-file=schema.json --document-file=doc.json
        %(prog)s --schema-file=schema.json < doc.json
    """

    help = 'validate a document against a schema'

    def arguments(self, parser):
        document_arguments(parser)
        schema_arguments(parser)
        indentation_arguments(parser)

    def run(self, args):
        parse_document(args)
        parse_schema(args)

        from jsonspec.validators import load
        from jsonspec.validators import ValidationError

        try:
            validated = load(args.schema).validate(args.document)
            return driver.dumps(validated, indent=args.indent)
        except ValidationError as error:
            msg = 'document does not validate with schema.\n\n'
            for pointer, reasons in error.flatten().items():
                msg += '  {}\n'.format(pointer)
                for reason in reasons:
                    msg += '    - reason {}\n'.format(reason)
                msg += '\n'
            raise Exception(msg)


def get_parser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 0.9.11')

    subparsers = parser.add_subparsers(help='choose one of these actions',
                                       dest='action',
                                       metavar='<action>')
    subparsers.required = True
    cmds = []
    for entrypoint in pkg_resources.iter_entry_points('jsonspec.cli.commands'):
        logging.debug('loaded %s from %s', entrypoint, entrypoint.dist)
        cmds.append((entrypoint.name, entrypoint.load()))

    for name, command_class in sorted(cmds):
        description, help, epilog = None, None, None
        if command_class.__doc__:
            description, _, epilog = command_class.__doc__.lstrip().partition('\n\n')  # noqa

            if description:
                description = description.replace('\n', ' ')

            if epilog:
                epilog = dedent(epilog).replace('    ', '  ').replace('::\n\n', ':\n')  # noqa
        description = command_class.description or description
        epilog = command_class.epilog or epilog
        help = command_class.help or description
        subparser = subparsers.add_parser(name,
                                          help=help,
                                          description=description,
                                          epilog=epilog,
                                          formatter_class=argparse.RawDescriptionHelpFormatter)  # noqa

        command = command_class(subparser)  # noqa
    return parser


def main():
    logging.basicConfig()

    parser = get_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
