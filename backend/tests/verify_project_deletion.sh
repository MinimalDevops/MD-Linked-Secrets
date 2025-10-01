#!/bin/bash

# Project Deletion Verification Script
# This script verifies that when a project is deleted, all related data is properly cleaned up
# Usage: ./verify_project_deletion.sh [BASE_URL] [PROJECT_NAME]

BASE_URL=${1:-"http://localhost:8088/api/v1"}
PROJECT_NAME=${2}

echo "🔍 MD-Linked-Secrets Project Deletion Verification"
echo "=================================================="
echo "Base URL: $BASE_URL"
echo "Target Project: ${PROJECT_NAME:-'[Will be prompted]'}"
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

# Function to get all current projects
get_all_projects() {
    curl -s "$BASE_URL/projects/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    projects = data.get('projects', [])
    for project in projects:
        print(f'{project[\"id\"]}:{project[\"name\"]}:{project[\"description\"]}')
except Exception as e:
    print(f'ERROR:{e}')
"
}

# Function to check if project exists
check_project_exists() {
    local project_name=$1
    curl -s "$BASE_URL/projects/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    projects = data.get('projects', [])
    exists = any(p['name'] == '$project_name' for p in projects)
    if exists:
        project = next(p for p in projects if p['name'] == '$project_name')
        print(f'{project[\"id\"]}:{project[\"name\"]}:{project[\"description\"]}')
    else:
        print('NOT_FOUND')
except Exception as e:
    print(f'ERROR:{e}')
"
}

# Function to verify deletion cleanup
verify_deletion_cleanup() {
    local project_name=$1
    local project_id=$2
    
    print_header "Verifying Deletion Cleanup for '$project_name' (ID: $project_id)"
    
    # Get list of valid project IDs for orphan detection
    local valid_project_ids=$(curl -s "$BASE_URL/projects/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    projects = data.get('projects', [])
    ids = [str(p['id']) for p in projects]
    print(','.join(ids))
except:
    print('')
")
    
    echo "Valid project IDs: [$valid_project_ids]"
    echo ""
    
    # 1. Check if project still exists
    echo "1. Project Existence Check:"
    local project_check=$(check_project_exists "$project_name")
    if [[ "$project_check" == "NOT_FOUND" ]]; then
        print_success "Project '$project_name' successfully deleted from projects table"
    else
        print_error "Project '$project_name' still exists: $project_check"
        return 1
    fi
    echo ""
    
    # 2. Check for orphaned environment variables
    echo "2. Environment Variables Cleanup Check:"
    local orphaned_vars=$(curl -s "$BASE_URL/env-vars/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    variables = data.get('variables', [])
    valid_ids = ['$valid_project_ids'.replace(',', \"','\").split(\"','\") if '$valid_project_ids' else []]
    valid_ids = [int(id) for id in valid_ids if id.strip()]
    
    # Check for variables with the deleted project ID
    deleted_project_vars = [v for v in variables if v['project_id'] == $project_id]
    
    # Check for orphaned variables (project_id not in valid list)
    orphaned_vars = [v for v in variables if v['project_id'] not in valid_ids]
    
    print(f'DELETED_PROJECT_VARS:{len(deleted_project_vars)}')
    print(f'ORPHANED_VARS:{len(orphaned_vars)}')
    
    if deleted_project_vars:
        print('VARS_FOUND:')
        for var in deleted_project_vars:
            print(f'  - {var[\"name\"]} (ID: {var[\"id\"]})')
    
    if orphaned_vars:
        print('ORPHANED_FOUND:')
        for var in orphaned_vars:
            print(f'  - {var[\"name\"]} (Project ID: {var[\"project_id\"]}, Var ID: {var[\"id\"]})')
            
except Exception as e:
    print(f'ERROR:{e}')
")
    
    local deleted_vars=$(echo "$orphaned_vars" | grep "DELETED_PROJECT_VARS:" | cut -d: -f2)
    local orphaned_count=$(echo "$orphaned_vars" | grep "ORPHANED_VARS:" | cut -d: -f2)
    
    if [[ "$deleted_vars" == "0" ]]; then
        print_success "No environment variables found for deleted project"
    else
        print_error "$deleted_vars environment variables still exist for deleted project"
        echo "$orphaned_vars" | grep -A 10 "VARS_FOUND:"
    fi
    
    if [[ "$orphaned_count" == "0" ]]; then
        print_success "No orphaned environment variables found"
    else
        print_warning "$orphaned_count orphaned environment variables found"
        echo "$orphaned_vars" | grep -A 10 "ORPHANED_FOUND:"
    fi
    echo ""
    
    # 3. Check for orphaned export records
    echo "3. Export Records Cleanup Check:"
    local orphaned_exports=$(curl -s "$BASE_URL/exports/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    exports = data.get('exports', [])
    valid_ids = ['$valid_project_ids'.replace(',', \"','\").split(\"','\") if '$valid_project_ids' else []]
    valid_ids = [int(id) for id in valid_ids if id.strip()]
    
    # Check for exports with the deleted project ID
    deleted_project_exports = [e for e in exports if e['project_id'] == $project_id]
    
    # Check for orphaned exports
    orphaned_exports = [e for e in exports if e['project_id'] not in valid_ids]
    
    print(f'DELETED_PROJECT_EXPORTS:{len(deleted_project_exports)}')
    print(f'ORPHANED_EXPORTS:{len(orphaned_exports)}')
    
    if deleted_project_exports:
        print('EXPORTS_FOUND:')
        for export in deleted_project_exports:
            print(f'  - {export[\"export_path\"]} (ID: {export[\"id\"]})')
    
    if orphaned_exports:
        print('ORPHANED_EXPORTS_FOUND:')
        for export in orphaned_exports:
            print(f'  - {export[\"export_path\"]} (Project ID: {export[\"project_id\"]}, Export ID: {export[\"id\"]})')
            
except Exception as e:
    print(f'ERROR:{e}')
")
    
    local deleted_exports=$(echo "$orphaned_exports" | grep "DELETED_PROJECT_EXPORTS:" | cut -d: -f2)
    local orphaned_exports_count=$(echo "$orphaned_exports" | grep "ORPHANED_EXPORTS:" | cut -d: -f2)
    
    if [[ "$deleted_exports" == "0" ]]; then
        print_success "No export records found for deleted project"
    else
        print_error "$deleted_exports export records still exist for deleted project"
        echo "$orphaned_exports" | grep -A 10 "EXPORTS_FOUND:"
    fi
    
    if [[ "$orphaned_exports_count" == "0" ]]; then
        print_success "No orphaned export records found"
    else
        print_warning "$orphaned_exports_count orphaned export records found"
        echo "$orphaned_exports" | grep -A 10 "ORPHANED_EXPORTS_FOUND:"
    fi
    echo ""
    
    # 4. Check for broken variable references
    echo "4. Variable References Check:"
    local broken_refs=$(curl -s "$BASE_URL/env-vars/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    variables = data.get('variables', [])
    
    broken_linked = []
    broken_concat = []
    
    for var in variables:
        # Check linked_to references
        if var.get('linked_to') and '$project_name:' in str(var.get('linked_to')):
            broken_linked.append(var)
        
        # Check concat_parts references
        if var.get('concat_parts') and '$project_name:' in str(var.get('concat_parts')):
            broken_concat.append(var)
    
    print(f'BROKEN_LINKED:{len(broken_linked)}')
    print(f'BROKEN_CONCAT:{len(broken_concat)}')
    
    if broken_linked:
        print('BROKEN_LINKED_FOUND:')
        for var in broken_linked:
            print(f'  - {var[\"name\"]} -> {var[\"linked_to\"]} (Project ID: {var[\"project_id\"]})')
    
    if broken_concat:
        print('BROKEN_CONCAT_FOUND:')
        for var in broken_concat:
            print(f'  - {var[\"name\"]} -> {var[\"concat_parts\"]} (Project ID: {var[\"project_id\"]})')
            
except Exception as e:
    print(f'ERROR:{e}')
")
    
    local broken_linked_count=$(echo "$broken_refs" | grep "BROKEN_LINKED:" | cut -d: -f2)
    local broken_concat_count=$(echo "$broken_refs" | grep "BROKEN_CONCAT:" | cut -d: -f2)
    
    if [[ "$broken_linked_count" == "0" ]]; then
        print_success "No broken linked variable references found"
    else
        print_error "$broken_linked_count variables with broken linked references found"
        echo "$broken_refs" | grep -A 10 "BROKEN_LINKED_FOUND:"
    fi
    
    if [[ "$broken_concat_count" == "0" ]]; then
        print_success "No broken concatenated variable references found"
    else
        print_error "$broken_concat_count variables with broken concatenated references found"
        echo "$broken_refs" | grep -A 10 "BROKEN_CONCAT_FOUND:"
    fi
    echo ""
    
    # 5. Summary
    print_header "Deletion Verification Summary"
    local total_issues=$((deleted_vars + deleted_exports + broken_linked_count + broken_concat_count))
    
    if [[ $total_issues -eq 0 ]]; then
        print_success "✅ PERFECT CLEANUP: Project '$project_name' and all related data successfully deleted"
        print_success "✅ No orphaned records found"
        print_success "✅ No broken references found"
        print_success "✅ Database integrity maintained"
        echo ""
        print_info "Cascade deletion worked correctly! 🎉"
    else
        print_error "❌ CLEANUP ISSUES DETECTED:"
        echo "  - Remaining env vars: $deleted_vars"
        echo "  - Remaining exports: $deleted_exports"
        echo "  - Broken linked refs: $broken_linked_count"
        echo "  - Broken concat refs: $broken_concat_count"
        echo ""
        print_warning "Manual cleanup may be required!"
    fi
}

# Function to run verification for existing project (already deleted)
verify_existing_deletion() {
    local project_name=$1
    
    print_header "Verifying Previously Deleted Project: '$project_name'"
    
    # Since we don't know the original project ID, we'll check for data integrity
    echo "Checking for any remnants of '$project_name'..."
    echo ""
    
    # Check if project still exists
    local project_check=$(check_project_exists "$project_name")
    if [[ "$project_check" == "NOT_FOUND" ]]; then
        print_success "Project '$project_name' not found in projects table ✅"
    else
        print_error "Project '$project_name' still exists: $project_check"
        return 1
    fi
    
    # Check for broken references
    local broken_refs=$(curl -s "$BASE_URL/env-vars/" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    variables = data.get('variables', [])
    
    broken_count = 0
    for var in variables:
        if var.get('linked_to') and '$project_name:' in str(var.get('linked_to')):
            broken_count += 1
            print(f'BROKEN: {var[\"name\"]} links to {var[\"linked_to\"]}')
        if var.get('concat_parts') and '$project_name:' in str(var.get('concat_parts')):
            broken_count += 1
            print(f'BROKEN: {var[\"name\"]} concatenates {var[\"concat_parts\"]}')
    
    if broken_count == 0:
        print('NO_BROKEN_REFS')
    else:
        print(f'BROKEN_COUNT:{broken_count}')
        
except Exception as e:
    print(f'ERROR:{e}')
")
    
    if [[ "$broken_refs" == "NO_BROKEN_REFS" ]]; then
        print_success "No broken variable references to '$project_name' found ✅"
    else
        print_error "Found broken references to '$project_name':"
        echo "$broken_refs"
    fi
    
    echo ""
    print_success "✅ Verification complete for '$project_name'"
}

# Main execution
main() {
    # If no project name provided, show current projects and ask
    if [[ -z "$PROJECT_NAME" ]]; then
        print_header "Current Projects"
        echo "Available projects:"
        
        local projects=$(get_all_projects)
        if [[ "$projects" == *"ERROR"* ]]; then
            print_error "Failed to fetch projects: $projects"
            exit 1
        fi
        
        echo "$projects" | while IFS=':' read -r id name description; do
            echo "  $id. $name - $description"
        done
        
        echo ""
        echo "Usage: $0 [BASE_URL] [PROJECT_NAME]"
        echo "Example: $0 http://localhost:8088/api/v1 webapp"
        echo ""
        print_info "You can verify a previously deleted project (like 'webapp') or delete and verify a current one"
        exit 0
    fi
    
    # Check if project exists
    local project_info=$(check_project_exists "$PROJECT_NAME")
    
    if [[ "$project_info" == "NOT_FOUND" ]]; then
        print_info "Project '$PROJECT_NAME' not found - verifying previous deletion..."
        verify_existing_deletion "$PROJECT_NAME"
    else
        # Project exists - ask user what to do
        IFS=':' read -r project_id project_name project_desc <<< "$project_info"
        echo "Found project: $project_name (ID: $project_id) - $project_desc"
        echo ""
        
        echo "Choose an option:"
        echo "1. Delete the project and verify cleanup"
        echo "2. Just verify current database integrity"
        echo "3. Cancel"
        echo ""
        read -p "Enter your choice (1-3): " choice
        
        case $choice in
            1)
                print_info "Deleting project '$project_name' (ID: $project_id)..."
                
                delete_result=$(curl -s -X DELETE "$BASE_URL/projects/$project_id")
                
                if [[ $? -eq 0 ]]; then
                    print_success "Project deletion request sent"
                    sleep 2  # Wait for deletion to complete
                    verify_deletion_cleanup "$project_name" "$project_id"
                else
                    print_error "Failed to delete project: $delete_result"
                fi
                ;;
            2)
                print_info "Verifying current database integrity..."
                verify_deletion_cleanup "$project_name" "$project_id"
                ;;
            3)
                print_info "Operation cancelled"
                exit 0
                ;;
            *)
                print_error "Invalid choice"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@" 