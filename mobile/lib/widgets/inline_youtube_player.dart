import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:webview_flutter_android/webview_flutter_android.dart';

/// Định danh app gửi cho YouTube qua `Referer`/`origin`/`widget_referrer`.
///
/// Từ giữa 2025 YouTube bắt buộc trình phát nhúng phải cho biết nó đang được
/// nhúng ở đâu — thiếu (hoặc giả là chính `www.youtube.com`) thì trình phát
/// báo "Video unavailable — Error code: 152/153". Với app chạy WebView, tài
/// liệu YouTube IFrame API hướng dẫn dùng `https://<application id>`. Gói
/// `youtube_player_iframe` cũ cố định trang chứa ở origin `www.youtube.com`
/// và dùng luôn giá trị đó làm `host` của iframe, nên không đổi được — đó là
/// lý do tự viết widget này thay vì dùng gói.
///
/// Phải khớp `applicationId` trong `android/app/build.gradle.kts`.
const String kYoutubeEmbedReferrer = 'https://com.dlu.agrixai.agrixai_farmer';

/// Trình phát YouTube nhúng ngay trong app, chỉ là một `<iframe>` embed chuẩn
/// trong WebView — khung điều khiển play/pause/tua là của chính YouTube, không
/// vẽ thêm lớp nút Flutter đè lên (tránh lỗi "nhấn hai lần mới dừng" của
/// `youtube_player_flutter` trước đây).
///
/// Bấm vào logo/tiêu đề YouTube bên trong khung (điều hướng ra ngoài trang
/// embed) thì mở bằng app/trình duyệt ngoài, không để WebView tự chuyển trang.
class InlineYoutubePlayer extends StatefulWidget {
  const InlineYoutubePlayer({super.key, required this.videoId});

  final String videoId;

  @override
  State<InlineYoutubePlayer> createState() => _InlineYoutubePlayerState();
}

class _InlineYoutubePlayerState extends State<InlineYoutubePlayer> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFF000000))
      ..setNavigationDelegate(
        NavigationDelegate(onNavigationRequest: _onNavigationRequest),
      );

    final platform = _controller.platform;
    if (platform is AndroidWebViewController) {
      // Cho phép `autoplay=1` chạy ngay — người dùng đã bấm play trên ảnh
      // thumbnail rồi, không bắt bấm lần hai trong khung YouTube.
      platform.setMediaPlaybackRequiresUserGesture(false);
      // Cookie bên thứ ba mặc định TẮT cho từng WebView trên Android, trình
      // phát YouTube cần nó để khởi động ổn định.
      AndroidWebViewCookieManager(const PlatformWebViewCookieManagerCreationParams())
          .setAcceptThirdPartyCookies(platform, true);
      // Android WebView không tự xử lý toàn màn hình của <video>/<iframe>:
      // nút toàn màn hình của YouTube gọi tới đây, ta tự đẩy một route đen.
      platform.setCustomWidgetCallbacks(
        onShowCustomWidget: _showFullscreen,
        onHideCustomWidget: _hideFullscreen,
      );
    }

    _controller.loadHtmlString(_buildHtml(widget.videoId), baseUrl: kYoutubeEmbedReferrer);
  }

  static String _buildHtml(String videoId) {
    final String id = Uri.encodeComponent(videoId);
    final String ref = Uri.encodeComponent(kYoutubeEmbedReferrer);
    final String src = 'https://www.youtube.com/embed/$id'
        '?autoplay=1&playsinline=1&rel=0&modestbranding=1&fs=1'
        '&enablejsapi=1&origin=$ref&widget_referrer=$ref';
    return '''
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<style>
  html, body { margin: 0; padding: 0; background: #000; height: 100%; overflow: hidden; }
  iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
</style>
</head>
<body>
<iframe src="$src"
  referrerpolicy="strict-origin-when-cross-origin"
  allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
  allowfullscreen></iframe>
</body>
</html>
''';
  }

  NavigationDecision _onNavigationRequest(NavigationRequest request) {
    // Chỉ chặn điều hướng của khung chính — tài nguyên/iframe con của trình
    // phát phải được tải bình thường.
    if (!request.isMainFrame) return NavigationDecision.navigate;
    final Uri? uri = Uri.tryParse(request.url);
    if (uri == null) return NavigationDecision.prevent;
    if (request.url.startsWith(kYoutubeEmbedReferrer) || uri.scheme == 'about') {
      return NavigationDecision.navigate;
    }
    launchUrl(uri, mode: LaunchMode.externalApplication);
    return NavigationDecision.prevent;
  }

  bool _fullscreenShown = false;

  void _showFullscreen(Widget widget, void Function() onHidden) {
    if (_fullscreenShown || !mounted) return;
    _fullscreenShown = true;
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.immersiveSticky);
    SystemChrome.setPreferredOrientations(<DeviceOrientation>[
      DeviceOrientation.landscapeLeft,
      DeviceOrientation.landscapeRight,
    ]);
    Navigator.of(context, rootNavigator: true)
        .push(
          PageRouteBuilder<void>(
            opaque: true,
            pageBuilder: (_, __, ___) => PopScope(
              canPop: false,
              onPopInvokedWithResult: (bool didPop, Object? _) {
                // Nút Back: báo WebView thoát toàn màn hình, WebView sẽ gọi
                // lại onHideCustomWidget → _hideFullscreen đóng route này.
                if (!didPop) onHidden();
              },
              child: ColoredBox(color: const Color(0xFF000000), child: widget),
            ),
          ),
        )
        .whenComplete(_restoreSystemUi);
  }

  void _hideFullscreen() {
    if (!_fullscreenShown || !mounted) return;
    _fullscreenShown = false;
    Navigator.of(context, rootNavigator: true).pop();
  }

  void _restoreSystemUi() {
    _fullscreenShown = false;
    SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
    SystemChrome.setPreferredOrientations(DeviceOrientation.values);
  }

  @override
  Widget build(BuildContext context) {
    return AspectRatio(
      aspectRatio: 16 / 9,
      child: WebViewWidget(controller: _controller),
    );
  }
}
