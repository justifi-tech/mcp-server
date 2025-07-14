#!/usr/bin/env node
/**
 * JustiFi MCP Server Installation Script
 * 
 * This script handles the installation of Python dependencies and
 * environment setup for the JustiFi MCP server. It runs automatically
 * during npm install via the postinstall hook.
 */

const { spawn, spawnSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Configuration
const PYTHON_EXECUTABLES = ['python3', 'python', 'py'];
const PACKAGE_ROOT = path.dirname(__filename);
const SERVER_ROOT = path.resolve(PACKAGE_ROOT, '..');
const PYPROJECT_PATH = path.join(SERVER_ROOT, 'pyproject.toml');
const MINIMUM_PYTHON_VERSION = [3, 11];

/**
 * Log messages with timestamps
 */
function log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [${level}] ${message}`);
}

/**
 * Find available Python executable
 */
function findPythonExecutable() {
    log('Searching for Python executable...');
    
    for (const executable of PYTHON_EXECUTABLES) {
        try {
            const result = spawnSync(executable, ['--version'], {
                stdio: 'pipe',
                timeout: 5000
            });
            
            if (result.status === 0) {
                const version = result.stdout.toString().trim();
                log(`Found Python executable: ${executable} (${version})`);
                return executable;
            }
        } catch (error) {
            // Continue to next executable
        }
    }
    
    return null;
}

/**
 * Verify Python version meets requirements
 */
function verifyPythonVersion(pythonExecutable) {
    log('Verifying Python version...');
    
    try {
        const result = spawnSync(pythonExecutable, [
            '-c', 
            'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")'
        ], {
            stdio: 'pipe',
            timeout: 5000
        });
        
        if (result.status !== 0) {
            throw new Error('Failed to check Python version');
        }
        
        const version = result.stdout.toString().trim();
        const [major, minor, micro] = version.split('.').map(Number);
        
        if (major < MINIMUM_PYTHON_VERSION[0] || 
            (major === MINIMUM_PYTHON_VERSION[0] && minor < MINIMUM_PYTHON_VERSION[1])) {
            throw new Error(
                `Python ${version} is not supported. Please install Python ${MINIMUM_PYTHON_VERSION.join('.')} or later.`
            );
        }
        
        log(`Python version ${version} is compatible`);
        return version;
    } catch (error) {
        throw new Error(`Failed to verify Python version: ${error.message}`);
    }
}

/**
 * Check if pip is available
 */
function checkPipAvailable(pythonExecutable) {
    log('Checking pip availability...');
    
    try {
        const result = spawnSync(pythonExecutable, ['-m', 'pip', '--version'], {
            stdio: 'pipe',
            timeout: 5000
        });
        
        if (result.status === 0) {
            const version = result.stdout.toString().trim();
            log(`pip is available: ${version}`);
            return true;
        }
        
        return false;
    } catch (error) {
        return false;
    }
}

/**
 * Install pip if not available
 */
function installPip(pythonExecutable) {
    log('Installing pip...');
    
    try {
        const result = spawnSync(pythonExecutable, ['-m', 'ensurepip', '--upgrade'], {
            stdio: 'inherit',
            timeout: 30000
        });
        
        if (result.status !== 0) {
            throw new Error('Failed to install pip');
        }
        
        log('pip installed successfully');
    } catch (error) {
        throw new Error(`Failed to install pip: ${error.message}`);
    }
}

/**
 * Check if virtual environment should be created
 */
function shouldCreateVirtualEnv() {
    // Don't create virtual environment if:
    // 1. We're already in a virtual environment
    // 2. We're in a CI environment
    
    if (process.env.VIRTUAL_ENV) {
        log('Already in virtual environment, skipping creation');
        return false;
    }
    
    if (process.env.CI || process.env.GITHUB_ACTIONS) {
        log('CI environment detected, skipping virtual environment creation');
        return false;
    }
    
    return true;
}

/**
 * Check if global installation is explicitly allowed
 */
function isGlobalInstallationAllowed() {
    return process.env.JUSTIFI_MCP_ALLOW_GLOBAL === 'true';
}

/**
 * Create virtual environment
 */
function createVirtualEnvironment(pythonExecutable) {
    const venvPath = path.join(SERVER_ROOT, '.venv');
    
    if (fs.existsSync(venvPath)) {
        log('Virtual environment already exists');
        return venvPath;
    }
    
    log('Creating virtual environment...');
    
    try {
        const result = spawnSync(pythonExecutable, ['-m', 'venv', venvPath], {
            stdio: 'inherit',
            timeout: 30000
        });
        
        if (result.status !== 0) {
            throw new Error('Failed to create virtual environment');
        }
        
        log(`Virtual environment created at: ${venvPath}`);
        return venvPath;
    } catch (error) {
        throw new Error(`Failed to create virtual environment: ${error.message}`);
    }
}

/**
 * Get Python executable from virtual environment
 */
function getVenvPythonExecutable(venvPath) {
    const isWindows = os.platform() === 'win32';
    const pythonExecutable = isWindows 
        ? path.join(venvPath, 'Scripts', 'python.exe')
        : path.join(venvPath, 'bin', 'python');
    
    if (!fs.existsSync(pythonExecutable)) {
        throw new Error(`Python executable not found in virtual environment: ${pythonExecutable}`);
    }
    
    return pythonExecutable;
}

/**
 * Install Python dependencies
 */
function installPythonDependencies(pythonExecutable) {
    log('Installing Python dependencies...');
    
    if (!fs.existsSync(PYPROJECT_PATH)) {
        throw new Error(`pyproject.toml not found at ${PYPROJECT_PATH}`);
    }
    
    // Upgrade pip first
    log('Upgrading pip...');
    const upgradeResult = spawnSync(pythonExecutable, ['-m', 'pip', 'install', '--upgrade', 'pip'], {
        stdio: 'inherit',
        cwd: SERVER_ROOT
    });
    
    if (upgradeResult.status !== 0) {
        log('Warning: Failed to upgrade pip, continuing with current version', 'WARNING');
    }
    
    // Install package in editable mode
    log('Installing JustiFi MCP Server...');
    const installResult = spawnSync(pythonExecutable, [
        '-m', 'pip', 'install', '-e', '.'
    ], {
        stdio: 'inherit',
        cwd: SERVER_ROOT
    });
    
    if (installResult.status !== 0) {
        throw new Error('Failed to install Python dependencies');
    }
    
    log('Python dependencies installed successfully');
}

/**
 * Verify installation by importing key modules
 */
function verifyInstallation(pythonExecutable) {
    log('Verifying installation...');
    
    try {
        const result = spawnSync(pythonExecutable, [
            '-c', 
            'import mcp, fastmcp, httpx, pydantic; print("All dependencies imported successfully")'
        ], {
            stdio: 'pipe',
            timeout: 10000,
            cwd: SERVER_ROOT
        });
        
        if (result.status !== 0) {
            const error = result.stderr.toString().trim();
            throw new Error(`Import verification failed: ${error}`);
        }
        
        log('Installation verification passed');
    } catch (error) {
        throw new Error(`Installation verification failed: ${error.message}`);
    }
}

/**
 * Create installation summary
 */
function createInstallationSummary(pythonExecutable, pythonVersion, venvPath) {
    log('Installation completed successfully!');
    log(`Python executable: ${pythonExecutable}`);
    log(`Python version: ${pythonVersion}`);
    
    if (venvPath) {
        log(`Virtual environment: ${venvPath}`);
    }
    
    log('Server root: ' + SERVER_ROOT);
    log('');
    log('Next steps:');
    log('1. Set your JustiFi API credentials:');
    log('   export JUSTIFI_CLIENT_ID="your_client_id"');
    log('   export JUSTIFI_CLIENT_SECRET="your_client_secret"');
    log('');
    log('2. Test the installation:');
    log('   npx @justifi/mcp-server --health-check');
    log('');
    log('3. Use with Claude Desktop or other MCP clients');
}

/**
 * Handle installation errors
 */
function handleInstallationError(error) {
    log(`Installation failed: ${error.message}`, 'ERROR');
    log('');
    log('Troubleshooting:');
    log('1. Ensure Python 3.11+ is installed and in your PATH');
    log('2. Check that pip is available and working');
    log('3. Verify you have write permissions to the installation directory');
    log('4. For virtual environment issues, ensure venv module is available');
    log('5. To allow global installation (not recommended):');
    log('   JUSTIFI_MCP_ALLOW_GLOBAL=true npm install');
    log('6. Try running with verbose output:');
    log('   JUSTIFI_MCP_VERBOSE=true npm install');
    log('');
    log('If the problem persists, please file an issue at:');
    log('https://github.com/justifi-tech/mcp-servers/issues');
    
    process.exit(1);
}

/**
 * Main installation function
 */
async function main() {
    try {
        log('Starting JustiFi MCP Server installation...');
        log(`Platform: ${os.platform()} ${os.arch()}`);
        log(`Node.js: ${process.version}`);
        log(`Package root: ${PACKAGE_ROOT}`);
        log(`Server root: ${SERVER_ROOT}`);
        
        // Skip installation if explicitly disabled
        if (process.env.JUSTIFI_MCP_SKIP_INSTALL === 'true') {
            log('Installation skipped by user configuration');
            return;
        }
        
        // Find Python executable
        let pythonExecutable = findPythonExecutable();
        if (!pythonExecutable) {
            throw new Error(
                'Python not found. Please install Python 3.11+ and ensure it\'s in your PATH.\n' +
                `Searched for: ${PYTHON_EXECUTABLES.join(', ')}`
            );
        }
        
        // Verify Python version
        const pythonVersion = verifyPythonVersion(pythonExecutable);
        
        // Check pip availability
        if (!checkPipAvailable(pythonExecutable)) {
            installPip(pythonExecutable);
        }
        
        // Handle virtual environment - require by default for user safety
        let venvPath = null;
        if (shouldCreateVirtualEnv()) {
            try {
                venvPath = createVirtualEnvironment(pythonExecutable);
                pythonExecutable = getVenvPythonExecutable(venvPath);
            } catch (error) {
                if (!isGlobalInstallationAllowed()) {
                    throw new Error(
                        `Failed to create virtual environment: ${error.message}\n\n` +
                        `To protect your system, global package installation is disabled by default.\n` +
                        `Options:\n` +
                        `1. Fix virtual environment issues (recommended)\n` +
                        `2. Allow global installation: JUSTIFI_MCP_ALLOW_GLOBAL=true npm install\n\n` +
                        `Warning: Global installation may conflict with other Python packages.`
                    );
                }
                log('Virtual environment creation failed, proceeding with global installation (user override)', 'WARNING');
            }
        } else if (!process.env.VIRTUAL_ENV && !isGlobalInstallationAllowed()) {
            throw new Error(
                `Virtual environment required for installation.\n\n` +
                `To protect your system, global package installation is disabled by default.\n` +
                `Options:\n` +
                `1. Create a virtual environment first (recommended)\n` +
                `2. Allow global installation: JUSTIFI_MCP_ALLOW_GLOBAL=true npm install\n\n` +
                `Warning: Global installation may conflict with other Python packages.`
            );
        }
        
        // Install dependencies
        installPythonDependencies(pythonExecutable);
        
        // Verify installation
        verifyInstallation(pythonExecutable);
        
        // Create summary
        createInstallationSummary(pythonExecutable, pythonVersion, venvPath);
        
    } catch (error) {
        handleInstallationError(error);
    }
}

// Run installation if this script is executed directly
if (require.main === module) {
    main();
}

module.exports = { 
    main, 
    findPythonExecutable, 
    verifyPythonVersion,
    installPythonDependencies,
    verifyInstallation
};