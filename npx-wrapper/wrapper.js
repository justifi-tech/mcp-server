#!/usr/bin/env node
/**
 * JustiFi MCP Server NPX Wrapper
 * 
 * This wrapper script spawns the Python MCP server process with proper
 * stdio passthrough for the MCP protocol. It handles cross-platform
 * Python detection, environment variable passthrough, and graceful shutdown.
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

// Configuration
const PYTHON_EXECUTABLES = ['python3', 'python', 'py'];
const SERVER_SCRIPT = 'main.py';
const REQUIREMENTS_FILE = 'requirements.txt';
const PACKAGE_ROOT = path.dirname(__filename);
const SERVER_ROOT = path.resolve(PACKAGE_ROOT, '..');

// Global reference to child process for cleanup
let pythonProcess = null;

/**
 * Log messages to stderr (stdout is reserved for MCP protocol)
 */
function log(message, level = 'INFO') {
    const timestamp = new Date().toISOString();
    console.error(`[${timestamp}] [${level}] ${message}`);
}

/**
 * Find available Python executable
 */
function findPythonExecutable() {
    for (const executable of PYTHON_EXECUTABLES) {
        try {
            const result = require('child_process').spawnSync(executable, ['--version'], {
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
    
    throw new Error(
        `Python not found. Please install Python 3.11+ and ensure it's in your PATH.\n` +
        `Tried executables: ${PYTHON_EXECUTABLES.join(', ')}`
    );
}

/**
 * Verify Python version meets requirements
 */
function verifyPythonVersion(pythonExecutable) {
    try {
        const result = require('child_process').spawnSync(pythonExecutable, [
            '-c', 
            'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
        ], {
            stdio: 'pipe',
            timeout: 5000
        });
        
        if (result.status !== 0) {
            throw new Error('Failed to check Python version');
        }
        
        const version = result.stdout.toString().trim();
        const [major, minor] = version.split('.').map(Number);
        
        if (major < 3 || (major === 3 && minor < 11)) {
            throw new Error(
                `Python ${version} is not supported. Please install Python 3.11 or later.\n` +
                `Current version: ${version}`
            );
        }
        
        log(`Python version ${version} is compatible`);
        return version;
    } catch (error) {
        throw new Error(`Failed to verify Python version: ${error.message}`);
    }
}

/**
 * Check if Python dependencies are installed
 */
function checkPythonDependencies(pythonExecutable) {
    try {
        const result = require('child_process').spawnSync(pythonExecutable, [
            '-c', 
            'import mcp, fastmcp, httpx, pydantic; print("Dependencies OK")'
        ], {
            stdio: 'pipe',
            timeout: 10000,
            cwd: SERVER_ROOT
        });
        
        return result.status === 0;
    } catch (error) {
        return false;
    }
}

/**
 * Install Python dependencies
 */
function installPythonDependencies(pythonExecutable) {
    log('Installing Python dependencies...');
    
    const pyprojectPath = path.join(SERVER_ROOT, 'pyproject.toml');
    
    if (!fs.existsSync(pyprojectPath)) {
        throw new Error(`pyproject.toml not found at ${pyprojectPath}`);
    }
    
    // Install in editable mode from pyproject.toml
    const installProcess = require('child_process').spawnSync(pythonExecutable, [
        '-m', 'pip', 'install', '-e', '.'
    ], {
        stdio: 'inherit',
        cwd: SERVER_ROOT
    });
    
    if (installProcess.status !== 0) {
        throw new Error('Failed to install Python dependencies');
    }
    
    log('Python dependencies installed successfully');
}

/**
 * Setup graceful shutdown handlers
 */
function setupSignalHandlers() {
    const signals = ['SIGINT', 'SIGTERM', 'SIGQUIT'];
    
    signals.forEach(signal => {
        process.on(signal, () => {
            log(`Received ${signal}, shutting down gracefully...`);
            
            if (pythonProcess) {
                pythonProcess.kill(signal);
                
                // Force kill after 5 seconds
                setTimeout(() => {
                    if (pythonProcess && !pythonProcess.killed) {
                        log('Force killing Python process...');
                        pythonProcess.kill('SIGKILL');
                    }
                }, 5000);
            }
            
            process.exit(0);
        });
    });
    
    // Handle uncaught exceptions
    process.on('uncaughtException', (error) => {
        log(`Uncaught exception: ${error.message}`, 'ERROR');
        if (pythonProcess) {
            pythonProcess.kill('SIGTERM');
        }
        process.exit(1);
    });
    
    // Handle unhandled promise rejections
    process.on('unhandledRejection', (reason, promise) => {
        log(`Unhandled promise rejection: ${reason}`, 'ERROR');
        if (pythonProcess) {
            pythonProcess.kill('SIGTERM');
        }
        process.exit(1);
    });
}

/**
 * Get environment variables for Python process
 */
function getEnvironmentVariables() {
    const env = { ...process.env };
    
    // Ensure Python path includes the server root
    const pythonPath = env.PYTHONPATH || '';
    env.PYTHONPATH = pythonPath ? `${SERVER_ROOT}:${pythonPath}` : SERVER_ROOT;
    
    // Set working directory
    env.PWD = SERVER_ROOT;
    
    return env;
}

/**
 * Show help information
 */
function showHelp() {
    console.error(`
JustiFi MCP Server NPX Wrapper

Usage:
  npx @justifi/mcp-server [options]

Options:
  --help          Show this help message
  --health-check  Run health check and exit
  --version       Show version information

Environment Variables:
  JUSTIFI_CLIENT_ID       JustiFi API client ID (required)
  JUSTIFI_CLIENT_SECRET   JustiFi API client secret (required)
  JUSTIFI_ENVIRONMENT     API environment (sandbox/production, default: sandbox)
  MCP_TRANSPORT          Transport mode (stdio/http/sse, default: stdio)
  MCP_HOST               Host for HTTP/SSE transport (default: localhost)
  MCP_PORT               Port for HTTP/SSE transport (default: 3000)
  LOG_LEVEL              Logging level (DEBUG/INFO/WARNING/ERROR, default: INFO)

Examples:
  # Run with stdio transport (default)
  npx @justifi/mcp-server

  # Run with HTTP transport
  MCP_TRANSPORT=http MCP_PORT=3000 npx @justifi/mcp-server

  # Run health check
  npx @justifi/mcp-server --health-check

Configuration for Claude Desktop:
  Add to ~/.config/claude_desktop/claude_desktop_config.json:
  {
    "mcpServers": {
      "justifi": {
        "command": "npx",
        "args": ["@justifi/mcp-server"],
        "env": {
          "JUSTIFI_CLIENT_ID": "your_client_id",
          "JUSTIFI_CLIENT_SECRET": "your_client_secret",
          "JUSTIFI_ENVIRONMENT": "sandbox"
        }
      }
    }
  }
`);
}

/**
 * Show version information
 */
function showVersion() {
    const packageJson = require('./package.json');
    console.error(`JustiFi MCP Server NPX Wrapper v${packageJson.version}`);
    
    try {
        const pythonExecutable = findPythonExecutable();
        const pythonVersion = verifyPythonVersion(pythonExecutable);
        console.error(`Python: ${pythonVersion}`);
        console.error(`Node.js: ${process.version}`);
        console.error(`Platform: ${os.platform()} ${os.arch()}`);
    } catch (error) {
        console.error(`Python: not available (${error.message})`);
    }
}

/**
 * Main execution function
 */
async function main() {
    try {
        // Handle command line arguments
        const args = process.argv.slice(2);
        
        if (args.includes('--help')) {
            showHelp();
            process.exit(0);
        }
        
        if (args.includes('--version')) {
            showVersion();
            process.exit(0);
        }
        
        // Setup signal handlers
        setupSignalHandlers();
        
        // Find and verify Python
        const pythonExecutable = findPythonExecutable();
        verifyPythonVersion(pythonExecutable);
        
        // Check if dependencies are installed
        if (!checkPythonDependencies(pythonExecutable)) {
            log('Python dependencies not found, installing...');
            installPythonDependencies(pythonExecutable);
        }
        
        // Verify server script exists
        const serverScriptPath = path.join(SERVER_ROOT, SERVER_SCRIPT);
        if (!fs.existsSync(serverScriptPath)) {
            throw new Error(`Server script not found: ${serverScriptPath}`);
        }
        
        // Prepare Python process arguments
        const pythonArgs = [serverScriptPath, ...args];
        const env = getEnvironmentVariables();
        
        log(`Starting JustiFi MCP Server...`);
        log(`Python executable: ${pythonExecutable}`);
        log(`Server script: ${serverScriptPath}`);
        log(`Working directory: ${SERVER_ROOT}`);
        log(`Transport: ${env.MCP_TRANSPORT || 'stdio'}`);
        
        // Spawn Python process
        pythonProcess = spawn(pythonExecutable, pythonArgs, {
            stdio: 'inherit',
            env: env,
            cwd: SERVER_ROOT
        });
        
        // Handle Python process events
        pythonProcess.on('error', (error) => {
            log(`Failed to start Python process: ${error.message}`, 'ERROR');
            process.exit(1);
        });
        
        pythonProcess.on('exit', (code, signal) => {
            if (signal) {
                log(`Python process terminated by signal: ${signal}`);
            } else {
                log(`Python process exited with code: ${code}`);
            }
            
            process.exit(code || 0);
        });
        
        // Keep the wrapper process alive
        process.on('exit', () => {
            if (pythonProcess && !pythonProcess.killed) {
                pythonProcess.kill('SIGTERM');
            }
        });
        
    } catch (error) {
        log(`Error: ${error.message}`, 'ERROR');
        process.exit(1);
    }
}

// Run the main function
if (require.main === module) {
    main();
}

module.exports = { main, findPythonExecutable, verifyPythonVersion };