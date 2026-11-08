package com.wordpet.app;

import android.app.Activity;
import android.os.Bundle;
import android.graphics.Color;
import android.view.Gravity;
import android.view.View;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.content.SharedPreferences;
import android.net.Uri;
import android.view.ViewGroup;

public class MainActivity extends Activity {
  private SharedPreferences prefs;
  private LinearLayout root;
  private int purple = Color.rgb(55,48,96);
  @Override public void onCreate(Bundle b) {
    super.onCreate(b);
    prefs=getSharedPreferences("wordpet", MODE_PRIVATE);
    String url=prefs.getString("server_url","");
    if(url.isEmpty()) showSetup(); else openApp(url);
  }
  private TextView label(String s,int size) {
    TextView t=new TextView(this); t.setText(s); t.setTextSize(size); t.setTextColor(purple);
    t.setGravity(Gravity.CENTER); t.setPadding(18,18,18,18); return t;
  }
  private void base() {
    root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
    root.setPadding(28,36,28,28); root.setGravity(Gravity.CENTER);
    root.setBackgroundColor(Color.rgb(250,247,255)); setContentView(root);
  }
  private void showSetup() {
    base(); root.addView(label("✨ 作文小作家 Word Pet",26));
    root.addView(label("连接家庭学习空间",18));
    EditText input=new EditText(this); input.setSingleLine(true);
    input.setHint("https://你的家庭服务器域名");
    input.setText(prefs.getString("server_url",""));
    root.addView(input,new LinearLayout.LayoutParams(-1,-2));
    Button go=new Button(this); go.setText("连接并开始学习");
    root.addView(go); go.setOnClickListener(v->{
      String u=input.getText().toString().trim();
      Uri uri=Uri.parse(u);
      if(!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost()==null || uri.getUserInfo()!=null || uri.getQuery()!=null || uri.getFragment()!=null) {
        input.setError("请输入有效的 HTTPS 根网址"); return;
      }
      prefs.edit().putString("server_url",u.replaceAll("/+$","")).apply(); openApp(prefs.getString("server_url",""));
    });
    root.addView(label("需要家长先完成服务器部署和账号配对。",14));
  }
  private void openApp(String url) {
    WebView w=new WebView(this); w.getSettings().setJavaScriptEnabled(true); w.getSettings().setDomStorageEnabled(true);
    w.setWebViewClient(new WebViewClient(){});
    setContentView(w); w.loadUrl(url);
  }
  @Override public void onBackPressed() { showSetup(); }
}
