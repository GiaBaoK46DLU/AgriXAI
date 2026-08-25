import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_glass.dart';
import '../core/app_typography.dart';

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
