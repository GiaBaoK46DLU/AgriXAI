import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../widgets/agri_icons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/inputs.dart';
import '../login_screen.dart';

/// **12 Hồ sơ cá nhân** — UC-M2.
///
/// API khi nối thật: `GET /auth/me`, `PATCH /auth/me`.
class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final TextEditingController _name =
      TextEditingController(text: 'Triệu Quang Học');
  final TextEditingController _phone =
      TextEditingController(text: '0912 345 678');

  @override
  void dispose() {
    _name.dispose();
    _phone.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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
          _identityCard(),
          const SizedBox(height: 14),
          Row(
            children: <Widget>[
              Expanded(
                child: _statCard(
                  value: '3',
                  label: 'lô đất',
                  valueColor: AgriColors.primary,
                  background: AgriColors.primaryLightA(.16),
                ),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: _statCard(
                  value: '28',
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

  Widget _identityCard() {
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
              'H',
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
                  'Triệu Quang Học',
                  style:
                      agriStyle(size: 19, weight: FontWeight.w700, em: -0.01),
                ),
                const SizedBox(height: 2),
                Text(
                  'quanghoc · Cam Ly, Đà Lạt',
                  style: agriStyle(size: 13, color: AgriColors.inkA(.68)),
                ),
                const SizedBox(height: 7),
                PillTag(
                  label: 'Nông dân',
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
          _menuRow(label: 'Đổi mật khẩu', divider: true),
          _menuRow(label: 'Ngôn ngữ', value: 'Tiếng Việt', divider: true),
          _menuRow(label: 'Về ứng dụng', value: 'v0.1.0'),
        ],
      ),
    );
  }

  Widget _menuRow({
    required String label,
    String? value,
    bool divider = false,
  }) {
    return Material(
      color: const Color(0x00000000),
      child: InkWell(
        onTap: () {},
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
        onTap: () => AppNav.reset(context, (_) => const LoginScreen()),
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
