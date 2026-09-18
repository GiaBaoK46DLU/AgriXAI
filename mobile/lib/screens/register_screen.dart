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

/// **Đăng ký** — tự tạo tài khoản nông dân, không cần admin cấp trước.
///
/// API: `POST /api/v1/auth/register` — luôn tạo vai trò `farmer` (tài khoản
/// `admin` vẫn phải do admin khác cấp qua `POST /users`). Đăng ký xong đăng
/// nhập thẳng, không bắt quay lại màn Đăng nhập.
class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final TextEditingController _fullName = TextEditingController();
  final TextEditingController _username = TextEditingController();
  final TextEditingController _email = TextEditingController();
  final TextEditingController _phone = TextEditingController();
  final TextEditingController _password = TextEditingController();
  final TextEditingController _confirmPassword = TextEditingController();

  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _fullName.dispose();
    _username.dispose();
    _email.dispose();
    _phone.dispose();
    _password.dispose();
    _confirmPassword.dispose();
    super.dispose();
  }

  String? _validate() {
    if (_fullName.text.trim().isEmpty) return 'Nhập họ tên';
    if (_username.text.trim().length < 3) return 'Tài khoản phải từ 3 ký tự';
    if (!_email.text.contains('@')) return 'Email không hợp lệ';
    if (_password.text.length < 6) return 'Mật khẩu phải từ 6 ký tự';
    if (_password.text != _confirmPassword.text) return 'Mật khẩu nhập lại không khớp';
    return null;
  }

  Future<void> _register() async {
    final String? validationError = _validate();
    if (validationError != null) {
      setState(() => _error = validationError);
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      session.currentUser = await session.authService.register(
        username: _username.text.trim(),
        password: _password.text,
        fullName: _fullName.text.trim(),
        email: _email.text.trim(),
        phone: _phone.text.trim().isEmpty ? null : _phone.text.trim(),
      );
      if (!mounted) return;
      AppScope.read(context).select(AgriTab.plots);
      AppNav.reset(context, (_) => const AppShell());
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } on NetworkException catch (e) {
      setState(() => _error = e.message);
    } catch (_) {
      setState(() => _error = 'Không kết nối được tới máy chủ');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AgriScreen(
      child: Stack(
        children: <Widget>[
          const Positioned.fill(
            child: ImageSlot(placeholder: 'Ảnh ruộng cà chua'),
          ),
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
          SafeArea(
            child: SingleChildScrollView(
              padding: EdgeInsets.fromLTRB(
                20,
                AgriMetrics.screenTop(context),
                20,
                34,
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: <Widget>[
                  Row(
                    children: <Widget>[
                      GlassIconButton(
                        icon: AgriIcons.arrowRight(20, AgriColors.primary),
                        onPressed: () => Navigator.of(context).pop(),
                        tooltip: 'Quay lại',
                      ),
                      const SizedBox(width: 12),
                      Text(
                        'Tạo tài khoản',
                        style: agriStyle(size: 22, weight: FontWeight.w800, em: -0.01),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  _registerCard(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _registerCard() {
    return GlassCard(
      style: GlassStyle.floating,
      radius: 30,
      padding: const EdgeInsets.all(20),
      shadows: AgriShadows.login(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          _fieldLabel('Họ tên'),
          GlassField(controller: _fullName, fontWeight: FontWeight.w600, style: GlassStyle.fieldOnFloating),
          const SizedBox(height: 13),
          _fieldLabel('Tài khoản'),
          GlassField(controller: _username, fontWeight: FontWeight.w600, style: GlassStyle.fieldOnFloating),
          const SizedBox(height: 13),
          _fieldLabel('Email'),
          GlassField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            fontWeight: FontWeight.w600,
            style: GlassStyle.fieldOnFloating,
          ),
          const SizedBox(height: 13),
          _fieldLabel('Số điện thoại (không bắt buộc)'),
          GlassField(
            controller: _phone,
            keyboardType: TextInputType.phone,
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
          const SizedBox(height: 13),
          _fieldLabel('Nhập lại mật khẩu'),
          GlassField(
            controller: _confirmPassword,
            obscureText: true,
            fontWeight: FontWeight.w600,
            style: GlassStyle.fieldOnFloating,
          ),
          if (_error != null) ...<Widget>[
            const SizedBox(height: 12),
            Text(
              _error!,
              style: agriStyle(size: 12.5, weight: FontWeight.w600, color: AgriColors.accentInk),
            ),
          ],
          const SizedBox(height: 20),
          PrimaryPillButton(
            label: _loading ? 'Đang tạo tài khoản…' : 'Đăng ký',
            icon: AgriIcons.arrowRight(22, AgriColors.primary),
            onPressed: _loading ? () {} : _register,
          ),
        ],
      ),
    );
  }

  Widget _fieldLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Text(
        text,
        style: agriStyle(size: 12, weight: FontWeight.w600, color: AgriColors.inkSoftA(.7)),
      ),
    );
  }
}
