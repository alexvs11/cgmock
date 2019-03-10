# CGMOCK #

Generates usable google test mocks for C code using C headers.
C headers are parsed using libclang so potentially can work with headers
of any complixity, with dependencies etc.

## INSTALLATION ##

You'll need libclang and python clang module of corresponding versions.
For ubuntu 18.04 it will be:

```
sudo apt-get install -y libclang1-6.0 python3-pip
pip3 install clang==6.0.0.2
```
  
Or using docker:

```
docker build --network host -t cgmock .
docker run --rm -it -v `pwd`:`pwd` --workdir `pwd` cgmock ./cgmock.py --file example/do_test.h> mock.h
```

## HOW-TO ##

Take a look at example/test.cpp:


```
int test_function(int arg) {
    return function(arg) + sum(double(arg), arg);
}
```

It uses two functions declared at do_test.h:

```
#if !defined(EXT_TYPE)
#define EXT_TYPE int
#endif


int function(int)
int sum(double, EXT_TYPE);
```
Here is a demonstration how it works:
  
```
docker run --rm -it -v `pwd`:`pwd` --workdir `pwd` cgmock bash ./example/test.sh
++ dirname ./example/test.sh
+ dir=./example
+ cd ./example
+ echo 'generate mock.h from header...'
generate mock.h from header...
+ ../cgmock.py --file do_test.h -- -DEXT_TYPE=int -I.
+ g++ test.cpp -pthread -lgtest -lgmock -o test
+ echo 'executing test with mock...'
executing test with mock...
+ ./test
[==========] Running 1 test from 1 test suite.
[----------] Global test environment set-up.
[----------] 1 test from Fixture
[ RUN      ] Fixture.test
[       OK ] Fixture.test (0 ms)
[----------] 1 test from Fixture (0 ms total)

[----------] Global test environment tear-down
[==========] 1 test from 1 test suite ran. (0 ms total)
[  PASSED  ] 1 test.
```
    
## INFO ##

Inspired by:
* [gmock.py](https://github.com/cpp-testing/gmock.py)
* This answer <https://stackoverflow.com/a/32274666>
