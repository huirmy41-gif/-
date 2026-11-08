# Architecture
Android Activity + bundled HTML/CSS/JS. Secure local origin via AndroidX WebViewAssetLoader. File/content access and untrusted navigation disabled. Native bridge limited to atomic app-private state, system-selected backup files, local TTS and explicit system recognition intent. No raw recording storage.
Pure engine.js shared by unit tests and WebView. LocalStorage mirrors native AtomicFile state. Parent PIN uses salted PBKDF2-SHA256 120000 iterations with cooldown; a child gate, not enterprise identity.
Optional Cloudflare D1 v2 additive tables preserve legacy data. Household authentication token, exact CORS, versioned compare-and-swap writes. AI default disabled and separately consented, no automatic uploads. No analytics, advertisements, social network or payments.
