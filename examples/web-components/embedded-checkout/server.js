#!/usr/bin/env node

/**
 * Real-world Express.js server for JustiFi integration
 * 
 * This server makes actual HTTP calls to the JustiFi API for checkout
 * creation and payment processing. The MCP server was used during 
 * development in the IDE to help understand the API and generate this code.
 */

const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3001;

// JustiFi API configuration
const JUSTIFI_CLIENT_ID = process.env.JUSTIFI_CLIENT_ID;
const JUSTIFI_CLIENT_SECRET = process.env.JUSTIFI_CLIENT_SECRET;
const JUSTIFI_BASE_URL = process.env.JUSTIFI_BASE_URL || 'https://api.justifi.ai';

if (!JUSTIFI_CLIENT_ID || !JUSTIFI_CLIENT_SECRET) {
    console.error('❌ Missing JustiFi credentials. Please set:');
    console.error('   JUSTIFI_CLIENT_ID=your_client_id');
    console.error('   JUSTIFI_CLIENT_SECRET=your_client_secret');
    process.exit(1);
}

// OAuth token cache
let accessToken = null;
let tokenExpiry = null;

/**
 * Get OAuth access token from JustiFi
 * This code was generated with assistance from the MCP server in the IDE
 */
async function getAccessToken() {
    if (accessToken && tokenExpiry && new Date() < tokenExpiry) {
        return accessToken;
    }

    try {
        const response = await fetch(`${JUSTIFI_BASE_URL}/oauth/token`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                grant_type: 'client_credentials',
                client_id: JUSTIFI_CLIENT_ID,
                client_secret: JUSTIFI_CLIENT_SECRET
            })
        });

        if (!response.ok) {
            throw new Error(`OAuth failed: ${response.status} ${response.statusText}`);
        }

        const tokenData = await response.json();
        accessToken = tokenData.access_token;
        
        // Set expiry to 5 minutes before actual expiry for safety
        const expiresIn = (tokenData.expires_in - 300) * 1000;
        tokenExpiry = new Date(Date.now() + expiresIn);
        
        console.log('🔑 OAuth token refreshed successfully');
        return accessToken;

    } catch (error) {
        console.error('❌ OAuth token request failed:', error);
        throw error;
    }
}

/**
 * Make authenticated request to JustiFi API
 * This pattern was learned using the MCP server during development
 */
async function makeJustiFiRequest(endpoint, options = {}) {
    const token = await getAccessToken();
    
    const response = await fetch(`${JUSTIFI_BASE_URL}${endpoint}`, {
        ...options,
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        }
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`JustiFi API error: ${response.status} ${errorText}`);
    }

    return response.json();
}

// Middleware
app.use(express.json());
app.use(express.static(__dirname));

// Serve the HTML file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

/**
 * Create checkout endpoint - makes real JustiFi API call
 * This creates checkout sessions that work with the justifi-checkout web component
 * The MCP server helped us understand the API structure during development
 */
app.post('/api/checkout', async (req, res) => {
    try {
        const { amount, description } = req.body;
        
        // Validate input
        if (!amount || amount < 100) {
            return res.status(400).json({
                success: false,
                error: 'Amount must be at least $1.00 (100 cents)'
            });
        }

        if (!description || description.trim() === '') {
            return res.status(400).json({
                success: false,
                error: 'Description is required'
            });
        }
        
        console.log('Creating checkout via JustiFi API:', { amount, description });
        
        // Make real API call to JustiFi
        const checkout = await makeJustiFiRequest('/v1/checkouts', {
            method: 'POST',
            body: JSON.stringify({
                amount: parseInt(amount),
                description: description.trim(),
                currency: 'usd'
            })
        });
        
        console.log('✅ Checkout created:', checkout.data.id);
        res.json({
            success: true,
            data: checkout.data
        });
        
    } catch (error) {
        console.error('❌ Checkout creation error:', error);
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Retrieve payment endpoint - makes real JustiFi API call
 * MCP server provided the API endpoint structure during development
 */
app.get('/api/payment/:id', async (req, res) => {
    try {
        const { id } = req.params;
        
        if (!id || id.trim() === '') {
            return res.status(400).json({
                success: false,
                error: 'Payment ID is required'
            });
        }
        
        console.log('Retrieving payment via JustiFi API:', id);
        
        // Make real API call to JustiFi
        const payment = await makeJustiFiRequest(`/v1/payments/${id}`);
        
        console.log('✅ Payment retrieved:', payment.data.status);
        res.json({
            success: true,
            data: payment.data
        });
        
    } catch (error) {
        console.error('❌ Payment retrieval error:', error);
        
        // Handle specific error cases
        if (error.message.includes('404')) {
            return res.status(404).json({
                success: false,
                error: 'Payment not found'
            });
        }
        
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

/**
 * Health check endpoint
 */
app.get('/api/health', (req, res) => {
    res.json({
        status: 'ok',
        mcp_server: 'connected', // In real app, check MCP connection
        timestamp: new Date().toISOString()
    });
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Server error:', error);
    res.status(500).json({
        success: false,
        error: 'Internal server error'
    });
});

// Start server
app.listen(PORT, () => {
    console.log('🚀 JustiFi Embedded Checkout Server started');
    console.log(`📡 Server running at http://localhost:${PORT}`);
    console.log('💳 Visit http://localhost:${PORT} to see the checkout example');
    console.log('');
    console.log('🔧 To use with real MCP server:');
    console.log('   1. Start MCP server: make dev');
    console.log('   2. Update API endpoints to call MCP tools');
    console.log('   3. Add proper authentication and error handling');
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🛑 Server shutting down gracefully');
    process.exit(0);
});

module.exports = app;