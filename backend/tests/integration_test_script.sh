#!/bin/bash

# Integration Test Script for Variable Resolver
# This script runs all the test cases we've been performing manually
# Usage: ./integration_test_script.sh [BASE_URL]

BASE_URL=${1:-"http://localhost:8088/api/v1"}
TEST_PROJECT_NAME="IntegrationTest"
API_PROJECT_NAME="ApiTest"

echo "🧪 Variable Resolver Integration Tests"
echo "======================================"
echo "Base URL: $BASE_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper function to print test headers
print_test() {
    echo -e "${BLUE}📋 Test: $1${NC}"
    echo "----------------------------------------"
}

# Helper function to print success
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
    echo ""
}

# Helper function to print error
print_error() {
    echo -e "${RED}❌ $1${NC}"
    echo ""
}

# Helper function to print info
print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Helper function to extract project ID from response
extract_project_id() {
    echo "$1" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data['id'])" 2>/dev/null
}

# Helper function to extract variable ID from response
extract_variable_id() {
    echo "$1" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data['id'])" 2>/dev/null
}

# Helper function to pretty print JSON
pretty_json() {
    echo "$1" | python3 -m json.tool 2>/dev/null || echo "$1"
}

# Clean up function
cleanup() {
    print_info "Cleaning up test data..."
    
    # Get project IDs
    PROJECTS=$(curl -s "$BASE_URL/projects/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for project in data.get('projects', []):
        if project['name'] in ['$TEST_PROJECT_NAME', '$API_PROJECT_NAME']:
            print(project['id'])
except:
    pass
" 2>/dev/null)
    
    # Delete test projects (this will cascade delete variables)
    for PROJECT_ID in $PROJECTS; do
        if [ ! -z "$PROJECT_ID" ]; then
            curl -s -X DELETE "$BASE_URL/projects/$PROJECT_ID" > /dev/null
            print_info "Deleted project ID: $PROJECT_ID"
        fi
    done
}

# Setup function
setup() {
    print_test "Setup - Creating Test Projects and Variables"
    
    # Create test project
    RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"name\":\"$TEST_PROJECT_NAME\",\"description\":\"Integration test project\"}" \
        "$BASE_URL/projects/")
    
    TEST_PROJECT_ID=$(extract_project_id "$RESPONSE")
    if [ -z "$TEST_PROJECT_ID" ]; then
        print_error "Failed to create test project"
        echo "Response: $(pretty_json "$RESPONSE")"
        exit 1
    fi
    print_success "Created test project (ID: $TEST_PROJECT_ID)"
    
    # Create API project
    RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"name\":\"$API_PROJECT_NAME\",\"description\":\"API project for linking\"}" \
        "$BASE_URL/projects/")
    
    API_PROJECT_ID=$(extract_project_id "$RESPONSE")
    if [ -z "$API_PROJECT_ID" ]; then
        print_error "Failed to create API project"
        echo "Response: $(pretty_json "$RESPONSE")"
        exit 1
    fi
    print_success "Created API project (ID: $API_PROJECT_ID)"
    
    # Create raw variable in test project
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"testvar1\",\"raw_value\":\"value1\",\"description\":\"Raw test variable\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created raw variable: testvar1"
    
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"testvar2\",\"raw_value\":\"value2\",\"description\":\"Raw test variable 2\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created raw variable: testvar2"
    
    # Create API variable
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$API_PROJECT_ID,\"name\":\"API_VERSION\",\"raw_value\":\"v1\",\"description\":\"API version\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created API variable: API_VERSION"
    
    # Create linked variable
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"test_link\",\"linked_to\":\"$API_PROJECT_NAME:API_VERSION\",\"description\":\"Linked test variable\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created linked variable: test_link"
    
    echo ""
}

# Test concatenated variables with different separators
test_concatenated_variables() {
    print_test "Concatenated Variables - Separator Preservation"
    
    # Test 1: Pipe separator
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"concat_pipe\",\"concat_parts\":\"\\\"$TEST_PROJECT_NAME:testvar1\\\"|\\\"$TEST_PROJECT_NAME:testvar2\\\"\",\"description\":\"Pipe separator test\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created concat_pipe variable"
    
    # Test 2: Dash separator
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"concat_dash\",\"concat_parts\":\"\\\"$TEST_PROJECT_NAME:testvar1\\\"-\\\"$TEST_PROJECT_NAME:testvar2\\\"\",\"description\":\"Dash separator test\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created concat_dash variable"
    
    # Test 3: Underscore separator
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"concat_underscore\",\"concat_parts\":\"\\\"$TEST_PROJECT_NAME:testvar1\\\"_\\\"$TEST_PROJECT_NAME:testvar2\\\"\",\"description\":\"Underscore separator test\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created concat_underscore variable"
    
    # Test 4: Space separator
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"concat_space\",\"concat_parts\":\"\\\"$TEST_PROJECT_NAME:testvar1\\\" \\\"$TEST_PROJECT_NAME:testvar2\\\"\",\"description\":\"Space separator test\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created concat_space variable"
    
    # Test 5: Complex separator
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"concat_complex\",\"concat_parts\":\"\\\"$TEST_PROJECT_NAME:testvar1\\\"_-_\\\"$TEST_PROJECT_NAME:testvar2\\\"\",\"description\":\"Complex separator test\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created concat_complex variable"
    
    echo ""
}

# Test mixed variable types
test_mixed_variables() {
    print_test "Mixed Variable Types - Linked + Raw"
    
    # Test mixed linked and raw
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"concat_mixed\",\"concat_parts\":\"\\\"$TEST_PROJECT_NAME:test_link\\\"-\\\"$TEST_PROJECT_NAME:testvar1\\\"\",\"description\":\"Mixed linked and raw\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created concat_mixed variable (linked + raw)"
    
    # Test repeated variable
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"concat_repeat\",\"concat_parts\":\"\\\"$TEST_PROJECT_NAME:testvar1\\\"|\\\"$TEST_PROJECT_NAME:testvar1\\\"\",\"description\":\"Same variable repeated\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created concat_repeat variable (same var repeated)"
    
    # Test single variable
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"concat_single\",\"concat_parts\":\"\\\"$TEST_PROJECT_NAME:testvar1\\\"\",\"description\":\"Single variable\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created concat_single variable"
    
    echo ""
}

# Test backward compatibility
test_backward_compatibility() {
    print_test "Backward Compatibility - Old Format"
    
    # Test old format (without quotes)
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"old_format\",\"concat_parts\":\"$TEST_PROJECT_NAME:testvar1|$TEST_PROJECT_NAME:testvar2\",\"description\":\"Old format test\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_success "Created old_format variable (backward compatibility)"
    
    echo ""
}

# Test resolution
test_resolution() {
    print_test "Variable Resolution - All Types"
    
    RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID}" \
        "$BASE_URL/env-vars/resolve")
    
    echo "Resolution Response:"
    pretty_json "$RESPONSE"
    echo ""
    
    # Validate expected results
    echo "Expected Results Validation:"
    echo "----------------------------"
    
    # Extract resolved values
    RESOLVED=$(echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    resolved = data.get('resolved_values', {})
    
    # Test cases
    tests = [
        ('testvar1', 'value1', 'Raw variable'),
        ('testvar2', 'value2', 'Raw variable'),
        ('test_link', 'v1', 'Linked variable'),
        ('concat_pipe', 'value1|value2', 'Pipe separator'),
        ('concat_dash', 'value1-value2', 'Dash separator'), 
        ('concat_underscore', 'value1_value2', 'Underscore separator'),
        ('concat_space', 'value1 value2', 'Space separator'),
        ('concat_complex', 'value1_-_value2', 'Complex separator'),
        ('concat_mixed', 'v1-value1', 'Mixed linked+raw'),
        ('concat_repeat', 'value1|value1', 'Repeated variable'),
        ('concat_single', 'value1', 'Single variable'),
        ('old_format', 'value1value2', 'Old format (no separator)')
    ]
    
    for var_name, expected, description in tests:
        actual = resolved.get(var_name)
        status = '✅' if actual == expected else '❌'
        print(f'{status} {var_name}: {actual} (expected: {expected}) - {description}')
        
except Exception as e:
    print(f'Error parsing response: {e}')
    print(f'Raw response: {sys.stdin.read()}')
" 2>/dev/null)
    
    echo "$RESOLVED"
    echo ""
}

# Test error cases
test_error_cases() {
    print_test "Error Handling"
    
    # Test non-existent project
    RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"error_project\",\"concat_parts\":\"\\\"NonExistent:var\\\"|\\\"$TEST_PROJECT_NAME:testvar1\\\"\",\"description\":\"Error test - bad project\"}" \
        "$BASE_URL/env-vars/")
    
    if echo "$RESPONSE" | grep -q "error\|Error"; then
        print_success "Correctly rejected non-existent project reference"
    else
        print_info "Variable created, will fail on resolution"
    fi
    
    # Test non-existent variable  
    curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID,\"name\":\"error_variable\",\"concat_parts\":\"\\\"$TEST_PROJECT_NAME:nonexistent\\\"|\\\"$TEST_PROJECT_NAME:testvar1\\\"\",\"description\":\"Error test - bad variable\"}" \
        "$BASE_URL/env-vars/" > /dev/null
    print_info "Created variable with non-existent reference (will fail on resolution)"
    
    # Test resolution with errors
    RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" \
        -d "{\"project_id\":$TEST_PROJECT_ID}" \
        "$BASE_URL/env-vars/resolve")
    
    echo "Resolution with errors:"
    pretty_json "$RESPONSE"
    echo ""
}

# Test variable listing
test_variable_listing() {
    print_test "Variable Listing - Show Values Integration"
    
    RESPONSE=$(curl -s "$BASE_URL/env-vars/?project_id=$TEST_PROJECT_ID")
    
    echo "All Variables in Test Project:"
    echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    variables = data.get('variables', [])
    
    print(f'Total variables: {len(variables)}')
    print()
    
    for var in variables:
        name = var.get('name', 'Unknown')
        var_type = var.get('value_type', 'unknown')
        
        if var_type == 'raw':
            value = var.get('raw_value', '')
        elif var_type == 'linked':
            value = f\"→ {var.get('linked_to', '')}\"
        elif var_type == 'concatenated':
            value = var.get('concat_parts', '')
        else:
            value = 'Unknown type'
            
        print(f'{name:20} | {var_type:12} | {value}')
        
except Exception as e:
    print(f'Error: {e}')
" 2>/dev/null
    
    echo ""
}

# Main execution
main() {
    echo "Starting integration tests..."
    echo ""
    
    # Cleanup any existing test data
    cleanup
    
    # Run tests
    setup
    test_concatenated_variables
    test_mixed_variables  
    test_backward_compatibility
    test_variable_listing
    test_resolution
    test_error_cases
    
    print_test "Test Summary"
    print_success "All integration tests completed!"
    print_info "Check the output above for any failures"
    
    # Optionally cleanup (comment out to keep test data)
    # cleanup
}

# Check if script is being run directly
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi 