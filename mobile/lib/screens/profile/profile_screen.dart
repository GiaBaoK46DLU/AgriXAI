import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../widgets/agri_icons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/inputs.dart';
import '../../services/api_client.dart';
import '../../services/auth_service.dart' show CurrentUser;
import '../../services/session.dart' as session;
import '../login_screen.dart';

/// **12 Hồ sơ cá nhân** — UC-M2.
///
/// `GET /auth/me` đã chạy sẵn ở khởi động app (`AuthService.tryRestore`) nên
/// màn này đọc thẳng `session.currentUser`; chỉ gọi mạng thêm cho hai ô
/// thống kê (`GET /plots`, `GET /diagnoses`) và khi lưu sửa đổi.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  late final TextEditingController _name =
      TextEditingController(text: session.currentUser?.fullName ?? '');
  late final TextEditingController _phone =
      TextEditingController(text: session.currentUser?.phone ?? '');

  bool _saving = false;
  String? _saveError;

  int? _plotCount;
  int? _diagnosisCount;
  String _appVersion = '';

  @override
  void initState() {
    super.initState();
    _loadStats();
    _loadVersion();
  }

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    super.dispose();
  }

  Future<void> _loadStats() async {
    try {
      final List<dynamic> plots =
          await session.apiClient.get('/plots') as List<dynamic>;
      final ({List<dynamic> items, int total}) diagnoses =
          await session.diagnosisService.list(pageSize: 1);
      if (!mounted) return;
      setState(() {
        _plotCount = plots.length;
        _diagnosisCount = diagnoses.total;
      });
    } catch (_) {
      // Hai ô thống kê là phụ — hỏng thì cứ để "--", không chặn cả màn hình.
    }
  }

  Future<void> _loadVersion() async {
    final PackageInfo info = await PackageInfo.fromPlatform();
    if (mounted) setState(() => _appVersion = info.version);
  }

  Future<void> _save() async {
    final String name = _name.text.trim();
    if (name.isEmpty) {
      setState(() => _saveError = 'Họ và tên không được để trống');
      return;
    }
    setState(() {
      _saving = true;
      _saveError = null;
    });
    try {
      final CurrentUser updated = await session.authService.updateMe(
        fullName: name,
        phone: _phone.text.trim(),
      );
      session.currentUser = updated;
      if (!mounted) return;
      setState(() => _saving = false);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã lưu thông tin cá nhân')),
      );
    } on ApiException catch (e) {
      if (mounted) setState(() { _saveError = e.message; _saving = false; });
    } catch (_) {
      if (mounted) {
        setState(() {
          _saveError = 'Không lưu được — kiểm tra kết nối mạng rồi thử lại.';
          _saving = false;
        });
      }
    }
  }

  Future<void> _openChangePassword() async {
    await showDialog<void>(
      context: context,
      builder: (_) => const _ChangePasswordDialog(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final CurrentUser? user = session.currentUser;

    return SingleChildScrollView(
      padding: EdgeInsets.fromLTRB(
        16,
        AgriMetrics.screenTop(context),
        16,
        22,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            'Hồ sơ',
            style: agriStyle(size: 23, weight: FontWeight.w700, em: -0.02),
          ),
          const SizedBox(height: 18),
          _identityCard(user),
          const SizedBox(height: 14),
          Row(
            children: <Widget>[
              Expanded(
                child: _statCard(
                  value: _plotCount?.toString() ?? '--',
                  label: 'lô đất',
                  valueColor: AgriColors.primary,
                  background: AgriColors.primaryLightA(.16),
                ),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: _statCard(
                  value: _diagnosisCount?.toString() ?? '--',
                  label: 'lượt chẩn đoán',
                  valueColor: AgriColors.accentInk,
                  background: AgriColors.accentA(.16),
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          GlassCard(
            style: GlassStyle.card,
            radius: 28,
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                const FieldLabel('Họ và tên'),
                GlassField(controller: _name),
                const SizedBox(height: 15),
                const FieldLabel('Số điện thoại'),
                GlassField(
                  controller: _phone,
                  keyboardType: TextInputType.phone,
                ),
                if (_saveError != null) ...<Widget>[
                  const SizedBox(height: 12),
                  Text(
                    _saveError!,
                    style: agriStyle(
                      size: 12.5,
                      weight: FontWeight.w600,
                      color: AgriColors.accentInk,
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                _SaveButton(saving: _saving, onPressed: _save),
              ],
            ),
          ),
          const SizedBox(height: 20),
          _menuCard(),
          const SizedBox(height: 20),
          _logoutButton(),
        ],
      ),
    );
  }

  Widget _identityCard(CurrentUser? user) {
    final String fullName = user?.fullName ?? 'Chưa có tên';
    final String initial = fullName.isEmpty ? '?' : fullName.substring(0, 1).toUpperCase();

    return GlassCard(
      style: GlassStyle.card,
      radius: 28,
      padding: const EdgeInsets.all(18),
      shadows: AgriShadows.raised(),
      child: Row(
        children: <Widget>[
          Container(
            width: 62,
            height: 62,
            decoration: BoxDecoration(
              gradient: agriPrimaryGradient,
              borderRadius: BorderRadius.circular(22),
            ),
            alignment: Alignment.center,
            child: Text(
              initial,
              style: agriStyle(
                size: 24,
                weight: FontWeight.w700,
                color: const Color(0xFFFFFFFF),
              ),
            ),
          ),
          const SizedBox(width: 15),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  fullName,
                  style:
                      agriStyle(size: 19, weight: FontWeight.w700, em: -0.01),
                ),
                const SizedBox(height: 2),
                Text(
                  '@${user?.username ?? ''}',
                  style: agriStyle(size: 13, color: AgriColors.inkA(.68)),
                ),
                const SizedBox(height: 7),
                PillTag(
                  label: user?.isAdmin == true ? 'Quản trị' : 'Nông dân',
                  background: AgriColors.primaryLightA(.2),
                  foreground: AgriColors.primary,
                  fontSize: 11,
                  fontWeight: FontWeight.w700,
                  padding: const EdgeInsets.symmetric(
                    horizontal: 11,
                    vertical: 4,
                  ),
                  border: Border.all(color: AgriColors.mintA(.28)),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _statCard({
    required String value,
    required String label,
    required Color valueColor,
    required Color background,
  }) {
    return Container(
      padding: const EdgeInsets.all(17),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: AgriColors.paleLime),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            value,
            style: agriStyle(
              size: 27,
              weight: FontWeight.w800,
              color: valueColor,
              height: 1,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: agriStyle(
              size: 12.5,
              weight: FontWeight.w600,
              color: AgriColors.inkSoftA(.7),
            ),
          ),
        ],
      ),
    );
  }

  Widget _menuCard() {
    return GlassCard(
      style: GlassStyle.softFlat,
      radius: 26,
      child: Column(
        children: <Widget>[
          _menuRow(
            label: 'Đổi mật khẩu',
            divider: true,
            onTap: _openChangePassword,
          ),
          _menuRow(label: 'Ngôn ngữ', value: 'Tiếng Việt', divider: true),
          _menuRow(
            label: 'Về ứng dụng',
            value: _appVersion.isEmpty ? '…' : 'v$_appVersion',
          ),
        ],
      ),
    );
  }

  Widget _menuRow({
    required String label,
    String? value,
    bool divider = false,
    VoidCallback? onTap,
  }) {
    final Widget content = Container(
      constraints: const BoxConstraints(minHeight: 54),
      padding: const EdgeInsets.symmetric(horizontal: 17),
      decoration: divider
          ? BoxDecoration(
              border: Border(
                bottom: BorderSide(color: AgriColors.whiteA(.72)),
              ),
            )
          : null,
      child: Row(
        children: <Widget>[
          Expanded(
            child: Text(
              label,
              style: agriStyle(size: 15, weight: FontWeight.w600),
            ),
          ),
          if (value != null) ...<Widget>[
            Text(
              value,
              style: agriStyle(
                size: 14,
                weight: FontWeight.w500,
                color: AgriColors.inkA(.68),
              ),
            ),
            const SizedBox(width: 10),
          ],
          if (onTap != null) AgriIcons.chevronRight(19, AgriColors.inkA(.55)),
        ],
      ),
    );

    if (onTap == null) {
      return Material(color: const Color(0x00000000), child: content);
    }
    return Material(
      color: const Color(0x00000000),
      child: InkWell(onTap: onTap, child: content),
    );
  }

  Future<void> _logout(BuildContext context) async {
    await session.authService.logout();
    session.currentUser = null;
    if (!context.mounted) return;
    AppNav.reset(context, (_) => const LoginScreen());
  }

  Widget _logoutButton() {
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: () => _logout(context),
        borderRadius: BorderRadius.circular(999),
        child: Ink(
          decoration: BoxDecoration(
            color: AgriColors.accentA(.14),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: AgriColors.accentA(.3)),
          ),
          child: Container(
            constraints: const BoxConstraints(minHeight: 52),
            alignment: Alignment.center,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                AgriIcons.logout(20, AgriColors.accentInk),
                const SizedBox(width: 10),
                Text(
                  'Đăng xuất',
                  style: agriStyle(
                    size: 15.5,
                    weight: FontWeight.w600,
                    color: AgriColors.accentInk,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _SaveButton extends StatelessWidget {
  const _SaveButton({required this.saving, required this.onPressed});

  final bool saving;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: saving ? null : onPressed,
        borderRadius: BorderRadius.circular(999),
        child: Ink(
          decoration: BoxDecoration(
            gradient: agriPrimaryGradient,
            borderRadius: BorderRadius.circular(999),
          ),
          child: Container(
            constraints: const BoxConstraints(minHeight: 50),
            alignment: Alignment.center,
            child: Text(
              saving ? 'Đang lưu…' : 'Lưu thay đổi',
              style: agriStyle(
                size: 15,
                weight: FontWeight.w700,
                color: const Color(0xFFFFFFFF),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Hộp thoại đổi mật khẩu — bắt buộc đúng mật khẩu hiện tại
/// (`POST /auth/change-password`), xem lý do bảo mật ở `schemas/auth.py`.
class _ChangePasswordDialog extends StatefulWidget {
  const _ChangePasswordDialog();

  @override
  State<_ChangePasswordDialog> createState() => _ChangePasswordDialogState();
}

class _ChangePasswordDialogState extends State<_ChangePasswordDialog> {
  final TextEditingController _current = TextEditingController();
  final TextEditingController _next = TextEditingController();
  final TextEditingController _confirm = TextEditingController();

  bool _loading = false;
  String? _error;

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_next.text.length < 6) {
      setState(() => _error = 'Mật khẩu mới phải có ít nhất 6 ký tự');
      return;
    }
    if (_next.text != _confirm.text) {
      setState(() => _error = 'Mật khẩu xác nhận không khớp');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      await session.authService.changePassword(
        currentPassword: _current.text,
        newPassword: _next.text,
      );
      if (!mounted) return;
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Đã đổi mật khẩu')),
      );
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Không đổi được mật khẩu — kiểm tra kết nối mạng rồi thử lại.';
          _loading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Đổi mật khẩu'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            TextField(
              controller: _current,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Mật khẩu hiện tại'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _next,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Mật khẩu mới'),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: _confirm,
              obscureText: true,
              decoration: const InputDecoration(labelText: 'Xác nhận mật khẩu mới'),
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
          ],
        ),
      ),
      actions: <Widget>[
        TextButton(
          onPressed: _loading ? null : () => Navigator.of(context).pop(),
          child: const Text('Huỷ'),
        ),
        TextButton(
          onPressed: _loading ? null : _submit,
          child: Text(_loading ? 'Đang lưu…' : 'Đổi mật khẩu'),
        ),
      ],
    );
  }
}
