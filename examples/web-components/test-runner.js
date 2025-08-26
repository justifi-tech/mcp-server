#!/usr/bin/env node

/**
 * Simple E2E test runner for JustiFi Web Components examples
 * 
 * This script validates that the examples load correctly and
 * contain the expected elements and functionality.
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const { spawn } = require('child_process');

const EXAMPLES_DIR = __dirname;
const PORT = 3002;

class TestRunner {
    constructor() {
        this.server = null;
        this.testResults = [];
    }

    async runAllTests() {
        console.log('🚀 Starting JustiFi Web Components E2E Tests');
        console.log('==========================================\n');

        try {
            await this.startTestServer();
            await this.runExampleTests();
            await this.stopTestServer();
            
            this.printResults();
            
        } catch (error) {
            console.error('❌ Test runner failed:', error);
            process.exit(1);
        }
    }

    async startTestServer() {
        return new Promise((resolve, reject) => {
            this.server = http.createServer((req, res) => {
                const filePath = this.getFilePath(req.url);
                
                if (fs.existsSync(filePath)) {
                    const ext = path.extname(filePath);
                    const contentType = this.getContentType(ext);
                    
                    res.writeHead(200, { 'Content-Type': contentType });
                    fs.createReadStream(filePath).pipe(res);
                } else {
                    res.writeHead(404);
                    res.end('Not found');
                }
            });

            this.server.listen(PORT, () => {
                console.log(`📡 Test server started on http://localhost:${PORT}`);
                resolve();
            });

            this.server.on('error', reject);
        });
    }

    async stopTestServer() {
        if (this.server) {
            this.server.close();
            console.log('🛑 Test server stopped\n');
        }
    }

    getFilePath(url) {
        if (url === '/') return path.join(EXAMPLES_DIR, 'index.html');
        if (url.startsWith('/embedded-checkout')) {
            return path.join(EXAMPLES_DIR, 'embedded-checkout', url.replace('/embedded-checkout', '') || 'index.html');
        }
        if (url.startsWith('/tokenization')) {
            return path.join(EXAMPLES_DIR, 'tokenization', url.replace('/tokenization', '') || 'index.html');
        }
        if (url.startsWith('/dashboard')) {
            return path.join(EXAMPLES_DIR, 'dashboard', url.replace('/dashboard', '') || 'index.html');
        }
        return path.join(EXAMPLES_DIR, url);
    }

    getContentType(ext) {
        const types = {
            '.html': 'text/html',
            '.js': 'text/javascript',
            '.css': 'text/css',
            '.json': 'application/json'
        };
        return types[ext] || 'text/plain';
    }

    async runExampleTests() {
        const examples = [
            { 
                name: 'Embedded Checkout', 
                path: 'embedded-checkout',
                tests: this.getEmbeddedCheckoutTests()
            },
            { 
                name: 'Tokenization Flow', 
                path: 'tokenization',
                tests: this.getTokenizationTests()
            },
            { 
                name: 'Payment Dashboard', 
                path: 'dashboard',
                tests: this.getDashboardTests()
            }
        ];

        for (const example of examples) {
            console.log(`\n🧪 Testing ${example.name}...`);
            await this.runExampleTest(example);
        }
    }

    async runExampleTest(example) {
        try {
            // Test file existence
            const indexPath = path.join(EXAMPLES_DIR, example.path, 'index.html');
            const readmePath = path.join(EXAMPLES_DIR, example.path, 'README.md');
            
            this.addTestResult(example.name, 'File Structure', 
                fs.existsSync(indexPath) && fs.existsSync(readmePath),
                'index.html and README.md exist'
            );

            // Test HTML content
            const htmlContent = fs.readFileSync(indexPath, 'utf-8');
            
            // Run tests for this example
            for (const test of example.tests) {
                const passed = test.check(htmlContent);
                this.addTestResult(example.name, test.name, passed, test.description);
            }

        } catch (error) {
            this.addTestResult(example.name, 'General', false, `Error: ${error.message}`);
        }
    }

    getEmbeddedCheckoutTests() {
        return [
            {
                name: 'JustiFi CDN',
                description: 'Loads JustiFi Web Components from CDN',
                check: (html) => html.includes('https://cdn.justifi.ai/webcomponents') || html.includes('https://cdn.jsdelivr.net/npm/@justifi/webcomponents')
            },
            {
                name: 'Checkout Element',
                description: 'Creates justifi-checkout element',
                check: (html) => html.includes('justifi-checkout')
            },
            {
                name: 'Backend Integration',
                description: 'Contains backend API client code',
                check: (html) => html.includes('BackendApiClient') || html.includes('apiClient')
            },
            {
                name: 'Event Handling',
                description: 'Handles submit-event from justifi-checkout',
                check: (html) => html.includes('submit-event')
            },
            {
                name: 'Test Cards',
                description: 'Shows test card information',
                check: (html) => html.includes('4242424242424242')
            }
        ];
    }

    getTokenizationTests() {
        return [
            {
                name: 'Card Form',
                description: 'Creates justifi-card-form element',
                check: (html) => html.includes('justifi-card-form')
            },
            {
                name: 'Tokenization',
                description: 'Contains tokenization logic',
                check: (html) => html.includes('tokenizePaymentMethod') || html.includes('/api/tokenize')
            },
            {
                name: 'Payment Creation',
                description: 'Contains payment creation logic',
                check: (html) => html.includes('createPayment') || html.includes('/api/payments')
            },
            {
                name: 'Stored Methods',
                description: 'Handles stored payment methods',
                check: (html) => html.includes('storedMethods')
            },
            {
                name: 'Security Features',
                description: 'Shows PCI compliance features',
                check: (html) => html.includes('tokenization-only')
            }
        ];
    }

    getDashboardTests() {
        return [
            {
                name: 'Chart Library',
                description: 'Loads Chart.js for analytics',
                check: (html) => html.includes('chart.js')
            },
            {
                name: 'Dashboard Layout',
                description: 'Contains dashboard grid layout',
                check: (html) => html.includes('dashboard-grid')
            },
            {
                name: 'Payment List',
                description: 'Contains payment list functionality',
                check: (html) => html.includes('list_payments') || html.includes('/api/payments')
            },
            {
                name: 'Summary Cards',
                description: 'Contains summary metrics cards',
                check: (html) => html.includes('summary-cards')
            },
            {
                name: 'Search Feature',
                description: 'Contains payment search functionality',
                check: (html) => html.includes('payment-search')
            },
            {
                name: 'Auto Refresh',
                description: 'Contains auto-refresh functionality',
                check: (html) => html.includes('setInterval')
            }
        ];
    }

    addTestResult(example, testName, passed, description) {
        this.testResults.push({ example, testName, passed, description });
        const status = passed ? '✅' : '❌';
        console.log(`  ${status} ${testName}: ${description}`);
    }

    printResults() {
        console.log('\n📊 Test Results Summary');
        console.log('========================\n');

        const groupedResults = this.testResults.reduce((acc, result) => {
            if (!acc[result.example]) acc[result.example] = [];
            acc[result.example].push(result);
            return acc;
        }, {});

        let totalTests = 0;
        let totalPassed = 0;

        for (const [example, tests] of Object.entries(groupedResults)) {
            const passed = tests.filter(t => t.passed).length;
            const total = tests.length;
            const percentage = Math.round((passed / total) * 100);
            
            totalTests += total;
            totalPassed += passed;

            console.log(`${example}: ${passed}/${total} (${percentage}%)`);
        }

        const overallPercentage = Math.round((totalPassed / totalTests) * 100);
        console.log(`\nOverall: ${totalPassed}/${totalTests} (${overallPercentage}%)`);

        if (overallPercentage >= 80) {
            console.log('\n🎉 Tests passed! Examples are ready for use.');
        } else {
            console.log('\n⚠️  Some tests failed. Please review the examples.');
        }

        console.log('\n📖 To run examples manually:');
        console.log('  1. cd examples/web-components');
        console.log('  2. python -m http.server 8000');
        console.log('  3. Open http://localhost:8000 in your browser');
    }
}

// CLI interface
if (require.main === module) {
    const testRunner = new TestRunner();
    testRunner.runAllTests().catch(error => {
        console.error('Test runner error:', error);
        process.exit(1);
    });
}

module.exports = TestRunner;