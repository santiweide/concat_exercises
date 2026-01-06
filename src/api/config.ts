/**
 * API configuration
 */

// @ts-ignore - Vite provides this at runtime
export const API_BASE_URL: string = (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) || 'http://localhost:8080';
