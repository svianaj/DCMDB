"""
Provide overall functionality including dcmdb.catalog_freeze()
"""

import argparse
import sys
from argparse import ArgumentParser as ArgumentParserBase
from argparse import RawDescriptionHelpFormatter, _HelpAction
from importlib import import_module

from .src.chase import configure_parser as configure_chase_parser


def isiterable(obj):
    # and not a string
    from collections.abc import Iterable

    return not isinstance(obj, str) and isinstance(obj, Iterable)


def add_parser_help(p: ArgumentParserBase) -> None:
    """
    So we can use consistent capitalization and periods in the help. You must
    use the add_help=False argument to ArgumentParser or add_parser to use
    this. Add this first to be consistent with the default argparse output.

    """
    p.add_argument(
        "-h",
        "--help",
        action=_HelpAction,
        help="Show this help message and exit.",
    )


class ArgumentParser(ArgumentParserBase):
    def __init__(self, *args, add_help=True, **kwargs):
        kwargs.setdefault("formatter_class", RawDescriptionHelpFormatter)
        super().__init__(*args, add_help=False, **kwargs)

        if add_help:
            add_parser_help(self)

    def _check_value(self, action, value):
        # extend to properly handle when we accept multiple choices and the default is a list
        if action.choices is not None and isiterable(value):
            for element in value:
                super()._check_value(action, element)
        else:
            super()._check_value(action, value)

    def parse_args(self, *args, override_args=None, **kwargs):
        parsed_args = super().parse_args(*args, **kwargs)
        for name, value in (override_args or {}).items():
            if value is not None and getattr(parsed_args, name, None) is None:
                setattr(parsed_args, name, value)
        return parsed_args


class _GreedySubParsersAction(argparse._SubParsersAction):
    """A custom subparser action to conditionally act as a greedy consumer.

    This is a workaround since argparse.REMAINDER does not work as expected,
    see https://github.com/python/cpython/issues/61252.
    """

    def __call__(self, parser, namespace, values, option_string=None):
        super().__call__(parser, namespace, values, option_string)

        parser = self._name_parser_map[values[0]]

        # if the parser has a greedy=True attribute we want to consume all arguments
        # i.e. all unknown args should be passed to the subcommand as is
        if getattr(parser, "greedy", False):
            try:
                unknown = getattr(namespace, argparse._UNRECOGNIZED_ARGS_ATTR)
                delattr(namespace, argparse._UNRECOGNIZED_ARGS_ATTR)
            except AttributeError:
                unknown = ()

            # underscore prefixed indicating this is not a normal argparse argument
            namespace._args = tuple(unknown)

    def _get_subactions(self):
        """Sort actions for subcommands to appear alphabetically in help blurb."""
        return sorted(self._choices_actions, key=lambda action: action.dest)


def generate_pre_parser(**kwargs) -> ArgumentParser:
    pre_parser = ArgumentParser(
        description="dcmdb is a database containing information and references to DE_330 cases.",
        **kwargs,
    )

    return pre_parser


def generate_parser(**kwargs) -> ArgumentParser:
    """Generate main parser that makes usage of subparsers depending on the given command argument."""

    parser = generate_pre_parser(**kwargs)

    sub_parsers = parser.add_subparsers(
        metavar="COMMAND",
        title="commands",
        description="The following subcommands are available.",
        dest="cmd",
        action=_GreedySubParsersAction,
        required=True,
    )

    configure_chase_parser(sub_parsers)

    return parser


def do_call(args: argparse.Namespace, parser: ArgumentParser):
    """
    Serves as the primary entry point for commands referred to in this file and for
    all registered plugin subcommands.
    """
    module_name, func_name = args.func.rsplit(".", 1)
    module = import_module(module_name)

    result = getattr(module, func_name)(args, parser)
    return result


def main(*args, **kwargs):
    args = args or sys.argv[1:]
    args = args or ["--help"]

    pre_parser = generate_pre_parser(add_help=False)
    pre_args, _ = pre_parser.parse_known_args(args)

    parser = generate_parser(add_help=True)
    args = parser.parse_args(args, namespace=pre_args)

    do_call(args, parser)
