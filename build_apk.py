import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

def sanitize_package(url):
    domain = re.sub(r'^https?://', '', url).split('/')[0]
    domain = re.sub(r'[^a-zA-Z0-9]', '', domain) or "myapp"
    return f"com.webview.{domain.lower()}"

def create_webview_project(url, app_name, out_dir):
    pkg = sanitize_package(url)
    pkg_path = pkg.replace('.', '/')
    p = Path(out_dir)
    if p.exists(): shutil.rmtree(p)

    (p / "app/src/main/java" / pkg_path).mkdir(parents=True)
    (p / "app/src/main/res/values").mkdir(parents=True)

    # MainActivity.java
    (p / "app/src/main/java" / pkg_path / "MainActivity.java").write_text(f'''package {pkg};
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import androidx.appcompat.app.AppCompatActivity;
public class MainActivity extends AppCompatActivity {{
    private WebView webView;
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        webView = new WebView(this);
        WebSettings s = webView.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl(getString(R.string.app_url));
        setContentView(webView);
    }}
    @Override
    public void onBackPressed() {{
        if (webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }}
}}
''')

    # strings.xml
    (p / "app/src/main/res/values/strings.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{app_name}</string>
    <string name="app_url">{url}</string>
</resources>''')

    # AndroidManifest.xml
    (p / "app/src/main/AndroidManifest.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{pkg}">
    <uses-permission android:name="android.permission.INTERNET"/>
    <application android:allowBackup="true" android:icon="@android:drawable/sym_def_app_icon"
        android:label="@string/app_name" android:usesCleartextTraffic="true"
        android:theme="@style/Theme.AppCompat.Light.NoActionBar">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>''')

    # build.gradle
    (p / "app/build.gradle").write_text(f'''plugins {{ id 'com.android.application' }}
android {{
    namespace '{pkg}'
    compileSdk 34
    defaultConfig {{ applicationId '{pkg}'; minSdk 21; targetSdk 34; versionCode 1; versionName "1.0" }}
    compileOptions {{ sourceCompatibility JavaVersion.VERSION_17; targetCompatibility JavaVersion.VERSION_17 }}
}}
dependencies {{ implementation 'androidx.appcompat:appcompat:1.6.1' }}''')

    (p / "build.gradle").write_text("plugins { id 'com.android.application' version '8.2.0' apply false }\n")
    (p / "settings.gradle").write_text('''pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }
dependencyResolutionManagement { repositories { google(); mavenCentral() } }
rootProject.name = "WebViewApp"
include ':app'
''')
    (p / "gradle.properties").write_text("org.gradle.jvmargs=-Xmx2048m\nandroid.useAndroidX=true\n")
    return p

if __name__ == "__main__":
    url = os.environ.get("INPUT_URL", "https://example.com")
    app_name = os.environ.get("INPUT_APP_NAME", "MyApp")
    
    print(f"Building APK for: {url} | Name: {app_name}")
    
    project_dir = "/tmp/webview_project"
    create_webview_project(url, app_name, project_dir)
    
    print("Downloading Gradle & Building APK (Wait 2-3 mins)...")
    result = subprocess.run(["gradle", "assembleDebug", "--no-daemon"], cwd=project_dir)
    
    if result.returncode != 0:
        print("Build Failed!")
        sys.exit(1)
        
    apk_src = Path(project_dir) / "app/build/outputs/apk/debug/app-debug.apk"
    
    # APK ko root folder me copy karein taaki GitHub isko utha sake
    out_dir = Path("output_apk")
    out_dir.mkdir(exist_ok=True)
    shutil.copy(apk_src, out_dir / f"{app_name.replace(' ', '_')}.apk")
    print("Build Successful!")
