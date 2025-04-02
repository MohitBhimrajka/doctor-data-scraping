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
    pathRewrite: {
        '^/api': '/api'  // Keep /api prefix when forwarding to backend
    }
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