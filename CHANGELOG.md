# Changelog

All notable changes to the JustiFi MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- NPX wrapper for easy installation and usage
- Cross-platform support (Windows, macOS, Linux)
- Automatic Python dependency management
- Virtual environment creation by default
- Health check functionality
- Comprehensive examples for LangChain integration

### Changed
- Improved error handling and user feedback
- Enhanced documentation with NPX usage examples
- Updated configuration examples without personal paths

### Fixed
- Removed accidentally committed user-specific files
- Fixed asyncio warnings in test suite
- Resolved import order issues

## [1.0.0] - 2024-XX-XX

### Added
- Initial release of JustiFi MCP Server
- Support for JustiFi payment operations
- MCP protocol implementation with FastMCP
- Docker support for development
- Comprehensive test suite
- LangChain and OpenAI integration examples
- Documentation and configuration examples

### Features
- Payment management tools
- Payout operations
- Refund processing
- Dispute handling
- Balance transaction monitoring
- Checkout management
- Payment method retrieval

### Supported Transports
- STDIO (default for AI clients)
- HTTP for web integrations
- Server-Sent Events (SSE) for real-time applications