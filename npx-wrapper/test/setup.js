/**
 * Test setup and configuration
 * 
 * This file is automatically loaded by Mocha before running tests.
 * It sets up global test configuration, utilities, and environment.
 */

const path = require('path');
const fs = require('fs');

// Set test environment
process.env.NODE_ENV = 'test';

// Increase timeout for slower systems
process.env.MOCHA_TIMEOUT = process.env.MOCHA_TIMEOUT || '30000';

// Global test configuration
global.TEST_ROOT = __dirname;
global.PROJECT_ROOT = path.dirname(__dirname);

// Test utilities
global.testUtils = {
    /**
     * Create temporary directory for tests
     */
    createTempDir: () => {
        const tmpDir = path.join(require('os').tmpdir(), 'npx-wrapper-test-' + Date.now());
        fs.mkdirSync(tmpDir, { recursive: true });
        return tmpDir;
    },

    /**
     * Clean up temporary directory
     */
    cleanupTempDir: (dir) => {
        if (fs.existsSync(dir)) {
            fs.rmSync(dir, { recursive: true, force: true });
        }
    },

    /**
     * Wait for a condition to be true
     */
    waitFor: (condition, timeout = 5000) => {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            const check = () => {
                if (condition()) {
                    resolve();
                } else if (Date.now() - startTime > timeout) {
                    reject(new Error('Timeout waiting for condition'));
                } else {
                    setTimeout(check, 100);
                }
            };
            check();
        });
    },

    /**
     * Create mock process object
     */
    createMockProcess: (overrides = {}) => {
        return {
            argv: ['node', 'test.js'],
            env: { ...process.env },
            exit: () => {},
            on: () => {},
            stdout: { write: () => {} },
            stderr: { write: () => {} },
            version: process.version,
            platform: process.platform,
            ...overrides
        };
    },

    /**
     * Create mock child process
     */
    createMockChildProcess: (overrides = {}) => {
        return {
            on: () => {},
            kill: () => {},
            stdout: { on: () => {} },
            stderr: { on: () => {} },
            stdin: { write: () => {}, end: () => {} },
            killed: false,
            pid: 12345,
            ...overrides
        };
    }
};

// Global test hooks
beforeEach(function() {
    // Reset environment variables
    this.originalEnv = { ...process.env };
    
    // Set common test environment variables
    process.env.NODE_ENV = 'test';
    process.env.JUSTIFI_CLIENT_ID = 'test_client_id';
    process.env.JUSTIFI_CLIENT_SECRET = 'test_client_secret';
    process.env.JUSTIFI_ENVIRONMENT = 'sandbox';
});

afterEach(function() {
    // Restore original environment variables
    process.env = this.originalEnv;
});

// Global error handling
process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
});

process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    process.exit(1);
});

// Platform-specific test configuration
if (process.platform === 'win32') {
    // Windows-specific test setup
    global.testUtils.pythonExecutables = ['python.exe', 'py.exe'];
    global.testUtils.isWindows = true;
} else {
    // Unix-like systems
    global.testUtils.pythonExecutables = ['python3', 'python'];
    global.testUtils.isWindows = false;
}

// CI/CD environment detection
global.testUtils.isCI = !!(
    process.env.CI ||
    process.env.GITHUB_ACTIONS ||
    process.env.GITLAB_CI ||
    process.env.CIRCLECI ||
    process.env.TRAVIS ||
    process.env.JENKINS_URL
);

// Test performance monitoring
if (process.env.MONITOR_PERFORMANCE) {
    const originalIt = global.it;
    global.it = function(description, fn) {
        return originalIt(description, function() {
            const start = Date.now();
            const result = fn.call(this);
            
            if (result && typeof result.then === 'function') {
                return result.then(
                    (value) => {
                        const duration = Date.now() - start;
                        if (duration > 5000) {
                            console.warn(`Slow test: "${description}" took ${duration}ms`);
                        }
                        return value;
                    },
                    (error) => {
                        const duration = Date.now() - start;
                        console.error(`Failed test: "${description}" took ${duration}ms`);
                        throw error;
                    }
                );
            } else {
                const duration = Date.now() - start;
                if (duration > 5000) {
                    console.warn(`Slow test: "${description}" took ${duration}ms`);
                }
                return result;
            }
        });
    };
}

console.log('Test environment initialized');
console.log(`Platform: ${process.platform} ${process.arch}`);
console.log(`Node.js: ${process.version}`);
console.log(`Test root: ${global.TEST_ROOT}`);
console.log(`Project root: ${global.PROJECT_ROOT}`);
console.log(`CI environment: ${global.testUtils.isCI}`);
console.log(`Performance monitoring: ${!!process.env.MONITOR_PERFORMANCE}`);