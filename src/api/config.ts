/**
 * API configuration
 * 
 * In production, the frontend and backend are served from the same domain and port.
 * In development, you can set VITE_API_URL in .env to override.
 */

// Use relative path to current domain, or fall back to /api for production
// In production: frontend and backend share the same origin
// In development: can be overridden via VITE_API_URL env var
export const API_BASE_URL: string = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || '';
