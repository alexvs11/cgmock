#!/bin/bash
set -ex

dir=$(dirname "$0")
cd "$dir"

echo "generate mock.h from header..."
../cgmock.py --file do_test.h -- -DEXT_TYPE=int -I. > mock.h
g++ test.cpp -pthread -lgtest -lgmock -o test

echo "executing test with mock..."
./test
