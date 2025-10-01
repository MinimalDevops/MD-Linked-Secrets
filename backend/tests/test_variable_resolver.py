import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.variable_resolver import VariableResolver
from app.models import EnvVar, Project


class TestVariableResolver:
    """Test cases for variable resolver functionality"""

    @pytest.fixture
    async def mock_db_session(self):
        """Mock database session"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def resolver(self, mock_db_session):
        """Create resolver instance with mocked session"""
        return VariableResolver(mock_db_session)

    @pytest.fixture
    def mock_project(self):
        """Mock project object"""
        project = MagicMock()
        project.id = 1
        project.name = "Test"
        return project

    @pytest.fixture
    def mock_api_project(self):
        """Mock API project object"""
        project = MagicMock()
        project.id = 2
        project.name = "api"
        return project

    # Raw Variable Tests
    async def test_resolve_raw_variable(self, resolver, mock_db_session):
        """Test resolving a raw variable"""
        # Setup
        raw_var = MagicMock()
        raw_var.id = 1
        raw_var.name = "testvar1"
        raw_var.raw_value = "value1"
        raw_var.linked_to = None
        raw_var.concat_parts = None

        # Test
        result = await resolver._resolve_var_value(raw_var)

        # Assert
        assert result == "value1"

    # Linked Variable Tests
    async def test_resolve_linked_variable_basic(self, resolver, mock_db_session, mock_project, mock_api_project):
        """Test resolving a basic linked variable"""
        # Setup linked variable
        linked_var = MagicMock()
        linked_var.id = 2
        linked_var.name = "test_link"
        linked_var.raw_value = None
        linked_var.linked_to = "api:API_VERSION"
        linked_var.concat_parts = None

        # Setup target variable
        target_var = MagicMock()
        target_var.id = 3
        target_var.name = "API_VERSION"
        target_var.raw_value = "v1"
        target_var.linked_to = None
        target_var.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # First call: find project "api"
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_api_project)),
            # Second call: find variable "API_VERSION" in project
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var))
        ]

        # Test
        result = await resolver._resolve_var_value(linked_var)

        # Assert
        assert result == "v1"

    async def test_resolve_linked_variable_not_found_project(self, resolver, mock_db_session):
        """Test resolving linked variable with non-existent project"""
        # Setup
        linked_var = MagicMock()
        linked_var.id = 2
        linked_var.name = "test_link"
        linked_var.raw_value = None
        linked_var.linked_to = "nonexistent:VAR"
        linked_var.concat_parts = None

        # Mock database query - project not found
        mock_db_session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        # Test & Assert
        with pytest.raises(ValueError, match="Project not found: nonexistent"):
            await resolver._resolve_var_value(linked_var)

    async def test_resolve_linked_variable_not_found_variable(self, resolver, mock_db_session, mock_api_project):
        """Test resolving linked variable with non-existent variable"""
        # Setup
        linked_var = MagicMock()
        linked_var.id = 2
        linked_var.name = "test_link"
        linked_var.raw_value = None
        linked_var.linked_to = "api:NONEXISTENT"
        linked_var.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # First call: find project "api" - success
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_api_project)),
            # Second call: find variable "NONEXISTENT" - not found
            MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        ]

        # Test & Assert
        with pytest.raises(ValueError, match="Variable not found: api:NONEXISTENT"):
            await resolver._resolve_var_value(linked_var)

    # Concatenated Variable Tests - Raw Variables
    async def test_resolve_concatenated_raw_variables_pipe_separator(self, resolver, mock_db_session, mock_project):
        """Test concatenated variables with raw values using pipe separator"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 4
        concat_var.name = "test_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:testvar1"|"Test:testvar2"'

        # Setup target variables
        target_var1 = MagicMock()
        target_var1.id = 5
        target_var1.name = "testvar1"
        target_var1.raw_value = "value1"
        target_var1.linked_to = None
        target_var1.concat_parts = None

        target_var2 = MagicMock()
        target_var2.id = 6
        target_var2.name = "testvar2"
        target_var2.raw_value = "value2"
        target_var2.linked_to = None
        target_var2.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # Find project "Test" (1st variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var1)),
            # Find project "Test" (2nd variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar2"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var2))
        ]

        # Test
        result = await resolver._resolve_var_value(concat_var)

        # Assert
        assert result == "value1|value2"

    async def test_resolve_concatenated_raw_variables_dash_separator(self, resolver, mock_db_session, mock_project):
        """Test concatenated variables with raw values using dash separator"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 4
        concat_var.name = "test_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:testvar1"-"Test:testvar2"'

        # Setup target variables
        target_var1 = MagicMock()
        target_var1.id = 5
        target_var1.name = "testvar1"
        target_var1.raw_value = "value1"
        target_var1.linked_to = None
        target_var1.concat_parts = None

        target_var2 = MagicMock()
        target_var2.id = 6
        target_var2.name = "testvar2"
        target_var2.raw_value = "value2"
        target_var2.linked_to = None
        target_var2.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # Find project "Test" (1st variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var1)),
            # Find project "Test" (2nd variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar2"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var2))
        ]

        # Test
        result = await resolver._resolve_var_value(concat_var)

        # Assert
        assert result == "value1-value2"

    async def test_resolve_concatenated_raw_variables_underscore_separator(self, resolver, mock_db_session, mock_project):
        """Test concatenated variables with raw values using underscore separator"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 4
        concat_var.name = "test_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:testvar1"_"Test:testvar2"'

        # Setup target variables
        target_var1 = MagicMock()
        target_var1.id = 5
        target_var1.name = "testvar1"
        target_var1.raw_value = "value1"
        target_var1.linked_to = None
        target_var1.concat_parts = None

        target_var2 = MagicMock()
        target_var2.id = 6
        target_var2.name = "testvar2"
        target_var2.raw_value = "value2"
        target_var2.linked_to = None
        target_var2.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # Find project "Test" (1st variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var1)),
            # Find project "Test" (2nd variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar2"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var2))
        ]

        # Test
        result = await resolver._resolve_var_value(concat_var)

        # Assert
        assert result == "value1_value2"

    async def test_resolve_concatenated_raw_variables_space_separator(self, resolver, mock_db_session, mock_project):
        """Test concatenated variables with raw values using space separator"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 4
        concat_var.name = "test_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:testvar1" "Test:testvar2"'

        # Setup target variables
        target_var1 = MagicMock()
        target_var1.id = 5
        target_var1.name = "testvar1"
        target_var1.raw_value = "value1"
        target_var1.linked_to = None
        target_var1.concat_parts = None

        target_var2 = MagicMock()
        target_var2.id = 6
        target_var2.name = "testvar2"
        target_var2.raw_value = "value2"
        target_var2.linked_to = None
        target_var2.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # Find project "Test" (1st variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var1)),
            # Find project "Test" (2nd variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar2"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var2))
        ]

        # Test
        result = await resolver._resolve_var_value(concat_var)

        # Assert
        assert result == "value1 value2"

    # Concatenated Variable Tests - Mixed Types
    async def test_resolve_concatenated_linked_and_raw_variables(self, resolver, mock_db_session, mock_project, mock_api_project):
        """Test concatenated variables mixing linked and raw variables"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 7
        concat_var.name = "mixed_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:test_link"-"Test:testvar1"'

        # Setup linked variable
        linked_var = MagicMock()
        linked_var.id = 8
        linked_var.name = "test_link"
        linked_var.raw_value = None
        linked_var.linked_to = "api:API_VERSION"
        linked_var.concat_parts = None

        # Setup target of linked variable
        api_var = MagicMock()
        api_var.id = 9
        api_var.name = "API_VERSION"
        api_var.raw_value = "v1"
        api_var.linked_to = None
        api_var.concat_parts = None

        # Setup raw variable
        raw_var = MagicMock()
        raw_var.id = 10
        raw_var.name = "testvar1"
        raw_var.raw_value = "value1"
        raw_var.linked_to = None
        raw_var.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # 1st variable: Find project "Test" for test_link
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "test_link"
            MagicMock(scalar_one_or_none=MagicMock(return_value=linked_var)),
            # Resolve linked variable: Find project "api"
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_api_project)),
            # Find variable "API_VERSION"
            MagicMock(scalar_one_or_none=MagicMock(return_value=api_var)),
            # 2nd variable: Find project "Test" for testvar1
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=raw_var))
        ]

        # Test
        result = await resolver._resolve_var_value(concat_var)

        # Assert
        assert result == "v1-value1"

    async def test_resolve_concatenated_same_raw_variable_repeated(self, resolver, mock_db_session, mock_project):
        """Test concatenated variables with the same raw variable repeated"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 11
        concat_var.name = "repeated_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:testvar1"|"Test:testvar1"'

        # Setup target variable
        target_var = MagicMock()
        target_var.id = 12
        target_var.name = "testvar1"
        target_var.raw_value = "value1"
        target_var.linked_to = None
        target_var.concat_parts = None

        # Mock database queries (called twice for same variable)
        mock_db_session.execute.side_effect = [
            # 1st occurrence: Find project "Test"
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var)),
            # 2nd occurrence: Find project "Test"
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var))
        ]

        # Test
        result = await resolver._resolve_var_value(concat_var)

        # Assert
        assert result == "value1|value1"

    # Backward Compatibility Tests
    async def test_resolve_concatenated_old_format_pipe(self, resolver, mock_db_session, mock_project):
        """Test backward compatibility with old format using pipe separator"""
        # Setup concatenated variable (old format without quotes)
        concat_var = MagicMock()
        concat_var.id = 13
        concat_var.name = "old_format_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = 'Test:testvar1|Test:testvar2'

        # Setup target variables
        target_var1 = MagicMock()
        target_var1.id = 14
        target_var1.name = "testvar1"
        target_var1.raw_value = "value1"
        target_var1.linked_to = None
        target_var1.concat_parts = None

        target_var2 = MagicMock()
        target_var2.id = 15
        target_var2.name = "testvar2"
        target_var2.raw_value = "value2"
        target_var2.linked_to = None
        target_var2.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # Find project "Test" (1st variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var1)),
            # Find project "Test" (2nd variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar2"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var2))
        ]

        # Test
        result = await resolver._resolve_var_value(concat_var)

        # Assert - old format concatenates without separators
        assert result == "value1value2"

    # Project Resolution Tests
    async def test_resolve_project_variables_all_types(self, resolver, mock_db_session, mock_project, mock_api_project):
        """Test resolving all variables in a project with mixed types"""
        # Setup variables in project
        raw_var = MagicMock()
        raw_var.id = 16
        raw_var.name = "raw_var"
        raw_var.raw_value = "raw_value"
        raw_var.linked_to = None
        raw_var.concat_parts = None

        linked_var = MagicMock()
        linked_var.id = 17
        linked_var.name = "linked_var"
        linked_var.raw_value = None
        linked_var.linked_to = "api:API_VERSION"
        linked_var.concat_parts = None

        concat_var = MagicMock()
        concat_var.id = 18
        concat_var.name = "concat_var"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:raw_var"|"Test:linked_var"'

        # Setup API variable
        api_var = MagicMock()
        api_var.id = 19
        api_var.name = "API_VERSION"
        api_var.raw_value = "v1"
        api_var.linked_to = None
        api_var.concat_parts = None

        # Mock project variables query
        mock_db_session.execute.side_effect = [
            # Get all variables in project
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[raw_var, linked_var, concat_var])))),
            # Resolve linked_var: Find project "api"
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_api_project)),
            # Find variable "API_VERSION"
            MagicMock(scalar_one_or_none=MagicMock(return_value=api_var)),
            # Resolve concat_var: Find project "Test" (1st variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "raw_var"
            MagicMock(scalar_one_or_none=MagicMock(return_value=raw_var)),
            # Find project "Test" (2nd variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "linked_var"
            MagicMock(scalar_one_or_none=MagicMock(return_value=linked_var)),
            # Resolve linked_var again: Find project "api"
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_api_project)),
            # Find variable "API_VERSION"
            MagicMock(scalar_one_or_none=MagicMock(return_value=api_var))
        ]

        # Test
        result = await resolver.resolve_project_variables(project_id=1)

        # Assert
        expected = {
            "raw_var": "raw_value",
            "linked_var": "v1",
            "concat_var": "raw_value|v1"
        }
        assert result == expected

    # Error Handling Tests
    async def test_resolve_concatenated_variable_project_not_found(self, resolver, mock_db_session):
        """Test error handling when project is not found in concatenated variable"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 20
        concat_var.name = "error_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"NonExistent:var1"|"Test:var2"'

        # Mock database query - project not found
        mock_db_session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        # Test & Assert
        with pytest.raises(ValueError, match="Project not found: NonExistent"):
            await resolver._resolve_var_value(concat_var)

    async def test_resolve_concatenated_variable_variable_not_found(self, resolver, mock_db_session, mock_project):
        """Test error handling when variable is not found in concatenated variable"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 21
        concat_var.name = "error_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:nonexistent"|"Test:var2"'

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # Find project "Test" - success
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "nonexistent" - not found
            MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        ]

        # Test & Assert
        with pytest.raises(ValueError, match="Variable not found: Test:nonexistent"):
            await resolver._resolve_var_value(concat_var)

    # Edge Cases
    async def test_resolve_concatenated_variable_single_variable(self, resolver, mock_db_session, mock_project):
        """Test concatenated variable with only a single variable"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 22
        concat_var.name = "single_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:testvar1"'

        # Setup target variable
        target_var = MagicMock()
        target_var.id = 23
        target_var.name = "testvar1"
        target_var.raw_value = "value1"
        target_var.linked_to = None
        target_var.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # Find project "Test"
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var))
        ]

        # Test
        result = await resolver._resolve_var_value(concat_var)

        # Assert
        assert result == "value1"

    async def test_resolve_concatenated_variable_complex_separators(self, resolver, mock_db_session, mock_project):
        """Test concatenated variable with complex separators"""
        # Setup concatenated variable
        concat_var = MagicMock()
        concat_var.id = 24
        concat_var.name = "complex_concat"
        concat_var.raw_value = None
        concat_var.linked_to = None
        concat_var.concat_parts = '"Test:testvar1"_-_"Test:testvar2"'

        # Setup target variables
        target_var1 = MagicMock()
        target_var1.id = 25
        target_var1.name = "testvar1"
        target_var1.raw_value = "value1"
        target_var1.linked_to = None
        target_var1.concat_parts = None

        target_var2 = MagicMock()
        target_var2.id = 26
        target_var2.name = "testvar2"
        target_var2.raw_value = "value2"
        target_var2.linked_to = None
        target_var2.concat_parts = None

        # Mock database queries
        mock_db_session.execute.side_effect = [
            # Find project "Test" (1st variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar1"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var1)),
            # Find project "Test" (2nd variable)
            MagicMock(scalar_one_or_none=MagicMock(return_value=mock_project)),
            # Find variable "testvar2"
            MagicMock(scalar_one_or_none=MagicMock(return_value=target_var2))
        ]

        # Test
        result = await resolver._resolve_var_value(concat_var)

        # Assert
        assert result == "value1_-_value2"


# Integration Test Cases (to be run against actual API)
class TestVariableResolverIntegration:
    """Integration test cases that can be run against the actual API"""

    BASE_URL = "http://localhost:8088/api/v1"

    def test_create_test_project_and_variables(self):
        """
        Integration test setup - create test project and variables
        Run this manually via curl:
        
        # Create test project
        curl -X POST -H "Content-Type: application/json" \
             -d '{"name":"TestIntegration","description":"Integration test project"}' \
             {BASE_URL}/projects/
        
        # Create raw variable
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID,"name":"raw_var","raw_value":"raw_value","description":"Raw test variable"}' \
             {BASE_URL}/env-vars/
        
        # Create API project and variable for linking
        curl -X POST -H "Content-Type: application/json" \
             -d '{"name":"ApiIntegration","description":"API project for linking"}' \
             {BASE_URL}/projects/
             
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":API_PROJECT_ID,"name":"VERSION","raw_value":"v2.0","description":"API version"}' \
             {BASE_URL}/env-vars/
        
        # Create linked variable
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID,"name":"linked_var","linked_to":"ApiIntegration:VERSION","description":"Linked test variable"}' \
             {BASE_URL}/env-vars/
        """
        pass

    def test_concatenated_variables_integration(self):
        """
        Integration test cases for concatenated variables
        Run these manually via curl after setup:
        
        # Test 1: Raw concatenation with pipe separator
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID,"name":"concat_pipe","concat_parts":"\"TestIntegration:raw_var\"|\"TestIntegration:raw_var\"","description":"Pipe separator test"}' \
             {BASE_URL}/env-vars/
        
        # Test 2: Raw concatenation with dash separator
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID,"name":"concat_dash","concat_parts":"\"TestIntegration:raw_var\"-\"TestIntegration:raw_var\"","description":"Dash separator test"}' \
             {BASE_URL}/env-vars/
        
        # Test 3: Mixed linked and raw with underscore separator
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID,"name":"concat_mixed","concat_parts":"\"TestIntegration:linked_var\"_\"TestIntegration:raw_var\"","description":"Mixed types test"}' \
             {BASE_URL}/env-vars/
        
        # Test 4: Complex separator
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID,"name":"concat_complex","concat_parts":"\"TestIntegration:raw_var\"_-_\"TestIntegration:linked_var\"","description":"Complex separator test"}' \
             {BASE_URL}/env-vars/
        """
        pass

    def test_resolution_validation(self):
        """
        Integration test for resolution validation
        Run this via curl after creating variables:
        
        # Test resolution of all variables
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID}' \
             {BASE_URL}/env-vars/resolve
        
        Expected results:
        {
          "resolved_values": {
            "raw_var": "raw_value",
            "linked_var": "v2.0", 
            "concat_pipe": "raw_value|raw_value",
            "concat_dash": "raw_value-raw_value",
            "concat_mixed": "v2.0_raw_value",
            "concat_complex": "raw_value_-_v2.0"
          }
        }
        """
        pass

    def test_error_cases_integration(self):
        """
        Integration test for error cases
        Run these via curl:
        
        # Test 1: Non-existent project in concatenation
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID,"name":"error_project","concat_parts":"\"NonExistent:var\"|\"TestIntegration:raw_var\"","description":"Error test"}' \
             {BASE_URL}/env-vars/
        # Should return validation error
        
        # Test 2: Non-existent variable in concatenation
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID,"name":"error_variable","concat_parts":"\"TestIntegration:nonexistent\"|\"TestIntegration:raw_var\"","description":"Error test"}' \
             {BASE_URL}/env-vars/
        # Should create successfully but fail on resolution
        
        # Test resolution with errors
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID}' \
             {BASE_URL}/env-vars/resolve
        # Should return resolved values for valid variables only
        """
        pass

    def test_backward_compatibility_integration(self):
        """
        Integration test for backward compatibility
        Run these via curl:
        
        # Test old format (without quotes)
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID,"name":"old_format","concat_parts":"TestIntegration:raw_var|TestIntegration:raw_var","description":"Old format test"}' \
             {BASE_URL}/env-vars/
        
        # Test resolution
        curl -X POST -H "Content-Type: application/json" \
             -d '{"project_id":PROJECT_ID}' \
             {BASE_URL}/env-vars/resolve
        
        # Expected: old_format should resolve to "raw_valueraw_value" (no separator preserved)
        """
        pass


# Test Data Examples
TEST_DATA_EXAMPLES = {
    "raw_variable": {
        "name": "TEST_VAR",
        "raw_value": "test_value",
        "description": "A simple raw variable"
    },
    "linked_variable": {
        "name": "LINKED_VAR", 
        "linked_to": "OtherProject:SOME_VAR",
        "description": "A variable linked to another project"
    },
    "concatenated_variables": {
        "pipe_separator": {
            "name": "CONCAT_PIPE",
            "concat_parts": '"Project1:var1"|"Project1:var2"',
            "description": "Concatenated with pipe separator",
            "expected_resolution": "value1|value2"
        },
        "dash_separator": {
            "name": "CONCAT_DASH", 
            "concat_parts": '"Project1:var1"-"Project1:var2"',
            "description": "Concatenated with dash separator",
            "expected_resolution": "value1-value2"
        },
        "underscore_separator": {
            "name": "CONCAT_UNDERSCORE",
            "concat_parts": '"Project1:var1"_"Project1:var2"', 
            "description": "Concatenated with underscore separator",
            "expected_resolution": "value1_value2"
        },
        "space_separator": {
            "name": "CONCAT_SPACE",
            "concat_parts": '"Project1:var1" "Project1:var2"',
            "description": "Concatenated with space separator", 
            "expected_resolution": "value1 value2"
        },
        "complex_separator": {
            "name": "CONCAT_COMPLEX",
            "concat_parts": '"Project1:var1"_-_"Project1:var2"',
            "description": "Concatenated with complex separator",
            "expected_resolution": "value1_-_value2"
        },
        "mixed_types": {
            "name": "CONCAT_MIXED",
            "concat_parts": '"Project1:linked_var"-"Project1:raw_var"',
            "description": "Mixed linked and raw variables",
            "expected_resolution": "linked_resolved_value-raw_value"
        },
        "single_variable": {
            "name": "CONCAT_SINGLE", 
            "concat_parts": '"Project1:var1"',
            "description": "Single variable in concatenation",
            "expected_resolution": "value1"
        },
        "repeated_variable": {
            "name": "CONCAT_REPEAT",
            "concat_parts": '"Project1:var1"|"Project1:var1"',
            "description": "Same variable repeated",
            "expected_resolution": "value1|value1"
        }
    },
    "backward_compatibility": {
        "old_format_pipe": {
            "name": "OLD_PIPE",
            "concat_parts": "Project1:var1|Project1:var2",
            "description": "Old format with pipe",
            "expected_resolution": "value1value2"  # No separator preserved
        }
    }
}


if __name__ == "__main__":
    print("Variable Resolver Test Cases")
    print("=" * 50)
    print("\nTo run unit tests:")
    print("pytest backend/tests/test_variable_resolver.py -v")
    print("\nTo run integration tests:")
    print("Follow the curl commands in the TestVariableResolverIntegration class")
    print("\nTest data examples available in TEST_DATA_EXAMPLES dictionary") 