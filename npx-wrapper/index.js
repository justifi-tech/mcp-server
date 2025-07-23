#!/usr/bin/env node
/**
 * JustiFi MCP Server - Simple NPX Wrapper with Virtual Environment
 * 
 * This wrapper automatically creates a virtual environment and installs
 * Python dependencies in isolation, then spawns the MCP server with
 * proper stdio passthrough for seamless MCP protocol communication.
 */

const { spawn, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Configuration
const PYTHON_COMMANDS = ['python3', 'python', 'py'];
const PACKAGE_ROOT = __dirname;
const MAIN_SCRIPT = path.join(PACKAGE_ROOT, 'main.py');
const REQUIREMENTS_FILE = path.join(PACKAGE_ROOT, 'requirements.txt');
const VENV_DIR = path.join(PACKAGE_ROOT, '.venv');

// Get virtual environment Python executable path
const VENV_PYTHON = os.platform() === 'win32'
    ? path.join(VENV_DIR, 'Scripts', 'python.exe')
    : path.join(VENV_DIR, 'bin', 'python');

/**
 * Log to stderr (stdout reserved for MCP protocol)
 */
function log(message) {
    console.error(`[JustiFi MCP] ${message}`);
}

/**
 * Find available Python executable
 */
function findPython() {
    for (const cmd of PYTHON_COMMANDS) {
        try {
            const result = spawnSync(cmd, ['--version'], {
                stdio: 'pipe',
                timeout: 5000
            });
            if (result.status === 0) {
                return cmd;
            }
        } catch (error) {
            // Continue to next command
        }
    }
    throw new Error(
        `Python not found. Please install Python 3.11+ and ensure it's in your PATH.\n` +
        `Tried: ${PYTHON_COMMANDS.join(', ')}`
    );
}

/**
 * Verify Python version is compatible
 */
function verifyPython(pythonCmd) {
    try {
        const result = spawnSync(pythonCmd, [
            '-c',
            'import sys; exit(0 if sys.version_info >= (3, 11) else 1)'
        ], { stdio: 'pipe', timeout: 5000 });

        if (result.status !== 0) {
            throw new Error('Python 3.11+ required');
        }
    } catch (error) {
        throw new Error(`Python version check failed: ${error.message}`);
    }
}

/**
 * Check if virtual environment exists and is valid
 */
function isVenvValid() {
    return fs.existsSync(VENV_PYTHON);
}

/**
 * Create virtual environment
 */
function createVenv(pythonCmd) {
    log('Creating virtual environment...');

    const result = spawnSync(pythonCmd, ['-m', 'venv', VENV_DIR], {
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 30000
    });

    if (result.status !== 0) {
        const error = result.stderr?.toString() || 'Unknown error';
        throw new Error(`Failed to create virtual environment: ${error}`);
    }

    log('Virtual environment created successfully');
}

/**
 * Install Python dependencies in virtual environment
 */
function installDependencies() {
    log('Installing Python dependencies...');

    // First upgrade pip
    const upgradeResult = spawnSync(VENV_PYTHON, ['-m', 'pip', 'install', '--upgrade', 'pip'], {
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 30000
    });

    if (upgradeResult.status !== 0) {
        log('Warning: Failed to upgrade pip, continuing...');
    }

    // Install requirements
    const installResult = spawnSync(VENV_PYTHON, ['-m', 'pip', 'install', '-r', REQUIREMENTS_FILE], {
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 120000  // 2 minutes for dependency installation
    });

    if (installResult.status !== 0) {
        const error = installResult.stderr?.toString() || 'Unknown error';
        throw new Error(`Failed to install dependencies: ${error}`);
    }

    log('Dependencies installed successfully');
}

/**
 * Check if dependencies are installed in virtual environment
 */
function areDependenciesInstalled() {
    if (!isVenvValid()) {
        return false;
    }

    // Try to import key dependencies
    const result = spawnSync(VENV_PYTHON, [
        '-c',
        'import mcp, fastmcp, httpx, pydantic; print("OK")'
    ], {
        stdio: 'pipe',
        timeout: 10000
    });

    return result.status === 0;
}

/**
 * Setup virtual environment and dependencies
 */
function setupEnvironment() {
    const pythonCmd = findPython();
    verifyPython(pythonCmd);

    // Check if we need to create virtual environment
    if (!isVenvValid()) {
        log('Virtual environment not found, creating...');
        createVenv(pythonCmd);
    }

    // Check if dependencies need to be installed
    if (!areDependenciesInstalled()) {
        log('Dependencies not found, installing...');
        installDependencies();
    } else {
        log('Dependencies already installed');
    }
}

/**
 * Verify server files exist
 */
function verifyServerFiles() {
    if (!fs.existsSync(MAIN_SCRIPT)) {
        throw new Error(`Server script not found: ${MAIN_SCRIPT}`);
    }
    if (!fs.existsSync(REQUIREMENTS_FILE)) {
        throw new Error(`Requirements file not found: ${REQUIREMENTS_FILE}`);
    }
}

/**
 * Show help
 */
function showHelp() {
    console.error(`
JustiFi MCP Server

Usage:
  npx @justifi/mcp-server [options]

Options:
  --help     Show this help
  --version  Show version
  --clean    Clean virtual environment and reinstall dependencies

Environment Variables:
  JUSTIFI_CLIENT_ID       JustiFi API client ID (required)
  JUSTIFI_CLIENT_SECRET   JustiFi API client secret (required)
  JUSTIFI_ENVIRONMENT     API environment (sandbox/production, default: sandbox)

Example Claude Desktop config:
{
  "mcpServers": {
    "justifi": {
      "command": "npx",
      "args": ["@justifi/mcp-server"],
      "env": {
        "JUSTIFI_CLIENT_ID": "your_client_id",
        "JUSTIFI_CLIENT_SECRET": "your_client_secret"
      }
    }
  }
}

Note: This package automatically creates and manages a Python virtual
environment to avoid conflicts with your system Python packages.
`);
}

/**
 * Show version
 */
function showVersion() {
    const pkg = require('./package.json');
    console.error(`JustiFi MCP Server v${pkg.version}`);

    try {
        if (isVenvValid()) {
            const result = spawnSync(VENV_PYTHON, ['--version'], { stdio: 'pipe' });
            if (result.status === 0) {
                const version = result.stdout.toString().trim();
                console.error(`Python (venv): ${version}`);
            }
        }
    } catch (error) {
        // Ignore version check errors
    }
}

/**
 * Clean virtual environment
 */
function cleanEnvironment() {
    log('Cleaning virtual environment...');

    if (fs.existsSync(VENV_DIR)) {
        fs.rmSync(VENV_DIR, { recursive: true, force: true });
        log('Virtual environment removed');
    } else {
        log('No virtual environment to clean');
    }
}

/**
 * Main function
 */
function main() {
    const args = process.argv.slice(2);

    // Handle special arguments
    if (args.includes('--help')) {
        showHelp();
        return;
    }

    if (args.includes('--version')) {
        showVersion();
        return;
    }

    if (args.includes('--clean')) {
        cleanEnvironment();
        log('Run again to reinstall dependencies');
        return;
    }

    try {
        // Verify server files exist
        verifyServerFiles();

        // Setup virtual environment and dependencies
        setupEnvironment();

        // Filter out our special args before passing to Python
        const pythonArgs = args.filter(arg => !['--clean'].includes(arg));

        log('Starting JustiFi MCP Server...');

        // Spawn Python server with stdio passthrough
        const serverProcess = spawn(VENV_PYTHON, [MAIN_SCRIPT, ...pythonArgs], {
            stdio: 'inherit',  // Direct passthrough for MCP protocol
            cwd: PACKAGE_ROOT,
            env: { ...process.env }
        });

        // Handle process events
        serverProcess.on('error', (error) => {
            console.error(`Failed to start server: ${error.message}`);
            process.exit(1);
        });

        serverProcess.on('exit', (code) => {
            process.exit(code || 0);
        });

        // Forward signals to Python process
        ['SIGINT', 'SIGTERM'].forEach(signal => {
            process.on(signal, () => {
                serverProcess.kill(signal);
            });
        });

    } catch (error) {
        console.error(`Error: ${error.message}`);
        process.exit(1);
    }
}

// Run if called directly
if (require.main === module) {
    main();
}

module.exports = { main }; 