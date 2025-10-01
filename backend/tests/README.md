# Variable Resolver Test Suite

This directory contains comprehensive test cases for the MD-Linked-Secrets variable resolver functionality.

## 📁 Test Files

### `test_variable_resolver.py`
**Unit tests** for the variable resolver using pytest and mocks.

**Features Tested:**
- ✅ Raw variable resolution
- ✅ Linked variable resolution  
- ✅ Concatenated variables with all separator types
- ✅ Mixed variable types (linked + raw)
- ✅ Error handling and edge cases
- ✅ Backward compatibility with old format

### `integration_test_script.sh`
**Integration tests** that run against the actual API server.

**Features Tested:**
- ✅ End-to-end variable creation and resolution
- ✅ All separator types: `|`, `-`, `_`, space, complex separators
- ✅ Mixed variable types in concatenation
- ✅ Frontend "Show Values" functionality validation
- ✅ Error handling with real database
- ✅ Backward compatibility verification

## 🚀 Running Tests

### Prerequisites
- Backend server running on `http://localhost:8088`
- Python 3.7+ with pytest installed
- curl command available

### Unit Tests
```bash
# Install dependencies
pip install pytest pytest-asyncio

# Run unit tests
cd backend
pytest tests/test_variable_resolver.py -v

# Run with coverage
pytest tests/test_variable_resolver.py --cov=app.core.variable_resolver -v
```

### Integration Tests
```bash
# Make sure backend is running first
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8088

# Run integration tests (in new terminal)
cd backend/tests
./integration_test_script.sh

# Or with custom URL
./integration_test_script.sh http://localhost:8088/api/v1
```

## 🧪 Test Coverage

### Variable Types Tested

| Type | Format | Example | Expected Resolution |
|------|--------|---------|-------------------|
| **Raw** | `raw_value` | `"value1"` | `value1` |
| **Linked** | `PROJECT:VAR` | `api:API_VERSION` | `v1` |
| **Concatenated (Quoted)** | `"PROJECT:VAR"SEP"PROJECT:VAR"` | `"Test:var1"\|"Test:var2"` | `value1\|value2` |
| **Concatenated (Old)** | `PROJECT:VAR\|PROJECT:VAR` | `Test:var1\|Test:var2` | `value1value2` |

### Separator Types Tested

| Separator | Example | Expected |
|-----------|---------|----------|
| **Pipe** | `"Test:var1"\|"Test:var2"` | `value1\|value2` |
| **Dash** | `"Test:var1"-"Test:var2"` | `value1-value2` |
| **Underscore** | `"Test:var1"_"Test:var2"` | `value1_value2` |
| **Space** | `"Test:var1" "Test:var2"` | `value1 value2` |
| **Complex** | `"Test:var1"_-_"Test:var2"` | `value1_-_value2` |

### Mixed Type Combinations

| Combination | Example | Expected |
|-------------|---------|----------|
| **Linked + Raw** | `"Test:linked_var"-"Test:raw_var"` | `resolved_value-raw_value` |
| **Raw + Raw** | `"Test:var1"\|"Test:var2"` | `value1\|value2` |
| **Same Variable** | `"Test:var1"\|"Test:var1"` | `value1\|value1` |
| **Single Variable** | `"Test:var1"` | `value1` |

### Error Cases Tested

| Error Type | Scenario | Expected Behavior |
|------------|----------|------------------|
| **Project Not Found** | `"NonExistent:var"` | `ValueError: Project not found` |
| **Variable Not Found** | `"Test:nonexistent"` | `ValueError: Variable not found` |
| **Circular Reference** | `A → B → A` | `ValueError: Circular reference` |
| **Invalid Format** | Invalid concatenation syntax | Validation error |

## 🎯 Real-World Test Scenarios

### Scenario 1: Microservices Configuration
```json
{
  "SERVICE_URL": "Test:BASE_URL",
  "API_ENDPOINT": "\"Test:SERVICE_URL\"/api/\"Test:VERSION\"",
  "FULL_PATH": "\"Test:API_ENDPOINT\"/\"Test:RESOURCE\""
}
```

### Scenario 2: Environment-Specific Values
```json
{
  "DATABASE_URL": "\"Config:DB_HOST\":\"Config:DB_PORT\"/\"Config:DB_NAME\"",
  "REDIS_URL": "redis://\"Config:REDIS_HOST\":\"Config:REDIS_PORT\""
}
```

### Scenario 3: Backward Compatibility
```json
{
  "OLD_FORMAT": "Project:var1|Project:var2",
  "NEW_FORMAT": "\"Project:var1\"|\"Project:var2\""
}
```

## 📊 Expected Test Results

When running the integration tests, you should see output similar to:

```
🧪 Variable Resolver Integration Tests
======================================

📋 Test: Setup - Creating Test Projects and Variables
✅ Created test project (ID: 1)
✅ Created API project (ID: 2)
✅ Created raw variable: testvar1
✅ Created linked variable: test_link

📋 Test: Variable Resolution - All Types
Resolution Response:
{
  "resolved_values": {
    "testvar1": "value1",
    "testvar2": "value2", 
    "test_link": "v1",
    "concat_pipe": "value1|value2",
    "concat_dash": "value1-value2",
    "concat_underscore": "value1_value2",
    "concat_space": "value1 value2",
    "concat_complex": "value1_-_value2",
    "concat_mixed": "v1-value1",
    "concat_repeat": "value1|value1",
    "concat_single": "value1",
    "old_format": "value1value2"
  }
}

Expected Results Validation:
✅ testvar1: value1 (expected: value1) - Raw variable
✅ test_link: v1 (expected: v1) - Linked variable  
✅ concat_pipe: value1|value2 (expected: value1|value2) - Pipe separator
✅ concat_dash: value1-value2 (expected: value1-value2) - Dash separator
✅ concat_mixed: v1-value1 (expected: v1-value1) - Mixed linked+raw
...
```

## 🔧 Troubleshooting

### Common Issues

1. **Backend not running**
   ```bash
   # Start backend first
   cd backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8088
   ```

2. **Permission denied on script**
   ```bash
   chmod +x backend/tests/integration_test_script.sh
   ```

3. **Python modules not found**
   ```bash
   pip install pytest pytest-asyncio
   ```

4. **Database connection issues**
   - Ensure PostgreSQL is running
   - Check database credentials in backend config

### Manual Testing

You can also run individual test cases manually:

```bash
# Test variable resolution
curl -X POST -H "Content-Type: application/json" \
     -d '{"project_id":5}' \
     http://localhost:8088/api/v1/env-vars/resolve

# Create concatenated variable
curl -X POST -H "Content-Type: application/json" \
     -d '{"project_id":5,"name":"test","concat_parts":"\"Test:var1\"-\"Test:var2\""}' \
     http://localhost:8088/api/v1/env-vars/

# List variables  
curl http://localhost:8088/api/v1/env-vars/?project_id=5
```

## 📝 Adding New Tests

### Unit Tests
Add new test methods to `test_variable_resolver.py`:

```python
async def test_your_scenario(self, resolver, mock_db_session):
    # Setup mocks
    # Test functionality
    # Assert results
    pass
```

### Integration Tests
Add new test functions to `integration_test_script.sh`:

```bash
test_your_scenario() {
    print_test "Your Test Description"
    
    # Create test data with curl
    # Test functionality 
    # Validate results
    
    print_success "Test completed"
}
```

## 🎯 Validation Checklist

When implementing new features, ensure these tests pass:

- [ ] Raw variables resolve correctly
- [ ] Linked variables resolve correctly  
- [ ] All separator types preserve correctly in concatenation
- [ ] Mixed variable types work together
- [ ] Error cases are handled gracefully
- [ ] Backward compatibility is maintained
- [ ] Frontend "Show Values" displays resolved values
- [ ] Performance is acceptable for complex concatenations

---

**Note**: These tests validate the core functionality we implemented including:
- ✅ Quoted variable format (`"PROJECT:VAR"`)
- ✅ Separator preservation in concatenated variables
- ✅ Mixed linked and raw variable resolution
- ✅ Comprehensive error handling
- ✅ Backward compatibility with old format 