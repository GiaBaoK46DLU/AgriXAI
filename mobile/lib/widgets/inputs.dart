import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_glass.dart';
import '../core/app_typography.dart';
import 'agri_icons.dart';

/// Ô nhập liệu dạng viên thuốc — `min-height:50px;padding:0 18px;font-size:16px`.
class GlassField extends StatelessWidget {
  const GlassField({
    super.key,
    this.controller,
    this.hintText,
    this.obscureText = false,
    this.keyboardType,
    this.fontWeight = FontWeight.w400,
    this.fontSize = 16,
    this.style = GlassStyle.field,
    this.prefix,
    this.onChanged,
  });

  final TextEditingController? controller;
  final String? hintText;
  final bool obscureText;
  final TextInputType? keyboardType;
  final FontWeight fontWeight;
  final double fontSize;
  final GlassStyle style;

  /// Icon nằm bên trái, ví dụ kính lúp ở màn 10.
  final Widget? prefix;
  final ValueChanged<String>? onChanged;

  @override
  Widget build(BuildContext context) {
    final Widget field = Container(
      constraints: const BoxConstraints(minHeight: 50),
      decoration: BoxDecoration(
        gradient: style.gradient,
        borderRadius: BorderRadius.circular(999),
        border: style.border,
      ),
      child: Row(
        children: <Widget>[
          if (prefix != null) ...<Widget>[
            const SizedBox(width: 17),
            prefix!,
          ],
          Expanded(
            child: TextField(
              controller: controller,
              obscureText: obscureText,
              keyboardType: keyboardType,
              onChanged: onChanged,
              cursorColor: AgriColors.primary,
              style: agriStyle(
                size: fontSize,
                weight: fontWeight,
                color: AgriColors.ink,
              ),
              decoration: InputDecoration(
                isDense: true,
                border: InputBorder.none,
                enabledBorder: InputBorder.none,
                focusedBorder: InputBorder.none,
                contentPadding: EdgeInsets.only(
                  left: prefix == null ? 18 : 10,
                  right: 18,
                  top: 14,
                  bottom: 14,
                ),
                hintText: hintText,
                hintStyle: agriStyle(
                  size: fontSize,
                  weight: fontWeight,
                  color: AgriColors.inkA(.55),
                ),
              ),
            ),
          ),
        ],
      ),
    );

    if (style.blurSigma <= 0) return field;
    return ClipRRect(
      borderRadius: BorderRadius.circular(999),
      child: BackdropFilter(
        filter: glassFilter(style.blurSigma),
        child: field,
      ),
    );
  }
}

/// Ô ghi chú nhiều dòng — `min-height:96px;border-radius:24px;font-size:15px`.
class GlassTextArea extends StatelessWidget {
  const GlassTextArea({
    super.key,
    this.controller,
    this.hintText,
    this.minLines = 3,
  });

  final TextEditingController? controller;
  final String? hintText;
  final int minLines;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 96),
      decoration: BoxDecoration(
        gradient: GlassStyle.field.gradient,
        borderRadius: BorderRadius.circular(24),
        border: GlassStyle.field.border,
      ),
      child: TextField(
        controller: controller,
        minLines: minLines,
        maxLines: null,
        keyboardType: TextInputType.multiline,
        cursorColor: AgriColors.primary,
        style: agriStyle(size: 15, color: AgriColors.ink, height: 1.5),
        decoration: InputDecoration(
          isDense: true,
          border: InputBorder.none,
          enabledBorder: InputBorder.none,
          focusedBorder: InputBorder.none,
          contentPadding: const EdgeInsets.symmetric(
            horizontal: 18,
            vertical: 14,
          ),
          hintText: hintText,
          hintStyle: agriStyle(
            size: 15,
            color: AgriColors.inkA(.55),
            height: 1.5,
          ),
        ),
      ),
    );
  }
}

/// Ô chọn dạng viên thuốc — cùng hình dạng `GlassField` nhưng mở bảng chọn
/// (`showModalBottomSheet`) thay vì gõ chữ. Dùng cho lọc diễn đàn và chọn
/// bệnh/lịch sử chẩn đoán ở màn tạo bài viết.
///
/// `T` bất kỳ; so khớp giá trị đang chọn bằng `==` nên dùng kiểu có `==` có ý
/// nghĩa (`String`, `int`, hoặc bản ghi (record) như trong `forum_screen.dart`).
class GlassDropdownField<T> extends StatelessWidget {
  const GlassDropdownField({
    required this.label,
    required this.value,
    required this.options,
    required this.optionLabel,
    required this.onChanged,
    super.key,
    this.sheetTitle,
  });

  final String label;
  final T value;
  final List<T> options;
  final String Function(T) optionLabel;
  final ValueChanged<T> onChanged;
  final String? sheetTitle;

  Future<void> _open(BuildContext context) async {
    final T? picked = await showModalBottomSheet<T>(
      context: context,
      backgroundColor: const Color(0x00000000),
      isScrollControlled: true,
      builder: (BuildContext sheetContext) => _OptionSheet<T>(
        title: sheetTitle ?? label,
        options: options,
        optionLabel: optionLabel,
        selected: value,
      ),
    );
    if (picked != null) onChanged(picked);
  }

  @override
  Widget build(BuildContext context) {
    return Material(
      color: const Color(0x00000000),
      borderRadius: BorderRadius.circular(999),
      child: InkWell(
        onTap: () => _open(context),
        borderRadius: BorderRadius.circular(999),
        child: Container(
          constraints: const BoxConstraints(minHeight: 50),
          padding: const EdgeInsets.symmetric(horizontal: 18),
          decoration: BoxDecoration(
            gradient: GlassStyle.field.gradient,
            borderRadius: BorderRadius.circular(999),
            border: GlassStyle.field.border,
          ),
          child: Row(
            children: <Widget>[
              Expanded(
                child: Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: agriStyle(size: 15, color: AgriColors.ink),
                ),
              ),
              const SizedBox(width: 8),
              Transform.rotate(
                angle: 1.5708, // 90° — dùng chung mũi tên phải làm mũi tên xuống
                child: AgriIcons.chevronRight(16, AgriColors.inkA(.62)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _OptionSheet<T> extends StatelessWidget {
  const _OptionSheet({
    required this.title,
    required this.options,
    required this.optionLabel,
    required this.selected,
  });

  final String title;
  final List<T> options;
  final String Function(T) optionLabel;
  final T selected;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Container(
        margin: const EdgeInsets.all(12),
        constraints: BoxConstraints(maxHeight: MediaQuery.of(context).size.height * .7),
        decoration: BoxDecoration(
          color: AgriColors.cream,
          borderRadius: BorderRadius.circular(28),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 8),
              child: Text(
                title,
                style: agriStyle(size: 16, weight: FontWeight.w700),
              ),
            ),
            Flexible(
              child: ListView.builder(
                shrinkWrap: true,
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                itemCount: options.length,
                itemBuilder: (BuildContext context, int i) {
                  final T option = options[i];
                  final bool active = option == selected;
                  return Material(
                    color: const Color(0x00000000),
                    borderRadius: BorderRadius.circular(18),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(18),
                      onTap: () => Navigator.of(context).pop(option),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                        child: Row(
                          children: <Widget>[
                            Expanded(
                              child: Text(
                                optionLabel(option),
                                style: agriStyle(
                                  size: 15,
                                  weight: active ? FontWeight.w700 : FontWeight.w500,
                                  color: active ? AgriColors.primary : AgriColors.ink,
                                ),
                              ),
                            ),
                            if (active)
                              AgriIcons.checkCircle(18),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
            ),
            const SizedBox(height: 10),
          ],
        ),
      ),
    );
  }
}

/// Nhãn nhỏ đặt trên ô nhập liệu.
class FieldLabel extends StatelessWidget {
  const FieldLabel(this.text, {super.key, this.bottomGap = 6});

  final String text;
  final double bottomGap;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(bottom: bottomGap),
      child: Text(text, style: AgriTextStyles.fieldLabel),
    );
  }
}
