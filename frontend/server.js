const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// In production (Render), backend may be accessible through API calls directly
// In development, use localhost with the specified port
const isProduction = process.env.NODE_ENV === 'production';
const BACKEND_API_URL = isProduction 
    ? process.env.BACKEND_API_URL || '/api' // Use relative path in production
    : process.env.BACKEND_API_URL || 'http://localhost:8000';

console.log(`Using BACKEND_API_URL: ${BACKEND_API_URL}`);
console.log(`Environment: ${isProduction ? 'Production' : 'Development'}`);

// Serve static files from public directory
app.use(express.static(path.join(__dirname, 'public')));

// Serve assets directory
app.use('/assets', express.static(path.join(__dirname, 'assets')));

// Proxy API requests to the backend
app.use('/api', createProxyMiddleware({
    target: isProduction ? 'http://127.0.0.1:8000' : BACKEND_API_URL,
    changeOrigin: true,
    pathRewrite: function(path) {
        // If BACKEND_API_URL already includes /api, don't duplicate it
        if (BACKEND_API_URL.endsWith('/api')) {
            return path.replace(/^\/api/, '');
        }
        // Otherwise keep as is
        return path;
    },
    onError: (err, req, res) => {
        console.error('Proxy error:', err);
        res.writeHead(500, {
            'Content-Type': 'application/json'
        });
        res.end(JSON.stringify({
            error: 'Proxy Error',
            message: 'Failed to communicate with the backend service',
            details: err.message
        }));
    },
    logLevel: 'debug'
}));

// Serve the HTML for all other routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
    console.log(`Frontend server running on http://localhost:${PORT}`);
    console.log(`Proxying API requests to ${isProduction ? 'http://127.0.0.1:8000' : BACKEND_API_URL}`);
}); 