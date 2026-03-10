package com.hjpetrovic.n2srs

import android.os.Bundle
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView

    private val appUrl = "https://hjpetrovic.github.io/n2-srs/n2_srs.html"

    private val chromeUA =
        "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36 N2SRS-Android/1.0"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        webView = WebView(this).apply {
            settings.apply {
                javaScriptEnabled = true
                domStorageEnabled = true
                databaseEnabled = true
                cacheMode = WebSettings.LOAD_DEFAULT
                userAgentString = chromeUA
                loadWithOverviewMode = true
                useWideViewPort = true
                setSupportZoom(false)
                javaScriptCanOpenWindowsAutomatically = true
                setSupportMultipleWindows(true)
            }

            webChromeClient = WebChromeClient()

            webViewClient = object : WebViewClient() {
                override fun onReceivedError(
                    view: WebView,
                    request: WebResourceRequest,
                    error: WebResourceError
                ) {
                    if (request.isForMainFrame) {
                        view.loadDataWithBaseURL(null, offlinePage(), "text/html", "UTF-8", null)
                    }
                }
            }
        }

        setContentView(webView)
        webView.loadUrl(appUrl)
    }

    @Suppress("DEPRECATION")
    override fun onBackPressed() {
        if (webView.canGoBack()) webView.goBack()
        else super.onBackPressed()
    }

    private fun offlinePage(): String = """
        <!DOCTYPE html>
        <html>
        <head>
          <meta name="viewport" content="width=device-width, initial-scale=1">
          <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body {
              background: #100d36; color: #9388c0; font-family: sans-serif;
              display: flex; flex-direction: column; align-items: center;
              justify-content: center; min-height: 100vh; padding: 32px; text-align: center;
            }
            h1 {
              font-size: 1.8rem; margin-bottom: 16px;
              background: linear-gradient(135deg, #bae6fd, #d8b4fe);
              -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            }
            p  { line-height: 1.7; margin-bottom: 8px; }
            .hint { font-size: 0.82rem; color: #3e3870; margin-top: 24px; }
          </style>
        </head>
        <body>
          <h1>N2 SRS</h1>
          <p>No internet connection.</p>
          <p>Connect to Wi-Fi or mobile data to load the app.</p>
          <p class="hint">
            Once loaded online for the first time,<br>
            the app will work offline automatically.
          </p>
        </body>
        </html>
    """.trimIndent()
}
