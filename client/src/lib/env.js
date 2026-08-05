// Single place for environment-specific values. The dev proxy in
// vite.config.js means API_BASE_URL stays empty during dev (we call
// relative paths like "/api/accounts/login/"), but if this app is ever
// pointed at a different host in production, this is the one line to change.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

// Backend-documented limits, kept here so UI copy and validation can
// reference them instead of hardcoding numbers in components.
export const MAX_DOCUMENT_UPLOAD_MB = 20
export const ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.md', '.txt']
export const MAX_FLASHCARDS_PER_SET = 30