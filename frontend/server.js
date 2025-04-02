const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;
const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';

// Serve static files from public directory
app.use(express.static(path.join(__dirname, 'public')));

// Serve assets directory
app.use('/assets', express.static(path.join(__dirname, 'assets')));

// Proxy API requests to the backend
app.use('/api', createProxyMiddleware({
    target: BACKEND_API_URL,
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
        res.status(500).json({
            error: 'Proxy Error',
            message: 'Failed to communicate with the backend service'
        });
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
    console.log(`Proxying API requests to ${BACKEND_API_URL}`);
}); 