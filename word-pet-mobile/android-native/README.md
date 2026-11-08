# Word Pet Android APK
Standalone Android WebView shell for the Word Pet family learning service.
- Package: com.wordpet.app
- Min Android: 6.0 (API 23)
- Target SDK: 35
- First launch asks for a parent-managed HTTPS server root URL.
- No credentials or API keys are embedded in the APK.
- Build with GitHub Actions workflow: .github/workflows/android-apk.yml
This APK shell requires an already deployed Word Pet HTTPS backend to provide the full synced learning experience. It does not bundle the backend.
