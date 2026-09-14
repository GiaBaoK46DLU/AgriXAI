import 'package:flutter/material.dart';

import '../../core/app_colors.dart';
import '../../core/app_glass.dart';
import '../../core/app_metrics.dart';
import '../../core/app_scope.dart';
import '../../core/app_typography.dart';
import '../../models/models.dart';
import '../../services/api_client.dart';
import '../../services/session.dart' as session;
import '../../widgets/agri_icons.dart';
import '../../widgets/agri_screen.dart';
import '../../widgets/buttons.dart';
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/inputs.dart';
import '../../widgets/misc.dart';
import '../result/result_screen.dart';

/// Chi tiết một bài viết diễn đàn + danh sách bình luận.
///
/// API: `GET /forum/posts/{id}` (kèm `comments`), `POST /forum/posts/{id}/comments`,
/// `POST /forum/posts/{id}/like`. Mở kết quả chẩn đoán liên kết qua
/// `GET /diagnoses/{id}` rồi đẩy `ResultScreen`.
class ForumDetailScreen extends StatefulWidget {
  const ForumDetailScreen({required this.postId, super.key});

  final int postId;

  @override
  State<ForumDetailScreen> createState() => _ForumDetailScreenState();
}

class _ForumDetailScreenState extends State<ForumDetailScreen> {
  final TextEditingController _comment = TextEditingController();

  bool _loading = true;
  bool _sending = false;
  bool _openingDiagnosis = false;
  bool _liking = false;
  String? _error;
  ForumPost? _post;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _comment.dispose();
    super.dispose();
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final ForumPost post = await session.forumService.getPost(widget.postId);
      if (!mounted) return;
      setState(() {
        _post = post;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Không tải được bài viết — kiểm tra kết nối mạng rồi thử lại.';
          _loading = false;
        });
      }
    }
  }

  Future<void> _sendComment() async {
    final String content = _comment.text.trim();
    if (content.isEmpty || _sending) return;
    setState(() => _sending = true);
    try {
      await session.forumService.addComment(widget.postId, content);
      _comment.clear();
      await _load(silent: true);
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.message)));
      }
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Không gửi được bình luận')),
        );
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  Future<void> _like() async {
    if (_liking || _post == null) return;
    setState(() => _liking = true);
    try {
      await session.forumService.likePost(widget.postId);
      await _load(silent: true);
    } catch (_) {
      // Bấm thích thất bại thì im lặng — không phải thao tác quan trọng.
    } finally {
      if (mounted) setState(() => _liking = false);
    }
  }

  Future<void> _openDiagnosis() async {
    final int? diagnosisId = _post?.diagnosisId;
    if (diagnosisId == null || _openingDiagnosis) return;
    setState(() => _openingDiagnosis = true);
    try {
      final DiagnosisCase detail = await session.diagnosisService.get(diagnosisId);
      if (!mounted) return;
      await AppNav.push(context, (_) => ResultScreen(diagnosisCase: detail));
    } catch (_) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Không mở được kết quả chẩn đoán liên kết')),
        );
      }
    } finally {
      if (mounted) setState(() => _openingDiagnosis = false);
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
              title: 'Bài viết diễn đàn',
              onBack: () => Navigator.of(context).pop(),
            ),
            const SizedBox(height: 16),
            if (_loading)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 60),
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_error != null)
              _errorState(_error!)
            else
              ..._content(_post!),
          ],
        ),
      ),
    );
  }

  List<Widget> _content(ForumPost post) {
    return <Widget>[
      Row(
        children: <Widget>[
          Expanded(
            child: Text(
              post.diseaseName,
              style: agriStyle(size: 21, weight: FontWeight.w800, em: -0.02, height: 1.15),
            ),
          ),
          const SizedBox(width: 8),
          PillTag(
            label: forumPostKindLabel(post.kind),
            background: AgriColors.oliveA(.14),
            foreground: AgriColors.oliveInk,
            fontSize: 11,
            fontWeight: FontWeight.w700,
          ),
        ],
      ),
      const SizedBox(height: 6),
      Text(
        '${post.userFullName} · ${post.createdAt}',
        style: agriStyle(size: 12.5, color: AgriColors.inkA(.62)),
      ),
      const SizedBox(height: 16),
      GlassCard(
        style: GlassStyle.card,
        radius: 26,
        padding: const EdgeInsets.all(16),
        shadows: AgriShadows.raised(.1),
        child: Text(post.content, style: agriStyle(size: 15, height: 1.55)),
      ),
      if (post.diagnosisId != null) ...<Widget>[
        const SizedBox(height: 12),
        GlassCard(
          style: GlassStyle.soft,
          radius: 22,
          onTap: _openingDiagnosis ? null : _openDiagnosis,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          child: Row(
            children: <Widget>[
              AgriIcons.tabHistory(18, AgriColors.primary),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  post.diagnosisSummary ?? 'Xem kết quả chẩn đoán liên kết',
                  style: agriStyle(size: 13.5, weight: FontWeight.w600, color: AgriColors.primary),
                ),
              ),
              AgriIcons.chevronRight(18, AgriColors.primary),
            ],
          ),
        ),
      ],
      const SizedBox(height: 14),
      Row(
        children: <Widget>[
          GlassIconButton(
            size: 40,
            radius: 999,
            onPressed: _liking ? () {} : _like,
            icon: AgriIcons.heart(17, filled: false, color: AgriColors.accentInk),
          ),
          const SizedBox(width: 8),
          Text(
            '${post.likesCount} lượt thích',
            style: agriStyle(size: 13, weight: FontWeight.w600, color: AgriColors.inkA(.72)),
          ),
        ],
      ),
      const SizedBox(height: 22),
      Text('Bình luận (${post.comments.length})', style: AgriTextStyles.sectionTitle),
      const SizedBox(height: 12),
      GlassField(
        controller: _comment,
        hintText: 'Viết bình luận…',
      ),
      const SizedBox(height: 8),
      Align(
        alignment: Alignment.centerRight,
        child: GlassPillButton(
          label: _sending ? 'Đang gửi…' : 'Gửi bình luận',
          icon: AgriIcons.send(16, AgriColors.primary),
          onPressed: _sending ? () {} : _sendComment,
          minHeight: 42,
          fontSize: 13.5,
        ),
      ),
      const SizedBox(height: 16),
      if (post.comments.isEmpty)
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 20),
          child: Center(
            child: Text(
              'Chưa có bình luận nào — hãy là người đầu tiên.',
              style: agriStyle(size: 13.5, color: AgriColors.inkA(.62)),
            ),
          ),
        )
      else
        for (int i = 0; i < post.comments.length; i++) ...<Widget>[
          _CommentRow(comment: post.comments[i]),
          if (i != post.comments.length - 1) const SizedBox(height: 10),
        ],
    ];
  }

  Widget _errorState(String message) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 46),
      child: Column(
        children: <Widget>[
          Text(
            message,
            textAlign: TextAlign.center,
            style: agriStyle(size: 14, color: AgriColors.inkA(.72)),
          ),
          const SizedBox(height: 14),
          GlassPillButton(label: 'Thử lại', onPressed: _load, minHeight: 44, fontSize: 14),
        ],
      ),
    );
  }
}

class _CommentRow extends StatelessWidget {
  const _CommentRow({required this.comment});

  final ForumComment comment;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      style: GlassStyle.faint,
      radius: 20,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            '${comment.userFullName} · ${comment.createdAt}',
            style: agriStyle(size: 12, weight: FontWeight.w600, color: AgriColors.inkA(.68)),
          ),
          const SizedBox(height: 4),
          Text(comment.content, style: agriStyle(size: 13.5, height: 1.5)),
        ],
      ),
    );
  }
}
