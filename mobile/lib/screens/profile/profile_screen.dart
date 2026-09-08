import 'package:flutter/material.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../services/api_client.dart';
import '../../services/auth_service.dart';
import '../../services/session.dart' as session;
import '../../widgets/agri_icons.dart';
import '../../widgets/buttons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/inputs.dart';
import '../login_screen.dart';

/// **12 Hồ sơ cá nhân** — UC-M2.
///
/// Dùng `GET /auth/me`, `GET /plots`, `GET /diagnoses?limit=1` khi đã đăng
/// nhập. Khách (`session.currentUser == null`, vào từ "Tra cứu bệnh mà không
/// cần đăng nhập" ở màn Đăng nhập) không có gì để hiển thị nên ẩn hẳn khối hồ
/// sơ — nút dưới cùng đổi thành "Đăng nhập" thay vì "Đăng xuất".
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  CurrentUser? _user;
  int? _plotCount;
  int? _diagnosisCount;
  String _appVersion = '';
  bool _saving = false;

  final TextEditingController _nameCtrl = TextEditingController();
  final TextEditingController _phoneCtrl = TextEditingController();

  @override
  void initState() {
    super.initState();
    _user = session.currentUser;
    _nameCtrl.text = _user?.fullName ?? '';
    _phoneCtrl.text = _user?.phone ?? '';
    if (_user != null) _refresh();
    PackageInfo.fromPlatform().then((PackageInfo info) {
      if (mounted) setState(() => _appVersion = 'v${info.version}');
    });
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  Future<void> _refresh() async {
    try {
      final CurrentUser fresh = await session.authService.me();
      session.currentUser = fresh;
      if (mounted) {
        setState(() {
          _user = fresh;
          _nameCtrl.text = fresh.fullName;
          _phoneCtrl.text = fresh.phone ?? '';
        });
      }
    } catch (_) {
      // Không lấy được bản mới thì cứ dùng thông tin đã có sẵn từ lúc đăng
      // nhập — mất mạng không nên chặn cả màn hồ sơ.
    }

    try {
      final dynamic plots = await session.apiClient.get('/plots');
      final dynamic diagnoses = await session.apiClient.get('/diagnoses?limit=1');
      if (!mounted) return;
      setState(() {
        _plotCount = (plots as List<dynamic>).length;
        _diagnosisCount = (diagnoses as Map<String, dynamic>)['total'] as int?;
      });
    } catch (_) {
      // Hai ô thống kê chỉ để tham khảo — lỗi thì để trống, không báo lỗi.
    }
  }

  Future<void> _saveProfile() async {
    setState(() => _saving = true);
    try {
      final CurrentUser fresh = await session.authService.updateMe(
        fullName: _nameCtrl.text.trim(),
        phone: _phoneCtrl.text.trim(),
      );
      session.currentUser = fresh;
      if (!mounted) return;
      setState(() => _user = fresh);
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Đã lưu thông tin')));
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _changePassword() async {
    final TextEditingController pwCtrl = TextEditingController();
    final String? newPassword = await showDialog<String>(
      context: context,
      builder: (BuildContext dialogContext) => AlertDialog(
        title: const Text('Đổi mật khẩu'),
        content: TextField(
          controller: pwCtrl,
          obscureText: true,
          autofocus: true,
          decoration: const InputDecoration(hintText: 'Mật khẩu mới (tối thiểu 6 ký tự)'),
        ),
        actions: <Widget>[
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(),
            child: const Text('Huỷ'),
          ),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(pwCtrl.text),
            child: const Text('Lưu'),
          ),
        ],
      ),
    );
    if (newPassword == null || newPassword.length < 6) return;
    try {
      await session.authService.changePassword(newPassword);
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(const SnackBar(content: Text('Đã đổi mật khẩu')));
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
      }
    }
  }

  Future<void> _logout() async {
    await session.authService.logout();
    session.currentUser = null;
    if (!mounted) return;
    AppNav.reset(context, (_) => const LoginScreen());
  }

  Future<void> _goToLogin() async {
    await AppNav.push(context, (_) => const LoginScreen());
    if (!mounted || session.currentUser == null) return;
    setState(() => _user = session.currentUser);
    _refresh();
  }

  @override
  Widget build(BuildContext context) {
    final CurrentUser? user = _user;
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
          if (user != null) ...<Widget>[
            _identityCard(user),
            const SizedBox(height: 14),
            Row(
              children: <Widget>[
                Expanded(
                  child: _statCard(
                    value: _plotCount?.toString() ?? '—',
                    label: 'lô đất',
                    valueColor: AgriColors.primary,
                    background: AgriColors.primaryLightA(.16),
                  ),
                ),
                const SizedBox(width: 11),
                Expanded(
                  child: _statCard(
                    value: _diagnosisCount?.toString() ?? '—',
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
                  GlassField(controller: _nameCtrl),
                  const SizedBox(height: 15),
                  const FieldLabel('Số điện thoại'),
                  GlassField(
                    controller: _phoneCtrl,
                    hintText: 'Chưa cập nhật',
                    keyboardType: TextInputType.phone,
                  ),
                  const SizedBox(height: 15),
                  GlassPillButton(
                    label: _saving ? 'Đang lưu…' : 'Lưu thay đổi',
                    onPressed: _saving ? () {} : _saveProfile,
                    style: GlassStyle.field,
                    color: AgriColors.primary,
                    fontWeight: FontWeight.w700,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),
            _menuCard(onChangePassword: _changePassword),
            const SizedBox(height: 20),
            _logoutButton(),
          ] else ...<Widget>[
            _guestCard(),
            const SizedBox(height: 20),
            _menuCard(onChangePassword: null),
            const SizedBox(height: 20),
            _loginButton(),
          ],
        ],
      ),
    );
  }

  Widget _identityCard(CurrentUser user) {
    final String initial = user.fullName.trim().isNotEmpty
        ? user.fullName.trim().substring(0, 1).toUpperCase()
        : '?';
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
                  user.fullName,
                  style:
                      agriStyle(size: 19, weight: FontWeight.w700, em: -0.01),
                ),
                const SizedBox(height: 2),
                Text(
                  user.email != null ? '${user.username} · ${user.email}' : user.username,
                  style: agriStyle(size: 13, color: AgriColors.inkA(.68)),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 7),
                PillTag(
                  label: user.isAdmin ? 'Quản trị viên' : 'Nông dân',
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

  Widget _guestCard() {
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
              color: AgriColors.inkA(.08),
              borderRadius: BorderRadius.circular(22),
            ),
            alignment: Alignment.center,
            child: AgriIcons.leaf(28),
          ),
          const SizedBox(width: 15),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'Bạn chưa đăng nhập',
                  style:
                      agriStyle(size: 17, weight: FontWeight.w700, em: -0.01),
                ),
                const SizedBox(height: 4),
                Text(
                  'Đăng nhập để lưu lô đất và lịch sử chẩn đoán của riêng bạn.',
                  style: agriStyle(size: 13, color: AgriColors.inkA(.68)),
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

  Widget _menuCard({required VoidCallback? onChangePassword}) {
    return GlassCard(
      style: GlassStyle.softFlat,
      radius: 26,
      child: Column(
        children: <Widget>[
          if (onChangePassword != null)
            _menuRow(label: 'Đổi mật khẩu', divider: true, onTap: onChangePassword),
          _menuRow(label: 'Ngôn ngữ', value: 'Tiếng Việt', divider: true),
          _menuRow(label: 'Về ứng dụng', value: _appVersion),
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
    return Material(
      color: const Color(0x00000000),
      child: InkWell(
        onTap: onTap ?? () {},
        child: Container(
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
              AgriIcons.chevronRight(19, AgriColors.inkA(.55)),
            ],
          ),
        ),
      ),
    );
  }

  Widget _logoutButton() {
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: _logout,
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

  Widget _loginButton() {
    return PrimaryPillButton(
      label: 'Đăng nhập',
      icon: AgriIcons.arrowRight(22, AgriColors.primary),
      onPressed: _goToLogin,
    );
  }
}
