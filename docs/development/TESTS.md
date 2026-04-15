# Property-Based and Load/Stress Testing

This document describes the property-based testing and load/stress testing infrastructure added to the Rhiza project.

## Overview

Rhiza now includes two additional types of testing:

1. **Property-Based Testing** (using Hypothesis) - Tests that verify properties hold across a wide range of generated inputs
2. **Load/Stress Testing** (using pytest-benchmark) - Tests that measure performance and verify stability under load

## README Code Block Testing

The test file `.rhiza/tests/sync/test_readme_validation.py` automatically executes every `python`
code block in `README.md` and checks that its output matches the adjacent ` ```result ` block. It
also syntax-checks every `bash` block using `bash -n`.

### Skipping individual blocks with `+RHIZA_SKIP`

To exclude a specific code block from being executed or syntax-checked, append `+RHIZA_SKIP` to
the opening fence line:

~~~markdown
```python +RHIZA_SKIP
# This block will NOT be executed or syntax-checked by the readme tests.
# Use it for illustrative examples, environment-specific code, or incomplete snippets.
from my_env import some_function
some_function()
```

```bash +RHIZA_SKIP
# This bash block will NOT be syntax-checked.
run-something --only-on-ci
```
~~~

Markdown renderers (including GitHub) ignore everything after the first word on a fence line, so
the block still renders as a normal syntax-highlighted code block. All blocks that do **not** carry
`+RHIZA_SKIP` continue to be validated as before.

## Property-Based Testing

Property-based tests use the [Hypothesis](https://hypothesis.readthedocs.io/) library to automatically generate test cases that verify certain properties always hold true.

### Locations

In a standard Rhiza project, there are two relevant locations for property-based tests:

- **Project property-based tests** live in `tests/property/`. These are part of your normal test suite and are discovered by `pytest` via `pytest.ini:testpaths = tests`.
- **Rhiza's own template/internal property-based tests** (if present) live in `.rhiza/tests/property/`. These are not part of your project's main test suite by default.

### Running Property-Based Tests

In a typical setup, the Make targets map to these suites as follows:

- `make test`: runs `pytest` over everything under `tests/` (including `tests/property/`).
- `make rhiza-test`: runs Rhiza's internal tests under `.rhiza/tests/` (including `.rhiza/tests/property/` if any exist).

You can also invoke the corresponding `pytest` commands directly:

```bash
# Run all project property-based tests (what make test covers)
pytest tests/property/ -v

# Run Rhiza's internal/template property-based tests (if you have any in .rhiza)
pytest .rhiza/tests/property/ -v

# Run project property-based tests with more examples (increase coverage)
pytest tests/property/ -v --hypothesis-max-examples=1000

# Run project property-based tests with verbose Hypothesis output
pytest tests/property/ -v --hypothesis-verbosity=verbose
```

### Example Tests

The following property-based tests are included as examples:

#### Generic Property Tests
- **test_sort_correctness_using_properties**: Verifies that sorted() correctly orders lists and preserves all elements including duplicates

## Load/Stress Testing

Load and stress tests use [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) to measure performance and verify system stability under load.

### Location

Benchmark and stress tests are located in `tests/benchmarks/`

### Running Benchmark Tests

```bash
# Run all benchmarks
make benchmark

# Or with pytest directly
pytest tests/benchmarks/ -v

# Run benchmarks and generate histogram
pytest tests/benchmarks/ --benchmark-histogram=_tests/benchmarks/histogram

# Run benchmarks and save results
pytest tests/benchmarks/ --benchmark-json=_tests/benchmarks/results.json

# Skip benchmarks (for CI)
pytest tests/benchmarks/ --benchmark-skip

# Run only stress tests (note: these don't run with make benchmark by default)
pytest tests/benchmarks/ -m stress -v

# Skip stress tests (run only performance benchmarks)
pytest tests/benchmarks/ -m "not stress" -v
```

**Note**: The `make benchmark` target runs with `--benchmark-only`, which means stress tests (that don't use the `benchmark` fixture) will be skipped. To run stress tests explicitly, use `pytest tests/benchmarks/ -m stress -v`.

### Benchmark Test Categories

#### 1. Makefile Performance
Tests that measure the performance of common Makefile operations:
- `test_help_target_performance` - Measures help target execution time
- `test_print_variable_performance` - Measures variable printing performance
- `test_dry_run_install_performance` - Measures dry-run install performance
- `test_makefile_parsing_overhead` - Measures Makefile parsing overhead

#### 2. File System Operations
Tests that benchmark file system operations:
- `test_directory_traversal_performance` - Measures directory traversal speed
- `test_file_reading_performance` - Measures file reading performance
- `test_multiple_file_checks_performance` - Measures file existence checking

#### 3. Subprocess Overhead
Tests that measure subprocess creation overhead:
- `test_subprocess_creation_overhead` - Measures subprocess creation time
- `test_git_command_performance` - Measures git command execution time

#### 4. Stress Scenarios
Tests that verify stability under load (marked with `@pytest.mark.stress`):
- `test_repeated_help_invocations` - Stress tests repeated help invocations (100 iterations)
- `test_concurrent_print_variable_stress` - Tests concurrent Makefile invocations (deterministic)
- `test_file_system_stress` - Tests rapid file creation/deletion (100 iterations)

**Note**: Stress tests can be slow and are marked with the `stress` marker. They don't use the `benchmark` fixture, so they won't run with `make benchmark` (which uses `--benchmark-only`). Use `pytest tests/benchmarks/ -m stress -v` to run them explicitly.

### Understanding Benchmark Results

Benchmark output includes:
- **Min/Max**: Minimum and maximum execution times
- **Mean**: Average execution time
- **StdDev**: Standard deviation (consistency)
- **Median**: Median execution time
- **IQR**: Interquartile range
- **Outliers**: Number of outlier measurements
- **OPS**: Operations per second (1/Mean)

Example output:
```
--------------------------------------------------- benchmark: 1 tests ---------------------------------------------------
Name (time in ms)                    Min      Max     Mean  StdDev   Median     IQR  Outliers      OPS  Rounds  Iterations
--------------------------------------------------------------------------------------------------------------------------
test_help_target_performance     16.5255  18.0592  16.9294  0.3194  16.8354  0.4791      15;1  59.0689      55           1
--------------------------------------------------------------------------------------------------------------------------
```

## Integration with CI/CD

### GitHub Actions Integration

The benchmark tests are integrated with GitHub Actions via `.github/workflows/rhiza_benchmarks.yml`:

- Runs benchmarks on every push to main and pull requests
- Stores historical benchmark data in the `gh-pages` branch
- Alerts on performance regressions > 150%
- Posts warnings to PRs for performance degradation

### Running in CI

The property-based tests run as part of the regular test suite:

```bash
# Run all tests including property-based tests
make test
```

Benchmarks can be run separately or as part of validation:

```bash
# Run benchmarks
make benchmark
```

## Best Practices

### Writing Property-Based Tests

1. **Focus on invariants**: Test properties that should always hold true
2. **Use appropriate strategies**: Choose Hypothesis strategies that generate realistic inputs
3. **Keep tests fast**: Property tests run multiple times, so keep them quick
4. **Test edge cases**: Use `@example` decorator to test specific known edge cases

Example:
```python
from hypothesis import given, strategies as st, example

@given(version=st.from_regex(r"^\d+\.\d+\.\d+$", fullmatch=True))
@example(version="0.0.0")  # Test specific edge case
def test_version_parsing(version):
    parts = version.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)
```

### Writing Benchmark Tests

1. **Benchmark real operations**: Test actual operations users will perform
2. **Use fixtures wisely**: Use module or session-scoped fixtures for expensive setup
3. **Test multiple scenarios**: Benchmark best case, average case, and worst case
4. **Monitor trends**: Track benchmark results over time to detect regressions

Example:
```python
def test_operation_performance(benchmark):
    def run_operation():
        # Operation to benchmark
        return perform_operation()
    
    result = benchmark(run_operation)
    assert result is not None
```

### Writing Stress Tests

1. **Test realistic scenarios**: Simulate real-world usage patterns
2. **Set reasonable thresholds**: Allow small failure rates for resource contention
3. **Test concurrency**: Use ThreadPoolExecutor or ProcessPoolExecutor for concurrent tests
4. **Monitor resource usage**: Consider memory, CPU, and I/O in addition to time

Example:
```python
def test_concurrent_operations(root):
    import concurrent.futures
    
    def operation():
        # Operation to stress test
        return perform_operation()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(operation) for _ in range(100)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    success_rate = sum(results) / len(results)
    assert success_rate == 1.0  # Rhiza template stress tests require 100% success
```

## Dependencies

The following dependencies are required for property-based and load/stress testing:

```
# Property-based testing
hypothesis>=6.150.0

# Benchmarking and performance testing
pytest-benchmark>=5.2.3
pygal>=3.1.0
```

These are automatically installed when running `make install` or by installing from `.rhiza/requirements/tests.txt`.

## Troubleshooting

### Hypothesis Hangs or Times Out

If Hypothesis tests hang, you can:
1. Reduce the number of examples: `pytest --hypothesis-max-examples=10`
2. Set a deadline: `pytest --hypothesis-deadline=1000`
3. Use the CI profile: `pytest --hypothesis-profile=ci`

### Benchmarks Vary Too Much

If benchmark results have high variance:
1. Close other applications to reduce system load
2. Increase the number of rounds: `pytest --benchmark-min-rounds=10`
3. Run on a consistent environment (CI is preferred for accurate benchmarks)

### Stress Tests Fail

If stress tests fail occasionally:
1. Check system resources (memory, CPU)
2. Increase acceptable failure rate if resource contention is expected
3. Reduce iteration count for local development

## References

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)
- [GitHub Actions Benchmark Action](https://github.com/benchmark-action/github-action-benchmark)
