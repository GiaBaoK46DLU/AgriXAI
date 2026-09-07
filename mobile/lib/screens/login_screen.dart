import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_glass.dart';
import '../core/app_metrics.dart';
import '../core/app_scope.dart';
import '../core/app_typography.dart';
import '../services/api_client.dart';
import '../services/session.dart' as session;
import '../widgets/agri_icons.dart';
import '../widgets/agri_screen.dart';
import '../widgets/buttons.dart';
import '../widgets/glass_card.dart';
import '../widgets/image_slot.dart';
import '../widgets/inputs.dart';
import 'app_shell.dart';

/// **01 Đăng nhập** — UC-M1. Tài khoản do admin cấp, không có màn tự đăng ký.
///
/// API: `POST /api/v1/auth/login`, token lưu qua `AuthService`.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final TextEditingController _account = TextEditingController();
  final TextEditingController _password = TextEditingController();

  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _account.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    final String username = _account.text.trim();
    final String password = _password.text;
    if (username.isEmpty || password.isEmpty) {
      setState(() => _error = 'Nhập đủ tài khoản và mật khẩu');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      session.currentUser = await session.authService.login(username, password);
      if (!mounted) return;
      AppScope.read(context).select(AgriTab.plots);
      AppNav.reset(context, (_) => const AppShell());
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = 'Không kết nối được tới máy chủ');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _browseCatalog() {
    AppScope.read(context).select(AgriTab.catalog);
    AppNav.reset(context, (_) => const AppShell());
  }

  @override
  Widget build(BuildContext context) {
    return AgriScreen(
      child: Stack(
        children: <Widget>[
          const Positioned.fill(
            child: ImageSlot(placeholder: 'Ảnh ruộng cà chua'),
          ),
          // linear-gradient(180deg, .92 0%, .86 30%, .5 56%, .94 100%)
          Positioned.fill(
            child: IgnorePointer(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: <Color>[
                      AgriColors.heroVeil(.92),
                      AgriColors.heroVeil(.86),
                      AgriColors.heroVeil(.5),
                      AgriColors.heroVeil(.94),
                    ],
                    stops: const <double>[0, .30, .56, 1],
                  ),
                ),
              ),
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              Expanded(
                child: SingleChildScrollView(
                  child: Padding(
                    padding: EdgeInsets.fromLTRB(
                      26,
                      AgriMetrics.loginTop(context),
                      26,
                      0,
                    ),
                    child: _intro(),
                  ),
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(20, 0, 20, 34),
                child: _loginCard(),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _intro() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Row(
          children: <Widget>[
            GlassCard(
              style: GlassStyle.overImage,
              blurSigma: 22,
              radius: 14,
              width: 42,
              height: 42,
              child: Center(child: AgriIcons.leaf(24)),
            ),
            const SizedBox(width: 11),
            Text(
              'AgriXAI',
              style: agriStyle(size: 21, weight: FontWeight.w800, em: -0.01),
            ),
          ],
        ),
        const SizedBox(height: 24),
        Text(
          'Chẩn đoán bệnh\ncây trồng bằng ảnh',
          style: agriStyle(
            size: 34,
            weight: FontWeight.w800,
            height: 1.16,
            em: -0.02,
          ),
        ),
        const SizedBox(height: 10),
        ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 300),
          child: Text(
            'Nâng cao giá trị và phát triển bền vững từ sản xuất đến tiêu thụ.',
            style: agriStyle(size: 15, height: 1.55, color: AgriColors.ink),
          ),
        ),
      ],
    );
  }

  Widget _loginCard() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        GlassCard(
          style: GlassStyle.floating,
          radius: 30,
          padding: const EdgeInsets.all(20),
          shadows: AgriShadows.login(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              _fieldLabel('Tài khoản'),
              GlassField(
                controller: _account,
                fontWeight: FontWeight.w600,
                style: GlassStyle.fieldOnFloating,
              ),
              const SizedBox(height: 13),
              _fieldLabel('Mật khẩu'),
              GlassField(
                controller: _password,
                obscureText: true,
                fontWeight: FontWeight.w600,
                style: GlassStyle.fieldOnFloating,
              ),
              if (_error != null) ...<Widget>[
                const SizedBox(height: 12),
                Text(
                  _error!,
                  style: agriStyle(
                    size: 12.5,
                    weight: FontWeight.w600,
                    color: AgriColors.accentInk,
                  ),
                ),
              ],
              const SizedBox(height: 20),
              PrimaryPillButton(
                label: _loading ? 'Đang đăng nhập…' : 'Đăng nhập',
                icon: AgriIcons.arrowRight(22, AgriColors.primary),
                onPressed: _loading ? () {} : _login,
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        GhostButton(
          label: 'Tra cứu bệnh mà không cần đăng nhập',
          onPressed: _browseCatalog,
          color: AgriColors.inkA(.88),
          fontSize: 14.5,
          minHeight: 46,
          padding: EdgeInsets.zero,
        ),
      ],
    );
  }

  Widget _fieldLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: agriStyle(
          size: 12,
          weight: FontWeight.w600,
          color: AgriColors.inkSoftA(.7),
        ),
      ),
    );
  }
}
