import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import os
import sys

# Add the parent directory to the path so we can import main
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, code_analyzer, generate_tests, weather_api

client = TestClient(app)

class TestHealthEndpoints:
    """Test basic health and info endpoints."""
    
    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data
        assert "features" in data

class TestCodeGeneration:
    """Test code generation endpoints."""
    
    @patch('main.ChatOpenAI')
    def test_generate_function_endpoint(self, mock_llm):
        # Mock the LLM response
        mock_response = AsyncMock()
        mock_response.content = "    return n * 2"
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        response = client.post("/generate-function", json={
            "language": "python",
            "signature": "def double(n: int) -> int:",
            "description": "Double the input number"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert "language" in data
        assert data["language"] == "python"
    
    @patch('main.code_analyzer')
    def test_analyze_code_endpoint(self, mock_analyzer):
        mock_analyzer.return_value = "This function divides two numbers but lacks error handling for division by zero."
        
        response = client.post("/analyze-code", json={
            "code": "def divide(a, b):\n    return a / b",
            "language": "python"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "language" in data
    
    @patch('main.generate_tests')
    def test_generate_tests_endpoint(self, mock_tests):
        mock_tests.return_value = "import unittest\n\nclass TestDivide(unittest.TestCase):\n    def test_divide(self):\n        self.assertEqual(divide(10, 2), 5)"
        
        response = client.post("/generate-tests", json={
            "code": "def divide(a, b):\n    return a / b",
            "language": "python"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        assert "language" in data

class TestTools:
    """Test the individual tool functions."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_weather_api_success(self, mock_client):
        # Mock successful weather API response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "weather": [{"description": "sunny"}],
            "main": {"temp": 25}
        }
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await weather_api("London", "celsius")
        assert "sunny" in result
        assert "25" in result
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_weather_api_failure(self, mock_client):
        # Mock failed weather API response
        mock_response = AsyncMock()
        mock_response.status_code = 404
        
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        
        result = await weather_api("InvalidCity", "celsius")
        assert "Could not fetch weather" in result
    
    @pytest.mark.asyncio
    @patch('main.ChatOpenAI')
    async def test_code_analyzer(self, mock_llm):
        mock_response = AsyncMock()
        mock_response.content = "This function lacks error handling and documentation."
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        result = await code_analyzer("def test(): pass", "python")
        assert "error handling" in result
    
    @pytest.mark.asyncio
    @patch('main.ChatOpenAI')
    async def test_generate_tests(self, mock_llm):
        mock_response = AsyncMock()
        mock_response.content = "import unittest\n\nclass TestExample(unittest.TestCase):\n    def test_function(self):\n        pass"
        mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)
        
        result = await generate_tests("def example(): pass", "python")
        assert "unittest" in result
        assert "TestExample" in result

class TestValidation:
    """Test input validation and error handling."""
    
    def test_generate_function_missing_fields(self):
        response = client.post("/generate-function", json={
            "language": "python"
            # Missing required 'signature' field
        })
        assert response.status_code == 422  # Validation error
    
    def test_analyze_code_missing_fields(self):
        response = client.post("/analyze-code", json={
            "language": "python"
            # Missing required 'code' field
        })
        assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    pytest.main([__file__]) 