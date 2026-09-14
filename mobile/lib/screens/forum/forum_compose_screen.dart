import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_typography.dart';
import '../../models/models.dart';
import '../../services/api_client.dart';
import '../../services/session.dart' as session;
import '../../widgets/agri_screen.dart';
import '../../widgets/buttons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/inputs.dart';
import '../../widgets/misc.dart';

/// **Tạo bài viết diễn đàn** — gắn với một bệnh, có thể đính kèm một lần
/// chẩn đoán của chính người viết.
///
/// Mở từ ba chỗ: nút "+" ở màn Diễn đàn (không có gì điền sẵn), nút "Thêm
/// thảo luận" ở màn Kết quả và nút "Phản hồi về gợi ý xử lý này" ở màn Gợi ý
/// xử lý — cả hai điền sẵn [initialDiagnosisId]/[initialDiseaseKey].
///
/// API: `POST /forum/posts`. Trả `true` qua `Navigator.pop` khi đăng thành
/// công để màn gọi biết mà tải lại danh sách.
class ForumComposeScreen extends StatefulWidget {
  const ForumComposeScreen({
    super.key,
    this.initialDiagnosisId,
    this.initialDiseaseKey,
    this.initialKind,
  });

  final int? initialDiagnosisId;
  final String? initialDiseaseKey;
  final ForumPostKind? initialKind;

  @override
  State<ForumComposeScreen> createState() => _ForumComposeScreenState();
}

class _ForumComposeScreenState extends State<ForumComposeScreen> {
  final TextEditingController _content = TextEditingController();

  bool _loadingOptions = true;
  bool _saving = false;
  String? _error;

  List<Disease> _diseases = <Disease>[];
  List<DiagnosisEntry> _diagnoses = <DiagnosisEntry>[];

  String? _diseaseKey;
  int? _diagnosisId;
  late ForumPostKind _kind = widget.initialKind ?? ForumPostKind.tip;

  @override
  void initState() {
    super.initState();
    _diseaseKey = widget.initialDiseaseKey;
    _diagnosisId = widget.initialDiagnosisId;
    _loadOptions();
  }

  @override
  void dispose() {
    _content.dispose();
    super.dispose();
  }

  Future<void> _loadOptions() async {
    try {
      final List<Disease> diseases = await session.diseaseService.fetchAll();
      final ({List<DiagnosisEntry> items, int total}) diagnoses =
          await session.diagnosisService.list(pageSize: 100);
      if (!mounted) return;
      setState(() {
        _diseases = diseases;
        _diagnoses = diagnoses.items;
        _diseaseKey ??= diseases.isEmpty ? null : diseases.first.key;
        _loadingOptions = false;
      });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Không tải được danh mục bệnh/lịch sử — kiểm tra kết nối mạng.';
          _loadingOptions = false;
        });
      }
    }
  }

  DiagnosisEntry? _findDiagnosis(int? id) {
    if (id == null) return null;
    for (final DiagnosisEntry entry in _diagnoses) {
      if (entry.id == id) return entry;
    }
    return null;
  }

  Disease? _findDisease(String? key) {
    if (key == null) return null;
    for (final Disease disease in _diseases) {
      if (disease.key == key) return disease;
    }
    return null;
  }

  DiagnosisEntry? get _selectedDiagnosis => _findDiagnosis(_diagnosisId);

  void _selectDiagnosis(int? id) {
    setState(() {
      _diagnosisId = id;
      // Đính kèm chẩn đoán nào thì tự khoá ô chọn bệnh theo đúng bệnh của
      // lần chẩn đoán đó — bỏ đính kèm (chọn "Không đính kèm") mới mở khoá lại.
      final DiagnosisEntry? entry = _findDiagnosis(id);
      if (entry != null) _diseaseKey = entry.diseaseKey;
    });
  }

  Future<void> _submit() async {
    final String content = _content.text.trim();
    if (_diseaseKey == null) {
      setState(() => _error = 'Chọn bệnh liên quan');
      return;
    }
    if (content.isEmpty) {
      setState(() => _error = 'Nhập nội dung bài viết');
      return;
    }

    setState(() {
      _saving = true;
      _error = null;
    });

    try {
      await session.forumService.createPost(
        diseaseKey: _diseaseKey,
        diagnosisId: _diagnosisId,
        kind: _kind,
        content: content,
      );
      if (!mounted) return;
      Navigator.of(context).pop(true);
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _saving = false; });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Không đăng được bài viết — kiểm tra kết nối mạng rồi thử lại.';
          _saving = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AgriScreen(
      child: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(16, AgriMetrics.screenTop(context), 16, 22),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: <Widget>[
            ScreenHeader(
              title: 'Tạo bài viết',
              onBack: () => Navigator.of(context).pop(),
            ),
            const SizedBox(height: 18),
            if (_loadingOptions)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 60),
                child: Center(child: CircularProgressIndicator()),
              )
            else
              _form(),
            if (_error != null) ...<Widget>[
              const SizedBox(height: 14),
              Text(
                _error!,
                style: agriStyle(size: 12.5, weight: FontWeight.w600, color: AgriColors.accentInk),
              ),
            ],
            const SizedBox(height: 20),
            PrimarySolidButton(
              label: _saving ? 'Đang đăng…' : 'Đăng bài',
              onPressed: _saving || _loadingOptions ? () {} : _submit,
            ),
            const SizedBox(height: 10),
            GlassPillButton(
              label: 'Huỷ',
              onPressed: () => Navigator.of(context).pop(),
              minHeight: 48,
              fontSize: 15,
              style: GlassStyle.field,
            ),
          ],
        ),
      ),
    );
  }

  Widget _form() {
    final DiagnosisEntry? selected = _selectedDiagnosis;
    final bool diseaseLocked = _diagnosisId != null;

    return GlassCard(
      style: GlassStyle.card,
      radius: 28,
      padding: const EdgeInsets.all(18),
      shadows: AgriShadows.raised(),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const FieldLabel('Bệnh liên quan'),
          IgnorePointer(
            ignoring: diseaseLocked,
            child: Opacity(
              opacity: diseaseLocked ? .55 : 1,
              child: GlassDropdownField<String?>(
                label: _diseaseKey == null
                    ? 'Chọn bệnh'
                    : _findDisease(_diseaseKey)?.name ?? _diseaseKey!,
                value: _diseaseKey,
                sheetTitle: 'Chọn bệnh liên quan',
                options: _diseases.map((Disease d) => d.key as String?).toList(),
                optionLabel: (String? key) =>
                    _diseases.firstWhere((Disease d) => d.key == key).name,
                onChanged: (String? key) => setState(() => _diseaseKey = key),
              ),
            ),
          ),
          if (diseaseLocked)
            Padding(
              padding: const EdgeInsets.only(top: 6, left: 6),
              child: Text(
                'Đã khoá theo lần chẩn đoán đính kèm bên dưới.',
                style: agriStyle(size: 11.5, color: AgriColors.inkA(.58)),
              ),
            ),
          const SizedBox(height: 15),
          const FieldLabel('Đính kèm lịch sử chẩn đoán của bạn (tuỳ chọn)'),
          GlassDropdownField<int?>(
            label: selected == null
                ? 'Không đính kèm'
                : '${selected.disease} · ${selected.time}',
            value: _diagnosisId,
            sheetTitle: 'Chọn lần chẩn đoán',
            options: <int?>[null, ..._diagnoses.map((DiagnosisEntry d) => d.id)],
            optionLabel: (int? id) {
              if (id == null) return 'Không đính kèm';
              final DiagnosisEntry entry =
                  _diagnoses.firstWhere((DiagnosisEntry d) => d.id == id);
              return '${entry.disease} · ${entry.time}';
            },
            onChanged: _selectDiagnosis,
          ),
          const SizedBox(height: 15),
          const FieldLabel('Loại phản hồi', bottomGap: 8),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: <Widget>[
              for (final ForumPostKind kind in ForumPostKind.values)
                SelectableChip(
                  label: forumPostKindLabel(kind),
                  selected: _kind == kind,
                  onPressed: () => setState(() => _kind = kind),
                  fontSize: 12.5,
                  minHeight: 40,
                  horizontalPadding: 14,
                ),
            ],
          ),
          const SizedBox(height: 15),
          const FieldLabel('Nội dung'),
          GlassTextArea(
            controller: _content,
            hintText: 'Chia sẻ ý kiến, kinh nghiệm hoặc phản hồi của bạn…',
            minLines: 4,
          ),
        ],
      ),
    );
  }
}
