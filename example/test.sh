#!/bin/bash
set -ex

dir=$(dirname "$0")
cd "$dir"

echo "generate mock.h from header..."
cat config.txt | ../cgmock.py --filter=- --file do_test.h --file do_test_another.h -- -DEXT_TYPE=int -I. > mock.h
g++ test.cpp -pthread -lgtest -lgmock -o test

echo "executing test with mock..."
./test

echo "generate mock.h and mock.cpp separately..."
../cgmock.py --filter=config.txt --file do_test.h --file do_test_another.h --gen-hpp-to-file=mock.h --gen-cpp-to-file=mock.cpp -- -DEXT_TYPE=int -I.
g++ mock.cpp test.cpp -pthread -lgtest -lgmock -o test

echo "executing test with mock..."
./test
