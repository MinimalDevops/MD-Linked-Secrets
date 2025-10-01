#!/bin/bash

echo "🧪 Testing CLI Prefix/Suffix Fix"
echo "================================="

# Test 1: No prefix/suffix
echo "Test 1: No prefix/suffix"
secretool export --project Test --dry-run | grep -A5 "Variables for project"

echo -e "\nTest 2: Prefix only"
secretool export --project Test --prefix "APP_" --dry-run | grep -A5 "Variables for project"

echo -e "\nTest 3: Suffix only"
secretool export --project Test --suffix "_ENV" --dry-run | grep -A5 "Variables for project"

echo -e "\nTest 4: Both prefix and suffix"
secretool export --project Test --prefix "WEBAPP_" --suffix "_PROD" --dry-run | grep -A5 "Variables for project"

echo -e "\n✅ All tests completed!"
echo -e "\nExpected results:"
echo "Test 1: testvar1, test_link, test_con"
echo "Test 2: APP_testvar1, APP_test_link, APP_test_con"
echo "Test 3: testvar1_ENV, test_link_ENV, test_con_ENV"
echo "Test 4: WEBAPP_testvar1_PROD, WEBAPP_test_link_PROD, WEBAPP_test_con_PROD" 