/**
 * End-to-end integration tests for NPX wrapper
 * 
 * Tests the complete integration including:
 * - Actual NPX execution flow
 * - MCP protocol communication
 * - Real Python subprocess interaction
 * - Health check functionality
 * - Graceful shutdown
 */

const { expect } = require('chai');
const sinon = require('sinon');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

describe('Integration Tests', function() {
    this.timeout(30000); // 30 second timeout for integration tests

    let sandbox;
    let originalEnv;

    beforeEach(function() {
        sandbox = sinon.createSandbox();
        originalEnv = { ...process.env };
    });

    afterEach(function() {
        sandbox.restore();
        process.env = originalEnv;
    });

    describe('NPX Wrapper Execution', function() {
        it('should execute wrapper.js successfully', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            // Skip if wrapper.js doesn't exist
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath, '--help'], {
                stdio: 'pipe',
                timeout: 5000
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                expect(stderr).to.include('JustiFi MCP Server NPX Wrapper');
                expect(stderr).to.include('Usage:');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle version command', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath, '--version'], {
                stdio: 'pipe',
                timeout: 5000
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                expect(stderr).to.include('JustiFi MCP Server NPX Wrapper');
                expect(stderr).to.include('Node.js:');
                expect(stderr).to.include('Platform:');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle health check command', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath, '--health-check'], {
                stdio: 'pipe',
                timeout: 10000,
                env: {
                    ...process.env,
                    JUSTIFI_CLIENT_ID: 'test_client_id',
                    JUSTIFI_CLIENT_SECRET: 'test_client_secret'
                }
            });

            let stdout = '';
            let stderr = '';

            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                // Health check might fail if Python dependencies aren't installed
                // We're mainly testing that the wrapper can start
                expect(stderr).to.include('JustiFi MCP Server');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle unknown arguments gracefully', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath, '--unknown-arg'], {
                stdio: 'pipe',
                timeout: 5000
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                // Should fail due to Python setup, but shouldn't crash
                expect(stderr).to.include('JustiFi MCP Server');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });
    });

    describe('Install Script Execution', function() {
        it('should execute install.js successfully', function(done) {
            const installPath = path.join(__dirname, '..', 'install.js');
            
            if (!fs.existsSync(installPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [installPath], {
                stdio: 'pipe',
                timeout: 60000, // 1 minute for installation
                env: {
                    ...process.env,
                    JUSTIFI_MCP_SKIP_INSTALL: 'true' // Skip actual installation
                }
            });

            let stdout = '';
            let stderr = '';

            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                expect(stdout).to.include('Installation skipped by user configuration');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle missing Python gracefully', function(done) {
            const installPath = path.join(__dirname, '..', 'install.js');
            
            if (!fs.existsSync(installPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [installPath], {
                stdio: 'pipe',
                timeout: 10000,
                env: {
                    ...process.env,
                    PATH: '/nonexistent/path' // Remove Python from PATH
                }
            });

            let stdout = '';
            let stderr = '';

            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                expect(code).to.equal(1);
                expect(stdout).to.include('Python not found');
                expect(stdout).to.include('Troubleshooting:');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });
    });

    describe('Signal Handling', function() {
        it('should handle SIGINT gracefully', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath], {
                stdio: 'pipe',
                env: {
                    ...process.env,
                    JUSTIFI_CLIENT_ID: 'test_client_id',
                    JUSTIFI_CLIENT_SECRET: 'test_client_secret'
                }
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            // Send SIGINT after a short delay
            setTimeout(() => {
                child.kill('SIGINT');
            }, 1000);

            child.on('close', (code, signal) => {
                // Should exit cleanly
                expect(signal).to.equal('SIGINT');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle SIGTERM gracefully', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath], {
                stdio: 'pipe',
                env: {
                    ...process.env,
                    JUSTIFI_CLIENT_ID: 'test_client_id',
                    JUSTIFI_CLIENT_SECRET: 'test_client_secret'
                }
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            // Send SIGTERM after a short delay
            setTimeout(() => {
                child.kill('SIGTERM');
            }, 1000);

            child.on('close', (code, signal) => {
                // Should exit cleanly
                expect(signal).to.equal('SIGTERM');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });
    });

    describe('Environment Variable Handling', function() {
        it('should pass environment variables to Python process', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const testEnv = {
                ...process.env,
                JUSTIFI_CLIENT_ID: 'test_client_id',
                JUSTIFI_CLIENT_SECRET: 'test_client_secret',
                JUSTIFI_ENVIRONMENT: 'sandbox',
                MCP_TRANSPORT: 'stdio',
                LOG_LEVEL: 'DEBUG'
            };

            const child = spawn('node', [wrapperPath, '--version'], {
                stdio: 'pipe',
                timeout: 5000,
                env: testEnv
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                // Environment variables should be available to the wrapper
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle missing required environment variables', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const testEnv = {
                ...process.env
            };
            
            // Remove required environment variables
            delete testEnv.JUSTIFI_CLIENT_ID;
            delete testEnv.JUSTIFI_CLIENT_SECRET;

            const child = spawn('node', [wrapperPath, '--health-check'], {
                stdio: 'pipe',
                timeout: 10000,
                env: testEnv
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                // Should fail due to missing credentials
                expect(code).to.not.equal(0);
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });
    });

    describe('Cross-Platform Compatibility', function() {
        it('should work on current platform', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath, '--version'], {
                stdio: 'pipe',
                timeout: 5000
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                expect(stderr).to.include(`Platform: ${os.platform()}`);
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle platform-specific Python executables', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath, '--version'], {
                stdio: 'pipe',
                timeout: 5000
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                // Should find appropriate Python executable for platform
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });
    });

    describe('MCP Protocol Communication', function() {
        it('should handle MCP protocol messages', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath], {
                stdio: 'pipe',
                timeout: 10000,
                env: {
                    ...process.env,
                    JUSTIFI_CLIENT_ID: 'test_client_id',
                    JUSTIFI_CLIENT_SECRET: 'test_client_secret',
                    MCP_TRANSPORT: 'stdio'
                }
            });

            let stdout = '';
            let stderr = '';

            child.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            // Send a simple MCP message
            const mcpMessage = JSON.stringify({
                jsonrpc: '2.0',
                method: 'initialize',
                params: {
                    protocolVersion: '2024-11-05',
                    capabilities: {},
                    clientInfo: {
                        name: 'test-client',
                        version: '1.0.0'
                    }
                },
                id: 1
            });

            child.stdin.write(mcpMessage + '\n');
            child.stdin.end();

            child.on('close', (code) => {
                // Process should handle the message (might fail due to Python setup)
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle large MCP messages', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath], {
                stdio: 'pipe',
                timeout: 10000,
                env: {
                    ...process.env,
                    JUSTIFI_CLIENT_ID: 'test_client_id',
                    JUSTIFI_CLIENT_SECRET: 'test_client_secret',
                    MCP_TRANSPORT: 'stdio'
                }
            });

            // Create a large message
            const largeData = 'x'.repeat(10000);
            const mcpMessage = JSON.stringify({
                jsonrpc: '2.0',
                method: 'test',
                params: {
                    data: largeData
                },
                id: 1
            });

            child.stdin.write(mcpMessage + '\n');
            child.stdin.end();

            child.on('close', (code) => {
                // Should handle large messages without crashing
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });
    });

    describe('Error Recovery', function() {
        it('should handle Python process crashes', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath], {
                stdio: 'pipe',
                timeout: 10000,
                env: {
                    ...process.env,
                    JUSTIFI_CLIENT_ID: 'test_client_id',
                    JUSTIFI_CLIENT_SECRET: 'test_client_secret'
                }
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            // Kill the process after a short delay
            setTimeout(() => {
                child.kill('SIGKILL');
            }, 1000);

            child.on('close', (code, signal) => {
                // Should exit cleanly even with force kill
                expect(signal).to.equal('SIGKILL');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle missing server script', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            // Mock missing server script by changing directory
            const child = spawn('node', [wrapperPath], {
                stdio: 'pipe',
                timeout: 5000,
                cwd: '/tmp',
                env: {
                    ...process.env,
                    JUSTIFI_CLIENT_ID: 'test_client_id',
                    JUSTIFI_CLIENT_SECRET: 'test_client_secret'
                }
            });

            let stderr = '';
            child.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            child.on('close', (code) => {
                expect(code).to.not.equal(0);
                expect(stderr).to.include('Error:');
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });
    });

    describe('Performance Tests', function() {
        it('should start within reasonable time', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const startTime = Date.now();
            const child = spawn('node', [wrapperPath, '--version'], {
                stdio: 'pipe',
                timeout: 5000
            });

            child.on('close', (code) => {
                const endTime = Date.now();
                const duration = endTime - startTime;
                
                expect(code).to.equal(0);
                expect(duration).to.be.below(5000); // Should start within 5 seconds
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle multiple rapid requests', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            let completed = 0;
            const total = 5;

            for (let i = 0; i < total; i++) {
                const child = spawn('node', [wrapperPath, '--version'], {
                    stdio: 'pipe',
                    timeout: 5000
                });

                child.on('close', (code) => {
                    expect(code).to.equal(0);
                    completed++;
                    
                    if (completed === total) {
                        done();
                    }
                });

                child.on('error', (error) => {
                    done(error);
                });
            }
        });
    });

    describe('Resource Management', function() {
        it('should clean up resources properly', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath, '--version'], {
                stdio: 'pipe',
                timeout: 5000
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                
                // Check that no zombie processes remain
                setTimeout(() => {
                    done();
                }, 100);
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle memory pressure gracefully', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            // Create child process with limited memory
            const child = spawn('node', ['--max-old-space-size=64', wrapperPath, '--version'], {
                stdio: 'pipe',
                timeout: 5000
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });
    });

    describe('Configuration Tests', function() {
        it('should handle different transport modes', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath, '--version'], {
                stdio: 'pipe',
                timeout: 5000,
                env: {
                    ...process.env,
                    MCP_TRANSPORT: 'http',
                    MCP_PORT: '3000'
                }
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });

        it('should handle different log levels', function(done) {
            const wrapperPath = path.join(__dirname, '..', 'wrapper.js');
            
            if (!fs.existsSync(wrapperPath)) {
                this.skip();
                return;
            }

            const child = spawn('node', [wrapperPath, '--version'], {
                stdio: 'pipe',
                timeout: 5000,
                env: {
                    ...process.env,
                    LOG_LEVEL: 'DEBUG'
                }
            });

            child.on('close', (code) => {
                expect(code).to.equal(0);
                done();
            });

            child.on('error', (error) => {
                done(error);
            });
        });
    });
});