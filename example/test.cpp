#include "gtest/gtest.h"
#include "gmock/gmock.h"
#include "mock.h"

using ::testing::Return;
using MockLib::Fixture;

int test_function(int arg) {
    return function(arg) + sum(double(arg), arg);
}

TEST_F(Fixture, test) {
    EXPECT_CALL(mock_c, function(10)).WillOnce(Return(20));
    EXPECT_CALL(mock_c, sum(10.0, 10)).WillOnce(Return(20));
    EXPECT_EQ(test_function(10), 40);
}

int main(int argc, char **argv) {
    testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
