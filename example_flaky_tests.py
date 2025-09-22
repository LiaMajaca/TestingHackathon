#!/usr/bin/env python3
"""
Example test file demonstrating various flaky test patterns.
This file contains intentionally flaky tests for demonstration purposes.
"""

import time
import random
import os
import requests
from unittest.mock import patch, MagicMock

# Example 1: Time-dependent flaky test
def test_time_dependent_flaky():
    """This test is flaky because it depends on timing."""
    start_time = time.time()
    # Simulate some work
    time.sleep(0.1)  # This makes the test flaky
    duration = time.time() - start_time
    assert duration < 0.2  # Might fail on slow systems

# Example 2: Random data flaky test
def test_random_data_flaky():
    """This test is flaky because it uses random data without a seed."""
    data = [random.randint(1, 100) for _ in range(10)]
    assert len(data) == 10
    assert all(x > 0 for x in data)  # This will always pass
    # But if we had: assert sum(data) > 500, it would be flaky

# Example 3: External dependency flaky test
def test_external_api_flaky():
    """This test is flaky because it depends on external API."""
    try:
        # This would be flaky in real scenarios
        response = requests.get("https://httpbin.org/status/200", timeout=5)
        assert response.status_code == 200
    except requests.RequestException:
        # Test might fail due to network issues
        assert False, "Network request failed"

# Example 4: File system flaky test
def test_filesystem_flaky():
    """This test is flaky because it doesn't clean up properly."""
    test_file = "temp_test_file.txt"
    
    # Create a file
    with open(test_file, 'w') as f:
        f.write("test data")
    
    # Test the file exists
    assert os.path.exists(test_file)
    
    # Clean up (but this might fail if test is interrupted)
    try:
        os.remove(test_file)
    except OSError:
        pass  # File might already be removed

# Example 5: Global state flaky test
def test_global_state_flaky():
    """This test is flaky because it modifies global state."""
    # Modify environment variable
    original_value = os.environ.get('TEST_VAR', '')
    os.environ['TEST_VAR'] = 'test_value'
    
    try:
        assert os.environ['TEST_VAR'] == 'test_value'
    finally:
        # Restore original value
        if original_value:
            os.environ['TEST_VAR'] = original_value
        else:
            os.environ.pop('TEST_VAR', None)

# Example 6: Good test (not flaky)
def test_deterministic_good():
    """This is a good, non-flaky test."""
    # Use fixed data
    data = [1, 2, 3, 4, 5]
    assert len(data) == 5
    assert sum(data) == 15
    assert max(data) == 5

# Example 7: Good test with mocking
@patch('requests.get')
def test_mocked_external_api_good(mock_get):
    """This is a good test that mocks external dependencies."""
    # Mock the response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok"}
    mock_get.return_value = mock_response
    
    # Test the function
    response = requests.get("https://api.example.com/data")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# Example 8: Good test with proper cleanup
def test_proper_cleanup_good():
    """This is a good test with proper cleanup."""
    import tempfile
    import shutil
    
    # Use temporary directory
    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test.txt")
    
    try:
        # Create and test file
        with open(test_file, 'w') as f:
            f.write("test data")
        
        assert os.path.exists(test_file)
        with open(test_file, 'r') as f:
            content = f.read()
        assert content == "test data"
        
    finally:
        # Always clean up
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    # Run tests if executed directly
    import pytest
    pytest.main([__file__, "-v"])
