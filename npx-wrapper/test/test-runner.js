#!/usr/bin/env node
/**
 * Cross-platform test runner for NPX wrapper
 * 
 * Features:
 * - Cross-platform test execution
 * - Test reporting and coverage
 * - CI/CD friendly output
 * - Selective test execution
 * - Performance monitoring
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Configuration
const TEST_DIR = __dirname;
const ROOT_DIR = path.dirname(TEST_DIR);
const TEST_FILES = [
    'test-wrapper.js',
    'test-install.js',
    'test-integration.js'
];

// Test runner options
const DEFAULT_OPTIONS = {
    reporter: 'spec',
    timeout: 30000,
    bail: false,
    colors: true,
    recursive: false,
    coverage: false,
    watch: false,
    grep: null,
    parallel: false
};

/**
 * Log messages with colors and formatting
 */
function log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    const colors = {
        ERROR: '\x1b[31m',   // Red
        WARN: '\x1b[33m',    // Yellow
        INFO: '\x1b[36m',    // Cyan
        SUCCESS: '\x1b[32m', // Green
        RESET: '\x1b[0m'     // Reset
    };

    const color = colors[level] || colors.INFO;
    const reset = colors.RESET;
    
    console.log(`${color}[${timestamp}] [${level}] ${message}${reset}`);
}

/**
 * Check if required dependencies are installed
 */
function checkDependencies() {
    log('Checking test dependencies...');
    
    const packageJsonPath = path.join(ROOT_DIR, 'package.json');
    if (!fs.existsSync(packageJsonPath)) {
        throw new Error('package.json not found');
    }

    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    const devDependencies = packageJson.devDependencies || {};
    
    const requiredDeps = ['mocha', 'chai', 'sinon'];
    const missingDeps = requiredDeps.filter(dep => !devDependencies[dep]);
    
    if (missingDeps.length > 0) {
        throw new Error(`Missing test dependencies: ${missingDeps.join(', ')}`);
    }

    log('All test dependencies are available');
}

/**
 * Check if test files exist
 */
function checkTestFiles() {
    log('Checking test files...');
    
    const missingFiles = TEST_FILES.filter(file => {
        const filePath = path.join(TEST_DIR, file);
        return !fs.existsSync(filePath);
    });

    if (missingFiles.length > 0) {
        throw new Error(`Missing test files: ${missingFiles.join(', ')}`);
    }

    log(`Found ${TEST_FILES.length} test files`);
}

/**
 * Parse command line arguments
 */
function parseArgs() {
    const args = process.argv.slice(2);
    const options = { ...DEFAULT_OPTIONS };
    const testFiles = [];

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];
        
        switch (arg) {
            case '--reporter':
                options.reporter = args[++i];
                break;
            case '--timeout':
                options.timeout = parseInt(args[++i], 10);
                break;
            case '--bail':
                options.bail = true;
                break;
            case '--no-colors':
                options.colors = false;
                break;
            case '--coverage':
                options.coverage = true;
                break;
            case '--watch':
                options.watch = true;
                break;
            case '--grep':
                options.grep = args[++i];
                break;
            case '--parallel':
                options.parallel = true;
                break;
            case '--unit':
                testFiles.push('test-wrapper.js', 'test-install.js');
                break;
            case '--integration':
                testFiles.push('test-integration.js');
                break;
            case '--help':
                showHelp();
                process.exit(0);
                break;
            default:
                if (arg.startsWith('--')) {
                    log(`Unknown option: ${arg}`, 'WARN');
                } else if (arg.endsWith('.js')) {
                    testFiles.push(arg);
                }
                break;
        }
    }

    // If no specific test files specified, run all
    if (testFiles.length === 0) {
        testFiles.push(...TEST_FILES);
    }

    return { options, testFiles };
}

/**
 * Show help information
 */
function showHelp() {
    console.log(`
NPX Wrapper Test Runner

Usage:
  npm test                    Run all tests
  npm run test:unit          Run unit tests only
  npm run test:integration   Run integration tests only
  npm run test:coverage      Run tests with coverage
  npm run test:watch         Run tests in watch mode

Options:
  --reporter <reporter>      Test reporter (spec, json, tap, etc.)
  --timeout <ms>            Test timeout in milliseconds
  --bail                    Stop on first failure
  --no-colors               Disable colored output
  --coverage                Generate coverage report
  --watch                   Watch for file changes
  --grep <pattern>          Run tests matching pattern
  --parallel                Run tests in parallel
  --unit                    Run unit tests only
  --integration             Run integration tests only
  --help                    Show this help

Examples:
  node test/test-runner.js --reporter json
  node test/test-runner.js --grep "Python"
  node test/test-runner.js --unit --coverage
  node test/test-runner.js test-wrapper.js
`);
}

/**
 * Get system information
 */
function getSystemInfo() {
    return {
        platform: os.platform(),
        arch: os.arch(),
        nodeVersion: process.version,
        cpus: os.cpus().length,
        memory: Math.round(os.totalmem() / 1024 / 1024 / 1024) + 'GB'
    };
}

/**
 * Run tests using Mocha
 */
function runTests(testFiles, options) {
    return new Promise((resolve, reject) => {
        const mochaPath = path.join(ROOT_DIR, 'node_modules', '.bin', 'mocha');
        const isWindows = os.platform() === 'win32';
        const mochaCmd = isWindows ? `${mochaPath}.cmd` : mochaPath;
        
        // Build Mocha arguments
        const mochaArgs = [];
        
        // Add test files
        testFiles.forEach(file => {
            mochaArgs.push(path.join(TEST_DIR, file));
        });

        // Add options
        if (options.reporter) {
            mochaArgs.push('--reporter', options.reporter);
        }
        
        if (options.timeout) {
            mochaArgs.push('--timeout', options.timeout.toString());
        }
        
        if (options.bail) {
            mochaArgs.push('--bail');
        }
        
        if (!options.colors) {
            mochaArgs.push('--no-colors');
        }
        
        if (options.grep) {
            mochaArgs.push('--grep', options.grep);
        }
        
        if (options.parallel) {
            mochaArgs.push('--parallel');
        }
        
        if (options.watch) {
            mochaArgs.push('--watch');
        }

        log(`Running command: ${mochaCmd} ${mochaArgs.join(' ')}`);
        
        const child = spawn(mochaCmd, mochaArgs, {
            stdio: 'inherit',
            cwd: ROOT_DIR,
            env: {
                ...process.env,
                NODE_ENV: 'test'
            }
        });

        child.on('close', (code) => {
            if (code === 0) {
                resolve(code);
            } else {
                reject(new Error(`Tests failed with exit code ${code}`));
            }
        });

        child.on('error', (error) => {
            reject(error);
        });
    });
}

/**
 * Run tests with coverage using nyc
 */
function runTestsWithCoverage(testFiles, options) {
    return new Promise((resolve, reject) => {
        const nycPath = path.join(ROOT_DIR, 'node_modules', '.bin', 'nyc');
        const isWindows = os.platform() === 'win32';
        const nycCmd = isWindows ? `${nycPath}.cmd` : nycPath;
        
        // Build nyc arguments
        const nycArgs = [
            '--reporter', 'text',
            '--reporter', 'html',
            '--reporter', 'lcov',
            '--report-dir', './coverage',
            '--include', 'wrapper.js',
            '--include', 'install.js',
            '--exclude', 'test/**',
            'mocha'
        ];

        // Add test files
        testFiles.forEach(file => {
            nycArgs.push(path.join(TEST_DIR, file));
        });

        // Add Mocha options
        if (options.reporter) {
            nycArgs.push('--reporter', options.reporter);
        }
        
        if (options.timeout) {
            nycArgs.push('--timeout', options.timeout.toString());
        }

        log(`Running command: ${nycCmd} ${nycArgs.join(' ')}`);
        
        const child = spawn(nycCmd, nycArgs, {
            stdio: 'inherit',
            cwd: ROOT_DIR,
            env: {
                ...process.env,
                NODE_ENV: 'test'
            }
        });

        child.on('close', (code) => {
            if (code === 0) {
                resolve(code);
            } else {
                reject(new Error(`Tests with coverage failed with exit code ${code}`));
            }
        });

        child.on('error', (error) => {
            reject(error);
        });
    });
}

/**
 * Generate test report
 */
function generateReport(startTime, endTime, success, error) {
    const duration = endTime - startTime;
    const systemInfo = getSystemInfo();
    
    log('');
    log('='.repeat(60));
    log('TEST REPORT');
    log('='.repeat(60));
    log(`Status: ${success ? 'PASSED' : 'FAILED'}`);
    log(`Duration: ${duration}ms`);
    log(`Platform: ${systemInfo.platform} ${systemInfo.arch}`);
    log(`Node.js: ${systemInfo.nodeVersion}`);
    log(`CPUs: ${systemInfo.cpus}`);
    log(`Memory: ${systemInfo.memory}`);
    
    if (error) {
        log(`Error: ${error.message}`, 'ERROR');
    }
    
    log('='.repeat(60));
}

/**
 * Main test runner function
 */
async function main() {
    const startTime = Date.now();
    let success = false;
    let error = null;

    try {
        log('Starting NPX Wrapper Test Runner');
        log(`Platform: ${os.platform()} ${os.arch()}`);
        log(`Node.js: ${process.version}`);
        log(`Working directory: ${ROOT_DIR}`);

        // Parse command line arguments
        const { options, testFiles } = parseArgs();
        
        log(`Test files: ${testFiles.join(', ')}`);
        log(`Options: ${JSON.stringify(options, null, 2)}`);

        // Check dependencies and test files
        checkDependencies();
        checkTestFiles();

        // Run tests
        if (options.coverage) {
            log('Running tests with coverage...');
            await runTestsWithCoverage(testFiles, options);
        } else {
            log('Running tests...');
            await runTests(testFiles, options);
        }

        success = true;
        log('All tests completed successfully!', 'SUCCESS');

    } catch (err) {
        error = err;
        log(`Test runner failed: ${err.message}`, 'ERROR');
        
        // Additional error handling
        if (err.code === 'ENOENT') {
            log('Make sure you have run "npm install" to install test dependencies', 'ERROR');
        }
        
        if (err.message.includes('timeout')) {
            log('Some tests timed out. Consider increasing timeout or checking for hanging processes', 'ERROR');
        }
    } finally {
        const endTime = Date.now();
        generateReport(startTime, endTime, success, error);
        
        process.exit(success ? 0 : 1);
    }
}

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    log(`Uncaught exception: ${error.message}`, 'ERROR');
    process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
    log(`Unhandled promise rejection: ${reason}`, 'ERROR');
    process.exit(1);
});

// Handle signals
process.on('SIGINT', () => {
    log('Received SIGINT, shutting down gracefully...', 'WARN');
    process.exit(0);
});

process.on('SIGTERM', () => {
    log('Received SIGTERM, shutting down gracefully...', 'WARN');
    process.exit(0);
});

// Run the main function
if (require.main === module) {
    main();
}

module.exports = { main, runTests, runTestsWithCoverage };