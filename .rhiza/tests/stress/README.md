# Stress Tests for Rhiza Framework

This directory contains stress tests that verify the stability and performance of the Rhiza framework under heavy load conditions.

## Overview

Stress tests differ from regular integration tests and benchmarks:
- **Integration tests** verify that workflows execute correctly
- **Benchmarks** measure performance of individual operations
- **Stress tests** verify system stability under concurrent load and repeated operations

These tests focus specifically on Rhiza's core operations: Makefile execution and Git operations used by release and sync workflows.

## Test Categories

### 1. Makefile Stress Tests (`test_makefile_stress.py`)

Tests Rhiza's Makefile operations under stress:
- Concurrent invocations of targets (help, dry-run)
- Repeated executions to detect resource leaks
- Parallel variable printing and Makefile parsing

### 2. Git Operations Stress Tests (`test_git_stress.py`)

Tests Git operations used by Rhiza (release scripts, sync) under concurrent load:
- Concurrent git status/log/diff/show commands
- Repeated git operations (status, log, branch, rev-parse)
- Rapid git rev-parse (used in release script)

## Running Stress Tests

### Run all stress tests
```bash
uv run pytest .rhiza/tests/stress/ -v
```

### Run specific stress test category
```bash
uv run pytest .rhiza/tests/stress/test_makefile_stress.py -v
uv run pytest .rhiza/tests/stress/test_git_stress.py -v
```

### Run with custom iteration count
```bash
# Reduce iterations for faster testing
uv run pytest .rhiza/tests/stress/ -v --iterations=10

# Increase iterations for more thorough testing
uv run pytest .rhiza/tests/stress/ -v --iterations=500
```

### Run with custom worker count
```bash
# Test with more concurrent workers
uv run pytest .rhiza/tests/stress/ -v --workers=20
```

### Skip stress tests (when running full test suite)
```bash
uv run pytest .rhiza/tests/ -v -m "not stress"
```

## Test Markers

All tests in this directory are marked with `@pytest.mark.stress` to allow selective execution:

```python
@pytest.mark.stress
def test_concurrent_operations():
    # Test concurrent operations
    pass
```

## Expected Behavior

Stress tests should:
1. **Pass consistently** - No flakiness or race conditions
2. **Complete in reasonable time** - Generally < 60 seconds per test
3. **Clean up resources** - No leaked file handles, processes, or temporary files
4. **Report clear failures** - When failures occur, provide actionable error messages

## Acceptance Criteria

For Rhiza framework stress tests, we aim for:
- **100% success rate** - All operations should complete successfully
- **No resource leaks** - Memory and file handles should be cleaned up
- **Deterministic behavior** - Tests should produce consistent results
- **Reasonable performance** - Operations should complete within expected time bounds

## Troubleshooting

### Tests timeout
- Reduce iteration count: `pytest --iterations=10`
- Reduce worker count: `pytest --workers=5`
- Check system resources (CPU, memory, disk)

### Intermittent failures
- Run with verbose output: `pytest -vv`
- Check for resource contention with other processes
- Verify git configuration (may affect git operations)

### Out of memory errors
- Reduce concurrent workers
- Check for memory leaks in test code
- Ensure proper cleanup in fixtures

## Contributing

When adding new stress tests:
1. Use the `@pytest.mark.stress` decorator
2. Use provided fixtures (`stress_iterations`, `concurrent_workers`)
3. Ensure proper cleanup (use context managers or fixtures)
4. Document expected behavior and acceptance criteria
5. Keep tests focused on one stress scenario
6. Provide clear assertion messages

Example:
```python
import pytest
import concurrent.futures

@pytest.mark.stress
def test_concurrent_operation(stress_iterations, concurrent_workers):
    """Test concurrent execution of operation X."""
    
    def perform_operation():
        # Operation to stress test
        return True
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor:
        futures = [executor.submit(perform_operation) for _ in range(stress_iterations)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    success_rate = sum(results) / len(results)
    assert success_rate == 1.0, f"Expected 100% success rate, got {success_rate * 100:.1f}%"
```

## See Also

- [Main Test README](../README.md) - Overview of all test categories
- [Integration Tests](../integration/) - End-to-end workflow tests
- [Benchmarks](../../../tests/benchmarks/) - Performance benchmarks
- [Property Tests](../../../tests/property/) - Property-based tests
