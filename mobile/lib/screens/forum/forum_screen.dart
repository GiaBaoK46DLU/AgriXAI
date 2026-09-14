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
import '../../widgets/chips.dart';
import '../../widgets/glass_card.dart';
import '../../widgets/inputs.dart';
import 'forum_compose_screen.dart';
import 'forum_detail_screen.dart';

/// **Diễn đàn nông dân** — trao đổi kinh nghiệm quanh một lần chẩn đoán cụ
/// thể. Nút thêm bài là nút tròn ghim ở góc dưới phải, chỉ hiện ở màn này.
///
/// API: `GET /forum/posts` — cần đăng nhập, giống mọi tab khác của app.
class ForumScreen extends StatefulWidget {
  const ForumScreen({super.key});

  @override
  State<ForumScreen> createState() => _ForumScreenState();
}

class _ForumScreenState extends State<ForumScreen> {
  /// `null` nghĩa là "Tất cả loại bệnh".
  String? _diseaseKey;

  /// `null` nghĩa là "Tất cả loại phản hồi".
  ForumPostKind? _kind;

  bool _loading = true;
  String? _error;
  List<ForumPost> _posts = <ForumPost>[];
  List<Disease> _diseases = <Disease>[];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final List<Disease> diseases = _diseases.isEmpty
          ? await session.diseaseService.fetchAll()
          : _diseases;
      final ({List<ForumPost> items, int total}) page = await session.forumService.listPosts(
        diseaseKey: _diseaseKey,
        kind: _kind,
        pageSize: 50,
      );
      if (!mounted) return;
      setState(() {
        _diseases = diseases;
        _posts = page.items;
        _loading = false;
      });
    } on ApiException catch (e) {
      if (mounted) setState(() { _error = e.message; _loading = false; });
    } catch (_) {
      if (mounted) {
        setState(() {
          _error = 'Không tải được diễn đàn — kiểm tra kết nối mạng rồi thử lại.';
          _loading = false;
        });
      }
    }
  }

  Future<void> _openCompose() async {
    final bool? posted = await AppNav.push<bool>(
      context,
      (_) => const ForumComposeScreen(),
    );
    if (posted == true) _load();
  }

  Future<void> _openDetail(ForumPost post) async {
    await AppNav.push(context, (_) => ForumDetailScreen(postId: post.id));
    _load();
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: <Widget>[
        RefreshIndicator(
          onRefresh: _load,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: EdgeInsets.fromLTRB(
              16,
              AgriMetrics.screenTop(context),
              16,
              90,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                Text(
                  'Diễn đàn nông dân',
                  style: agriStyle(size: 23, weight: FontWeight.w700, em: -0.02),
                ),
                const SizedBox(height: 3),
                Text(
                  'Trao đổi kinh nghiệm quanh các lần chẩn đoán',
                  style: agriStyle(size: 13, color: AgriColors.inkA(.7)),
                ),
                const SizedBox(height: 16),
                Row(
                  children: <Widget>[
                    Expanded(
                      child: GlassDropdownField<String?>(
                        label: _diseaseKey == null
                            ? 'Tất cả loại bệnh'
                            : _diseases
                                .firstWhere(
                                  (Disease d) => d.key == _diseaseKey,
                                  orElse: () => _diseases.first,
                                )
                                .name,
                        value: _diseaseKey,
                        sheetTitle: 'Lọc theo bệnh',
                        options: <String?>[null, ..._diseases.map((Disease d) => d.key)],
                        optionLabel: (String? key) => key == null
                            ? 'Tất cả loại bệnh'
                            : _diseases.firstWhere((Disease d) => d.key == key).name,
                        onChanged: (String? key) {
                          setState(() => _diseaseKey = key);
                          _load();
                        },
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: GlassDropdownField<ForumPostKind?>(
                        label: _kind == null ? 'Tất cả loại phản hồi' : forumPostKindLabel(_kind!),
                        value: _kind,
                        sheetTitle: 'Lọc theo loại phản hồi',
                        options: const <ForumPostKind?>[
                          null,
                          ForumPostKind.agree,
                          ForumPostKind.disagree,
                          ForumPostKind.medicineIssue,
                          ForumPostKind.tip,
                        ],
                        optionLabel: (ForumPostKind? k) =>
                            k == null ? 'Tất cả loại phản hồi' : forumPostKindLabel(k),
                        onChanged: (ForumPostKind? k) {
                          setState(() => _kind = k);
                          _load();
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 16),
                if (_loading)
                  const Padding(
                    padding: EdgeInsets.symmetric(vertical: 60),
                    child: Center(child: CircularProgressIndicator()),
                  )
                else if (_error != null)
                  _errorState(_error!)
                else if (_posts.isEmpty)
                  _emptyState()
                else
                  for (int i = 0; i < _posts.length; i++) ...<Widget>[
                    _ForumPostCard(post: _posts[i], onTap: () => _openDetail(_posts[i])),
                    if (i != _posts.length - 1) const SizedBox(height: 10),
                  ],
              ],
            ),
          ),
        ),
        Positioned(
          right: 4,
          bottom: 4,
          child: _ComposeButton(onPressed: _openCompose),
        ),
      ],
    );
  }

  Widget _emptyState() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 46),
      child: Column(
        children: <Widget>[
          Text(
            'Chưa có bài viết nào',
            style: agriStyle(size: 18, weight: FontWeight.w700),
          ),
          const SizedBox(height: 6),
          Text(
            'Nhấn nút "+" ở góc dưới để bắt đầu trao đổi kinh nghiệm.',
            textAlign: TextAlign.center,
            style: agriStyle(size: 14, color: AgriColors.inkA(.68)),
          ),
        ],
      ),
    );
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
          Material(
            color: const Color(0x00000000),
            child: InkWell(onTap: _load, child: const Text('Thử lại')),
          ),
        ],
      ),
    );
  }
}

class _ComposeButton extends StatelessWidget {
  const _ComposeButton({required this.onPressed});

  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        boxShadow: AgriShadows.fab(),
      ),
      child: Material(
        color: const Color(0x00000000),
        shape: const CircleBorder(),
        clipBehavior: Clip.antiAlias,
        child: InkWell(
          onTap: onPressed,
          customBorder: const CircleBorder(),
          child: Ink(
            width: 58,
            height: 58,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: agriPrimaryGradient,
              border: Border.all(color: AgriColors.whiteA(.5), width: 3),
            ),
            child: Center(child: AgriIcons.plus(24, const Color(0xFFFFFFFF))),
          ),
        ),
      ),
    );
  }
}

class _ForumPostCard extends StatelessWidget {
  const _ForumPostCard({required this.post, required this.onTap});

  final ForumPost post;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      style: GlassStyle.listRow,
      radius: 24,
      shadows: AgriShadows.card(.1),
      onTap: onTap,
      padding: const EdgeInsets.all(15),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Text(
                  post.diseaseName,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: agriStyle(size: 15.5, weight: FontWeight.w700, em: -0.01),
                ),
              ),
              const SizedBox(width: 8),
              PillTag(
                label: forumPostKindLabel(post.kind),
                background: AgriColors.oliveA(.14),
                foreground: AgriColors.oliveInk,
                fontSize: 10.5,
                fontWeight: FontWeight.w700,
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
              ),
            ],
          ),
          const SizedBox(height: 6),
          Text(
            post.content,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: agriStyle(size: 13.5, height: 1.45, color: AgriColors.inkA(.82)),
          ),
          if (post.diagnosisSummary != null) ...<Widget>[
            const SizedBox(height: 8),
            Row(
              children: <Widget>[
                AgriIcons.tabHistory(14, AgriColors.inkA(.6)),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    post.diagnosisSummary!,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: agriStyle(size: 12, color: AgriColors.inkA(.62)),
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 10),
          Row(
            children: <Widget>[
              Text(
                '${post.userFullName} · ${post.createdAt}',
                style: agriStyle(size: 11.5, color: AgriColors.inkA(.6)),
              ),
              const Spacer(),
              AgriIcons.heart(15, filled: false, color: AgriColors.inkA(.55)),
              const SizedBox(width: 4),
              Text(
                '${post.likesCount}',
                style: agriStyle(size: 11.5, weight: FontWeight.w600, color: AgriColors.inkA(.6)),
              ),
              const SizedBox(width: 10),
              AgriIcons.tabForum(15, AgriColors.inkA(.55)),
              const SizedBox(width: 4),
              Text(
                '${post.comments.length}',
                style: agriStyle(size: 11.5, weight: FontWeight.w600, color: AgriColors.inkA(.6)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
