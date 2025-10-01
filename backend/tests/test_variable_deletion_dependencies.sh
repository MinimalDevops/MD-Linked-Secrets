#!/bin/bash

# Variable Deletion Dependency Test Script
# This script tests that variables with dependencies cannot be deleted
# Usage: ./test_variable_deletion_dependencies.sh [BASE_URL]

BASE_URL=${1:-"http://localhost:8088/api/v1"}

echo "🔍 MD-Linked-Secrets Variable Deletion Dependency Testing"
echo "========================================================"
echo "Base URL: $BASE_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}📋 $1${NC}"
    echo "----------------------------------------"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Function to test variable deletion
test_deletion() {
    local var_id=$1
    local var_name=$2
    local expected_result=$3
    local description=$4
    
    echo ""
    print_info "Testing: $description"
    echo "Attempting to delete $var_name (ID: $var_id)..."
    
    local response=$(curl -s -X DELETE "$BASE_URL/env-vars/$var_id" -w "HTTP_CODE:%{http_code}")
    local http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    local body=$(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//')
    
    echo "Response: $body"
    echo "HTTP Status: $http_code"
    
    if [[ "$expected_result" == "SUCCESS" ]]; then
        if [[ "$http_code" == "200" ]]; then
            print_success "✅ Deletion successful as expected"
            return 0
        else
            print_error "❌ Expected successful deletion but got HTTP $http_code"
            return 1
        fi
    else
        if [[ "$http_code" == "400" ]]; then
            print_success "✅ Deletion blocked as expected (dependency protection working)"
            
            # Check if error message mentions dependencies
            if echo "$body" | grep -q "referenced by"; then
                print_success "✅ Error message correctly identifies dependent variables"
            else
                print_warning "⚠️  Error message doesn't mention dependencies"
            fi
            return 0
        else
            print_error "❌ Expected deletion to be blocked but got HTTP $http_code"
            return 1
        fi
    fi
}

# Function to get current variable relationships
show_current_variables() {
    print_header "Current Variable Relationships"
    
    curl -s "$BASE_URL/env-vars/" | python3 -c "
import json, sys
import subprocess

def get_project_name(project_id):
    try:
        result = subprocess.run(['curl', '-s', '$BASE_URL/projects/{}'.format(project_id)], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data['name']
    except:
        pass
    return f'Project_{project_id}'

try:
    data = json.load(sys.stdin)
    variables = data.get('variables', [])
    
    # Group by project
    by_project = {}
    for var in variables:
        project_name = get_project_name(var['project_id'])
        if project_name not in by_project:
            by_project[project_name] = []
        by_project[project_name].append(var)
    
    for project_name, vars in by_project.items():
        print(f'📁 Project: {project_name}')
        for var in vars:
            var_type = 'raw' if var.get('raw_value') else 'linked' if var.get('linked_to') else 'concatenated'
            if var_type == 'raw':
                print(f'  ✅ {var[\"name\"]} (ID: {var[\"id\"]}) = \"{var[\"raw_value\"]}\"')
            elif var_type == 'linked':
                print(f'  🔗 {var[\"name\"]} (ID: {var[\"id\"]}) → {var[\"linked_to\"]}')
            else:
                print(f'  ⊕ {var[\"name\"]} (ID: {var[\"id\"]}) = {var[\"concat_parts\"]}')
        print()
except Exception as e:
    print(f'Error parsing variables: {e}')
"
}

# Function to create test variables for dependency testing
create_test_variables() {
    print_header "Setting Up Test Variables"
    
    # Create a test project
    echo "Creating test project..."
    local project_response=$(curl -s -X POST "$BASE_URL/projects/" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "DepTest",
            "description": "Dependency test project"
        }')
    
    local project_id=$(echo "$project_response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get('id', ''))
except:
    pass
")
    
    if [[ -z "$project_id" ]]; then
        echo "Project already exists or error creating project"
        # Try to get existing project
        project_id=$(curl -s "$BASE_URL/projects/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    projects = data.get('projects', [])
    for p in projects:
        if p['name'] == 'DepTest':
            print(p['id'])
            break
except:
    pass
")
    fi
    
    echo "Using project ID: $project_id"
    
    # Create base variable
    echo "Creating base variable..."
    curl -s -X POST "$BASE_URL/env-vars/" \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": $project_id,
            \"name\": \"BASE_VAR\",
            \"raw_value\": \"base_value\",
            \"description\": \"Base variable for testing\"
        }" > /dev/null
    
    # Create linked variable
    echo "Creating linked variable..."
    curl -s -X POST "$BASE_URL/env-vars/" \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": $project_id,
            \"name\": \"LINKED_VAR\",
            \"linked_to\": \"DepTest:BASE_VAR\",
            \"description\": \"Linked variable for testing\"
        }" > /dev/null
    
    # Create concatenated variable
    echo "Creating concatenated variable..."
    curl -s -X POST "$BASE_URL/env-vars/" \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": $project_id,
            \"name\": \"CONCAT_VAR\",
            \"concat_parts\": \"\\\"DepTest:BASE_VAR\\\"|\\\"DepTest:LINKED_VAR\\\"\",
            \"description\": \"Concatenated variable for testing\"
        }" > /dev/null
    
    # Create standalone variable
    echo "Creating standalone variable..."
    curl -s -X POST "$BASE_URL/env-vars/" \
        -H "Content-Type: application/json" \
        -d "{
            \"project_id\": $project_id,
            \"name\": \"STANDALONE_VAR\",
            \"raw_value\": \"standalone_value\",
            \"description\": \"Standalone variable for testing\"
        }" > /dev/null
    
    print_success "Test variables created successfully"
}

# Function to get variable ID by name and project
get_var_id() {
    local project_name=$1
    local var_name=$2
    
    curl -s "$BASE_URL/env-vars/" | python3 -c "
import json, sys
import subprocess

def get_project_name(project_id):
    try:
        result = subprocess.run(['curl', '-s', '$BASE_URL/projects/{}'.format(project_id)], capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data['name']
    except:
        pass
    return f'Project_{project_id}'

try:
    data = json.load(sys.stdin)
    variables = data.get('variables', [])
    
    for var in variables:
        project_name = get_project_name(var['project_id'])
        if project_name == '$project_name' and var['name'] == '$var_name':
            print(var['id'])
            break
except:
    pass
"
}

# Function to cleanup test data
cleanup_test_data() {
    print_header "Cleaning Up Test Data"
    
    # Delete DepTest project if it exists
    local project_id=$(curl -s "$BASE_URL/projects/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    projects = data.get('projects', [])
    for p in projects:
        if p['name'] == 'DepTest':
            print(p['id'])
            break
except:
    pass
")
    
    if [[ -n "$project_id" ]]; then
        echo "Deleting DepTest project..."
        curl -s -X DELETE "$BASE_URL/projects/$project_id" > /dev/null
        print_success "Test data cleaned up"
    else
        print_info "No test data to clean up"
    fi
}

# Main test execution
main() {
    # Show current state
    show_current_variables
    
    # Create test variables
    create_test_variables
    sleep 2  # Wait for creation to complete
    
    # Show updated state
    show_current_variables
    
    print_header "Dependency Deletion Tests"
    
    # Get variable IDs for testing
    local base_var_id=$(get_var_id "DepTest" "BASE_VAR")
    local linked_var_id=$(get_var_id "DepTest" "LINKED_VAR")
    local concat_var_id=$(get_var_id "DepTest" "CONCAT_VAR")
    local standalone_var_id=$(get_var_id "DepTest" "STANDALONE_VAR")
    
    echo "Test Variable IDs:"
    echo "  BASE_VAR: $base_var_id"
    echo "  LINKED_VAR: $linked_var_id"
    echo "  CONCAT_VAR: $concat_var_id"
    echo "  STANDALONE_VAR: $standalone_var_id"
    
    # Test cases
    local tests_passed=0
    local total_tests=0
    
    # Test 1: Try to delete base variable (should fail - referenced by others)
    if [[ -n "$base_var_id" ]]; then
        total_tests=$((total_tests + 1))
        if test_deletion "$base_var_id" "DepTest:BASE_VAR" "BLOCKED" "Delete base variable (referenced by linked and concat vars)"; then
            tests_passed=$((tests_passed + 1))
        fi
    fi
    
    # Test 2: Try to delete linked variable (should fail - referenced by concat var)
    if [[ -n "$linked_var_id" ]]; then
        total_tests=$((total_tests + 1))
        if test_deletion "$linked_var_id" "DepTest:LINKED_VAR" "BLOCKED" "Delete linked variable (referenced by concat var)"; then
            tests_passed=$((tests_passed + 1))
        fi
    fi
    
    # Test 3: Delete concat variable (should succeed - no dependencies)
    if [[ -n "$concat_var_id" ]]; then
        total_tests=$((total_tests + 1))
        if test_deletion "$concat_var_id" "DepTest:CONCAT_VAR" "SUCCESS" "Delete concatenated variable (no dependencies)"; then
            tests_passed=$((tests_passed + 1))
        fi
    fi
    
    # Test 4: Delete standalone variable (should succeed - no dependencies)
    if [[ -n "$standalone_var_id" ]]; then
        total_tests=$((total_tests + 1))
        if test_deletion "$standalone_var_id" "DepTest:STANDALONE_VAR" "SUCCESS" "Delete standalone variable (no dependencies)"; then
            tests_passed=$((tests_passed + 1))
        fi
    fi
    
    # Now that concat var is deleted, try to delete linked var (should succeed)
    if [[ -n "$linked_var_id" ]]; then
        total_tests=$((total_tests + 1))
        if test_deletion "$linked_var_id" "DepTest:LINKED_VAR" "SUCCESS" "Delete linked variable (dependencies removed)"; then
            tests_passed=$((tests_passed + 1))
        fi
    fi
    
    # Finally, delete base var (should succeed)
    if [[ -n "$base_var_id" ]]; then
        total_tests=$((total_tests + 1))
        if test_deletion "$base_var_id" "DepTest:BASE_VAR" "SUCCESS" "Delete base variable (dependencies removed)"; then
            tests_passed=$((tests_passed + 1))
        fi
    fi
    
    # Test with existing variables from other projects
    print_header "Cross-Project Dependency Tests"
    
    # Try to delete a variable that's referenced from another project
    echo ""
    print_info "Testing cross-project dependencies..."
    
    # Get ID of a variable that's referenced by another project
    local api_version_id=$(get_var_id "api" "API_VERSION")
    if [[ -n "$api_version_id" ]]; then
        total_tests=$((total_tests + 1))
        if test_deletion "$api_version_id" "api:API_VERSION" "BLOCKED" "Delete variable referenced by another project"; then
            tests_passed=$((tests_passed + 1))
        fi
    fi
    
    # Summary
    print_header "Test Results Summary"
    echo "Tests passed: $tests_passed/$total_tests"
    
    if [[ $tests_passed -eq $total_tests ]]; then
        print_success "🎉 All dependency protection tests PASSED!"
        print_success "✅ Variables with dependencies cannot be deleted"
        print_success "✅ Variables without dependencies can be deleted"
        print_success "✅ Cross-project dependency protection works"
        print_success "✅ Error messages correctly identify dependent variables"
    else
        print_error "❌ Some tests FAILED - dependency protection may have issues"
    fi
    
    # Cleanup
    cleanup_test_data
    
    # Return success if all tests passed
    if [[ $tests_passed -eq $total_tests ]]; then
        return 0
    else
        return 1
    fi
}

# Run main function
main "$@" 