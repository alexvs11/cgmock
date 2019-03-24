#!/usr/bin/env python3

import argparse
import clang.cindex as clang
from clang.cindex import Index
import sys
import re

class Function:
    def __init__(self, name, signature, ret, display, args):
        self.name = name
        self.signature = signature
        self.ret = ret
        self.display = display
        self.args = args

class Parser:
    def __init__(self, file, _filter, clang_args):
        index = Index.create()
        tu = index.parse(path = file, args = clang_args)
        self.node = tu.cursor
        self.filter = _filter

    def getFunctions(self):
        assert self.node.kind == clang.CursorKind.TRANSLATION_UNIT
        is_function = lambda node : (node.kind == clang.CursorKind.FUNCTION_DECL) and self.filter.satisfy(node.spelling)
        return [Function(name = _.spelling,
                         signature = _.type.spelling,
                         ret = _.result_type.spelling,
                         display = _.displayname,
                         args = [arg.type.spelling for arg in _.get_children() if arg.is_definition()]) for _ in self.node.get_children() if is_function(_)]

class GroupParser:
    def __init__(self, files, _filter, clang_args):
        self.files = files
        self._filter = _filter
        self.clang_args = clang_args

    def getFunctions(self):
        res = []
        for _ in self.files:
            res += Parser(_, self._filter, self.clang_args).getFunctions()
        return res

class Filter:
    def __init__(self, names):
        self.names = names

    def satisfy(self, name):
        if self.names:
            return name in self.names
        else:
            return True

def FilterFromConfig(f):
    if f is not None:
        return Filter(
            list(filter(lambda s : not re.match("^(#.*|)$", s),
                        list(map(lambda s: s.rstrip(), f.readlines())))))
    else:
        return Filter([])

class Mocker:
    def __init__(self, libName, functions):
        self.libName = libName
        self.interface = "Lib{}Interface".format(libName)
        self.mockobj = "Lib{}MockObj".format(libName)
        self.fPrefix = ""
        self.functions = functions

    def _for_all(self, f):
        return "\n".join([f(_) for _ in self.functions])

    def _functionToInterface(self, f):
        return 'virtual {} {}{} = 0;'.format(f.ret, self.fPrefix, f.display)

    def _functionToMock(self, f):
        return 'MOCK_METHOD{}({}, {});'.format(len(f.args), f.name, f.signature)

    def _functionToDeclaration(self, f):
        return 'extern "C" {} {};'.format(f.ret, f.display)

    def _functionToWrapper(self, f):
        wrapper_args = ", ".join(["{} _{}".format(type, i) for i, type in enumerate(f.args)]) # [int, double] -> int _1, double _2
        args = ", ".join("_{}".format(i) for i,_ in enumerate(f.args)) # [int, double] -> _1, _2
        return_str = 'return' if f.ret != 'void' else ''

        return '''
extern "C" {} {}({})
{{
    {} {}::{}->{}{}({});
}}'''.format(f.ret, f.name, wrapper_args, return_str, self.libName, self.mockobj, self.fPrefix, f.name, args)

    def _libFixture(self):
        return '''
class Fixture : public testing::Test {{
protected:
    void SetUp() override {{ {0} = &mock_c; }}
    void TearDown() override {{ }}
    {1}Mock mock_c;
}};'''.format(self.mockobj, self.interface)

    def generateMockHeader(self):
        return '''
#pragma once
#include "gtest/gtest.h"
#include "gmock/gmock.h"

namespace {0} {{

class {1} {{
public:
   virtual ~{1}() {{}}
{2}
}};

class {1}Mock : public {1} {{
public:
   virtual ~{1}Mock() {{}}
{3}
}};

//that object should be set from test's fixture
extern {1}Mock* {4};

//fixture to set mock object from test suite
{5}

}}

//forward declaration for wrappers
{6}
'''.format(self.libName, self.interface, self._for_all(self._functionToInterface),
           self._for_all(self._functionToMock), self.mockobj, self._libFixture(), self._for_all(self._functionToDeclaration))

    def generateMockDefinitions(self, headerName=None):
        header = '#include "{}"'.format(headerName) if headerName else '//headerless'
        return '''{0}
//mock obj definition
{1}::{2}Mock* {1}::{3} = nullptr;
{4}
//wrappers global definitions
'''.format(header, self.libName, self.interface, self.mockobj, self._for_all(self._functionToWrapper))

def write(mocker, hpp=None, cpp=None):
    fileToWrite = lambda f: open(f, mode='w') if f else sys.stdout
    fileToWrite(hpp).write(mocker.generateMockHeader())
    fileToWrite(cpp).write(mocker.generateMockDefinitions(hpp))

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--file', help='header to mock. If specified several times then several headers will be parsed', action='append', type=str, required=True)
    argparser.add_argument('--name', help='namespace name for mocks', default='MockLib')
    argparser.add_argument('--filter', help='''filepath to a file with full names of C functions which should be mocked.
#-started lines are ignored.
If - specified instead of file name then stdin will be used.
If not specified then mocks will be generated for all functions''')
    argparser.add_argument('--gen-hpp-to-file', help='write header to a specified file', default=None)
    argparser.add_argument('--gen-cpp-to-file', help='write definitions part to file', default=None)

    argparser.add_argument('--clanglib', help='path to libclang shared library', default='/usr/lib/llvm-6.0/lib/libclang-6.0.so.1')
    argparser.add_argument('clangargs', nargs=argparse.REMAINDER, help='list of clang compile args for correct parsing')
    args = argparser.parse_args()
    clang.Config.set_library_file(args.clanglib)

    if bool(args.gen_hpp_to_file) ^ bool(args.gen_cpp_to_file):
        assert not "only both or none of arguments cpp/hpp can be specified"
    if not args.filter:
        config = None
    elif args.filter == '-':
        config = sys.stdin
    else:
        config = open(args.filter)

    _filter = FilterFromConfig(config)
    parser = GroupParser(args.file, _filter, list(filter(lambda arg : arg != '--', args.clangargs)))
    mocker = Mocker(args.name, parser.getFunctions())
    write(mocker, hpp=args.gen_hpp_to_file, cpp=args.gen_cpp_to_file)


if __name__ == '__main__':
    main()
