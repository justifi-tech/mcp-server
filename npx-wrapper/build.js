#!/usr/bin/env node
/**
 * Build script for JustiFi MCP Server NPX package
 * 
 * This script prepares a self-contained NPX package by copying
 * all necessary server files into the npx-wrapper directory.
 */

const fs = require('fs');
const path = require('path');

const SOURCE_ROOT = path.resolve(__dirname, '..');
const TARGET_ROOT = __dirname;

/**
 * Copy a file or directory recursively
 */
function copyRecursive(src, dest) {
    const stat = fs.statSync(src);

    if (stat.isDirectory()) {
        // Create directory if it doesn't exist
        if (!fs.existsSync(dest)) {
            fs.mkdirSync(dest, { recursive: true });
        }

        // Copy all contents
        const items = fs.readdirSync(src);
        for (const item of items) {
            if (item.startsWith('.') || item === '__pycache__') continue; // Skip hidden files and cache
            copyRecursive(path.join(src, item), path.join(dest, item));
        }
    } else {
        // Copy file
        const destDir = path.dirname(dest);
        if (!fs.existsSync(destDir)) {
            fs.mkdirSync(destDir, { recursive: true });
        }
        fs.copyFileSync(src, dest);
    }
}

/**
 * Clean previous build artifacts
 */
function clean() {
    console.log('🧹 Cleaning previous build artifacts...');

    const itemsToClean = [
        'main.py',
        'pyproject.toml',
        'python',
        'modelcontextprotocol',
        'wrapper.js',
        'install.js'
    ];

    for (const item of itemsToClean) {
        const itemPath = path.join(TARGET_ROOT, item);
        if (fs.existsSync(itemPath)) {
            if (fs.statSync(itemPath).isDirectory()) {
                fs.rmSync(itemPath, { recursive: true, force: true });
            } else {
                fs.unlinkSync(itemPath);
            }
        }
    }

    // Clean tgz files
    const files = fs.readdirSync(TARGET_ROOT);
    for (const file of files) {
        if (file.endsWith('.tgz')) {
            fs.unlinkSync(path.join(TARGET_ROOT, file));
        }
    }
}

/**
 * Copy essential server files
 */
function copyServerFiles() {
    console.log('📁 Copying server files...');

    const filesToCopy = [
        { src: 'main.py', dest: 'main.py' },
        { src: 'pyproject.toml', dest: 'pyproject.toml' },
        { src: 'python', dest: 'python' },
        { src: 'modelcontextprotocol', dest: 'modelcontextprotocol' }
    ];

    for (const { src, dest } of filesToCopy) {
        const srcPath = path.join(SOURCE_ROOT, src);
        const destPath = path.join(TARGET_ROOT, dest);

        if (fs.existsSync(srcPath)) {
            console.log(`  ✓ ${src} -> ${dest}`);
            copyRecursive(srcPath, destPath);
        } else {
            console.warn(`  ⚠️  ${src} not found, skipping`);
        }
    }
}

/**
 * Verify package.json is correctly configured
 */
function verifyPackageJson() {
    console.log('📝 Verifying package.json...');

    const packageJsonPath = path.join(TARGET_ROOT, 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));

    // Verify essential fields
    const requiredFields = {
        'main': 'index.js',
        'bin.justifi-mcp-server': 'index.js'
    };

    let hasErrors = false;

    for (const [field, expectedValue] of Object.entries(requiredFields)) {
        const fieldPath = field.split('.');
        let value = packageJson;
        for (const key of fieldPath) {
            value = value?.[key];
        }

        if (value !== expectedValue) {
            console.error(`  ❌ ${field} should be "${expectedValue}", got "${value}"`);
            hasErrors = true;
        } else {
            console.log(`  ✓ ${field}: ${value}`);
        }
    }

    // Verify all required files are listed
    const requiredFiles = [
        'index.js',
        'main.py',
        'pyproject.toml',
        'python/',
        'modelcontextprotocol/',
        'requirements.txt',
        'README.md'
    ];

    const missingFiles = requiredFiles.filter(file => !packageJson.files?.includes(file));
    if (missingFiles.length > 0) {
        console.error(`  ❌ Missing files in package.json: ${missingFiles.join(', ')}`);
        hasErrors = true;
    } else {
        console.log(`  ✓ All required files listed in package.json`);
    }

    if (hasErrors) {
        throw new Error('package.json configuration errors found');
    }
}

/**
 * Main build function
 */
function build() {
    console.log('🚀 Building JustiFi MCP Server NPX package...\n');

    try {
        clean();
        copyServerFiles();
        verifyPackageJson();

        console.log('\n✅ Build completed successfully!');
        console.log('\nPackage contents:');
        console.log('  📄 index.js         - Simple Node.js wrapper');
        console.log('  🐍 main.py          - Python MCP server entry point');
        console.log('  📦 python/          - Core MCP tools and utilities');
        console.log('  🔧 modelcontextprotocol/ - MCP protocol implementation');
        console.log('  📋 requirements.txt - Python dependencies');
        console.log('  📚 README.md        - Usage instructions');

        console.log('\nNext steps:');
        console.log('  npm pack           # Create the .tgz package');
        console.log('  npm publish        # Publish to NPM');
        console.log('  npx @justifi/mcp-server --version  # Test locally');

    } catch (error) {
        console.error('\n❌ Build failed:', error.message);
        process.exit(1);
    }
}

// Run build if script is executed directly
if (require.main === module) {
    build();
}

module.exports = { build, clean, copyServerFiles, verifyPackageJson }; 