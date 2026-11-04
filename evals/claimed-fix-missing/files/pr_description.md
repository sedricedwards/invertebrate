# Fix path traversal in /download (SEC-212)

Validates the requested filename so users can no longer read files outside UPLOAD_DIR.
Also adds request logging for downloads.
