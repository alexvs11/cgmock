#!/usr/bin/env python3

import argparse
import clang.cindex as clang
from clang.cindex import Index

class Function:
    def __init__(self, name, signature, ret, display, args):
        self.name = name
        self.signature = signature
        self.ret = ret
        self.display = display
        self.args = args

class Parser:
    def __init__(self, file, clang_args):
        index = Index.create()
        tu = index.parse(path = file, args = clang_args)
        self.node = tu.cursor

    def getFunctions(self):
        assert self.node.kind == clang.CursorKind.TRANSLATION_UNIT
        is_function = lambda node : node.kind == clang.CursorKind.FUNCTION_DECL
        return [Function(name = _.spelling,
                         signature = _.type.spelling,
                         ret = _.result_type.spelling,
                         display = _.displayname,
                         args = [arg.type.spelling for arg in _.get_children()]) for _ in self.node.get_children() if is_function(_)]

class Mocker:
    def __init__(self, libName):
        self.libName = libName
        self.interface = "Lib{}Interface".format(libName)
        self.mockobj = "Lib{}MockObj".format(libName)
        self.fPrefix = ""

    def _functionToInterface(self, f):
        return 'virtual {} {}{} = 0;'.format(f.ret, self.fPrefix, f.display)

    def _functionToMock(self, f):
        return 'MOCK_METHOD{}({}, {});'.format(len(f.args), f.name, f.signature)

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

    def generateMockHeader(self, functions):
        for_all = lambda f : "\n".join([f(_) for _ in functions])
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
{1}Mock* {4};

//fixture to set mock object from test suite
{5}

}}

//wrappers global definitions
{6}
'''.format(self.libName, self.interface, for_all(self._functionToInterface), for_all(self._functionToMock),
           self.mockobj, self._libFixture(), for_all(self._functionToWrapper))

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--file', help='header to mock', type=str, required=True)
    argparser.add_argument('--name', help='namespace name for mocks', default='MockLib')
    argparser.add_argument('--clanglib', help='path to libclang shared library', default='/usr/lib/llvm-6.0/lib/libclang-6.0.so.1')
    argparser.add_argument('clangargs', nargs=argparse.REMAINDER, help='list of clang compile args for correct parsing')
    args = argparser.parse_args()

    clang.Config.set_library_file(args.clanglib)
    parser = Parser(args.file, list(filter(lambda arg : arg != '--', args.clangargs)))
    mocker = Mocker(args.name)

    print(mocker.generateMockHeader(parser.getFunctions()))


if __name__ == '__main__':
    main()
