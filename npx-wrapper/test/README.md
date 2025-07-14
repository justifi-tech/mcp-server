# NPX Wrapper Test Suite

This directory contains comprehensive tests for the NPX wrapper implementation.

## Test Structure

```
test/
├── README.md                 # This file
├── setup.js                  # Test setup and configuration
├── mocha.opts               # Mocha configuration options
├── test-runner.js           # Cross-platform test runner
├── test-wrapper.js          # Tests for wrapper.js
├── test-install.js          # Tests for install.js
└── test-integration.js      # End-to-end integration tests
```

## Running Tests

### Basic Test Commands

```bash
# Run all tests
npm test

# Run unit tests only
npm run test:unit

# Run integration tests only
npm run test:integration

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch
```

### Advanced Test Options

```bash
# Run specific test file
node test/test-runner.js test-wrapper.js

# Run tests with specific reporter
node test/test-runner.js --reporter json

# Run tests matching pattern
node test/test-runner.js --grep "Python"

# Run tests with coverage and custom timeout
node test/test-runner.js --coverage --timeout 60000

# Run tests in parallel
node test/test-runner.js --parallel
```

## Test Categories

### Unit Tests (`test-wrapper.js`, `test-install.js`)

- **Wrapper Tests**: Test wrapper.js functionality including:
  - Python executable detection
  - Version verification
  - Signal handling
  - Environment variable management
  - Process spawning
  - Error handling

- **Install Tests**: Test install.js functionality including:
  - Python installation detection
  - Virtual environment creation
  - Dependency installation
  - Installation verification
  - Cross-platform compatibility

### Integration Tests (`test-integration.js`)

- End-to-end workflow testing
- Real subprocess interaction
- MCP protocol communication
- Signal handling in practice
- Resource cleanup
- Performance testing

## Test Configuration

### Environment Variables

The test suite uses several environment variables:

```bash
# Test environment
NODE_ENV=test

# JustiFi API credentials (for testing)
JUSTIFI_CLIENT_ID=test_client_id
JUSTIFI_CLIENT_SECRET=test_client_secret
JUSTIFI_ENVIRONMENT=sandbox

# Test control variables
JUSTIFI_MCP_SKIP_INSTALL=true    # Skip installation in tests
JUSTIFI_MCP_NO_VENV=true         # Skip virtual environment creation
JUSTIFI_MCP_VERBOSE=true         # Enable verbose output
MONITOR_PERFORMANCE=true         # Enable performance monitoring
```

### Mocha Configuration

The test suite uses Mocha with the following configuration:

- **Timeout**: 30 seconds (configurable)
- **Reporter**: spec (configurable)
- **Colors**: enabled
- **Recursive**: enabled
- **Exit**: enabled

### Coverage Configuration

NYC (Istanbul) is used for coverage reporting with:

- **Minimum Coverage**: 80% statements, 75% branches, 80% functions, 80% lines
- **Output Formats**: text, html, lcov, json
- **Coverage Directory**: `./coverage`
- **Per-file Coverage**: enabled

## Writing Tests

### Test Structure

```javascript
describe('Feature Name', function() {
    let sandbox;
    
    beforeEach(function() {
        sandbox = sinon.createSandbox();
        // Setup mocks
    });
    
    afterEach(function() {
        sandbox.restore();
    });
    
    it('should test specific behavior', function() {
        // Test implementation
    });
});
```

### Using Test Utilities

```javascript
// Create temporary directory
const tempDir = global.testUtils.createTempDir();

// Clean up temporary directory
global.testUtils.cleanupTempDir(tempDir);

// Wait for condition
await global.testUtils.waitFor(() => condition);

// Create mock process
const mockProcess = global.testUtils.createMockProcess({
    env: { CUSTOM_VAR: 'value' }
});

// Create mock child process
const mockChild = global.testUtils.createMockChildProcess({
    on: sinon.stub()
});
```

### Mocking Best Practices

1. **Always restore mocks**: Use `sandbox.restore()` in `afterEach`
2. **Mock external dependencies**: Mock `child_process`, `fs`, `os`, etc.
3. **Test error conditions**: Mock failures and exceptions
4. **Use specific assertions**: Verify exact behavior, not just success

### Platform-Specific Tests

```javascript
it('should handle Windows platform', function() {
    if (!global.testUtils.isWindows) {
        this.skip();
    }
    // Windows-specific test
});

it('should handle Unix platforms', function() {
    if (global.testUtils.isWindows) {
        this.skip();
    }
    // Unix-specific test
});
```

## Continuous Integration

The test suite is designed to work in CI/CD environments:

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16, 18, 20]
    steps:
      - uses: actions/checkout@v3
      - name: Use Node.js ${{ matrix.node-version }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm run test:coverage
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
```

### Test Environment Detection

The test suite automatically detects CI environments and adjusts behavior:

- Skips interactive features
- Reduces timeouts in some cases
- Disables virtual environment creation
- Uses appropriate Python executables

## Troubleshooting

### Common Issues

1. **Python Not Found**: Ensure Python 3.11+ is in PATH
2. **Permission Errors**: Check file permissions and user access
3. **Timeout Errors**: Increase timeout with `--timeout` option
4. **Memory Issues**: Use `--max-old-space-size` for Node.js
5. **Platform Issues**: Check platform-specific test skips

### Debug Mode

Enable debug mode for verbose output:

```bash
DEBUG=* npm test
JUSTIFI_MCP_VERBOSE=true npm test
MONITOR_PERFORMANCE=true npm test
```

### Test Isolation

If tests are interfering with each other:

```bash
# Run tests sequentially
npm run test:unit -- --bail

# Run specific test file
node test/test-runner.js test-wrapper.js

# Clear coverage and temp files
rm -rf coverage .nyc_output
```

## Performance Monitoring

The test suite includes performance monitoring:

- **Slow Test Detection**: Warns about tests taking >5 seconds
- **Memory Usage**: Monitors memory consumption
- **Resource Cleanup**: Verifies proper cleanup
- **CI Performance**: Optimized for CI/CD environments

## Contributing

When adding new tests:

1. Follow existing test structure and naming conventions
2. Add appropriate mocks and stubs
3. Test both success and failure scenarios
4. Include performance and resource cleanup tests
5. Update this README if adding new test categories
6. Ensure tests pass on all supported platforms

## Coverage Reports

Coverage reports are generated in the `./coverage` directory:

- **HTML Report**: `coverage/index.html`
- **LCOV Report**: `coverage/lcov.info`
- **JSON Report**: `coverage/coverage-final.json`
- **Text Report**: Displayed in console

Target coverage thresholds:
- **Statements**: 80%
- **Branches**: 75%  
- **Functions**: 80%
- **Lines**: 80%