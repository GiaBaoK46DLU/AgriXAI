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
/// Phân trang 10 bài/trang — chỉ tải trang hiện tại.
class ForumScreen extends StatefulWidget {
  const ForumScreen({super.key});

  @override
  State<ForumScreen> createState() => _ForumScreenState();
}

class _ForumScreenState extends State<ForumScreen> {
  static const int _pageSize = 10;

  /// `null` nghĩa là "Tất cả loại bệnh".
  String? _diseaseKey;

  /// `null` nghĩa là "Tất cả loại phản hồi".
  ForumPostKind? _kind;

  bool _loading = true;
  String? _error;
  List<ForumPost> _posts = <ForumPost>[];
  List<Disease> _diseases = <Disease>[];
  int _page = 1;
  int _total = 0;

  @override
  void initState() {
    super.initState();
    _load();
  }

  int get _totalPages => _total == 0 ? 1 : ((_total + _pageSize - 1) ~/ _pageSize);

  Future<void> _load({int? page}) async {
    final int targetPage = page ?? _page;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final List<Disease> diseases = _diseases.isEmpty
          ? await session.diseaseService.fetchAll()
          : _diseases;
      final ({List<ForumPost> items, int total}) result = await session.forumService.listPosts(
        diseaseKey: _diseaseKey,
        kind: _kind,
        page: targetPage,
        pageSize: _pageSize,
      );
      if (!mounted) return;
      setState(() {
        _diseases = diseases;
        _posts = result.items;
        _total = result.total;
        _page = targetPage;
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
    if (posted == true) _load(page: 1);
  }

  Future<void> _openDetail(ForumPost post) async {
    await AppNav.push(context, (_) => ForumDetailScreen(postId: post.id));
    _load();
  }

  /// Cập nhật trạng thái like của một bài trong danh sách (optimistic update).
  void _updatePostLike(ForumPost updated) {
    setState(() {
      final int idx = _posts.indexWhere((ForumPost p) => p.id == updated.id);
      if (idx != -1) {
        _posts = List<ForumPost>.of(_posts)..[idx] = updated;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: <Widget>[
        RefreshIndicator(
          onRefresh: () => _load(page: 1),
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
                          _load(page: 1);
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
                          _load(page: 1);
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
                else ...<Widget>[
                  for (int i = 0; i < _posts.length; i++) ...<Widget>[
                    _ForumPostCard(
                      post: _posts[i],
                      onTap: () => _openDetail(_posts[i]),
                      onLikeChanged: _updatePostLike,
                    ),
                    if (i != _posts.length - 1) const SizedBox(height: 10),
                  ],
                  const SizedBox(height: 16),
                  _PaginationBar(
                    page: _page,
                    totalPages: _totalPages,
                    total: _total,
                    onPrev: _page > 1 ? () => _load(page: _page - 1) : null,
                    onNext: _page < _totalPages ? () => _load(page: _page + 1) : null,
                  ),
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

// ─── Nút phân trang ────────────────────────────────────────────────────────

class _PaginationBar extends StatelessWidget {
  const _PaginationBar({
    required this.page,
    required this.totalPages,
    required this.total,
    required this.onPrev,
    required this.onNext,
  });

  final int page;
  final int totalPages;
  final int total;
  final VoidCallback? onPrev;
  final VoidCallback? onNext;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: <Widget>[
        _PageButton(
          label: '← Trước',
          onTap: onPrev,
        ),
        const SizedBox(width: 12),
        Text(
          'Trang $page / $totalPages  ($total bài)',
          style: agriStyle(size: 12.5, color: AgriColors.inkA(.65), weight: FontWeight.w600),
        ),
        const SizedBox(width: 12),
        _PageButton(
          label: 'Tiếp →',
          onTap: onNext,
        ),
      ],
    );
  }
}

class _PageButton extends StatelessWidget {
  const _PageButton({required this.label, required this.onTap});

  final String label;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final bool enabled = onTap != null;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 7),
        decoration: BoxDecoration(
          color: enabled ? AgriColors.primary.withValues(alpha: .12) : Colors.transparent,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: enabled ? AgriColors.primary.withValues(alpha: .35) : AgriColors.inkA(.12),
          ),
        ),
        child: Text(
          label,
          style: agriStyle(
            size: 12.5,
            weight: FontWeight.w700,
            color: enabled ? AgriColors.primary : AgriColors.inkA(.35),
          ),
        ),
      ),
    );
  }
}

// ─── Nút soạn bài ──────────────────────────────────────────────────────────

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

// ─── Card bài viết ─────────────────────────────────────────────────────────

/// Card bài viết — StatefulWidget để quản lý trạng thái like cục bộ,
/// cho phép optimistic update ngay khi nhấn (tim đỏ) mà không cần reload trang.
class _ForumPostCard extends StatefulWidget {
  const _ForumPostCard({
    required this.post,
    required this.onTap,
    required this.onLikeChanged,
  });

  final ForumPost post;
  final VoidCallback onTap;

  /// Gọi lại khi server xác nhận thay đổi trạng thái like, truyền bài viết
  /// đã cập nhật để ForumScreen đồng bộ danh sách.
  final ValueChanged<ForumPost> onLikeChanged;

  @override
  State<_ForumPostCard> createState() => _ForumPostCardState();
}

class _ForumPostCardState extends State<_ForumPostCard> {
  bool _liking = false;

  /// Trạng thái like hiển thị cục bộ (optimistic) — khởi tạo từ dữ liệu server.
  late bool _liked = widget.post.isLikedByMe;
  late int _count = widget.post.likesCount;

  @override
  void didUpdateWidget(_ForumPostCard oldWidget) {
    super.didUpdateWidget(oldWidget);
    // Đồng bộ khi bài viết từ parent được làm mới (ví dụ sau khi refresh trang).
    if (oldWidget.post != widget.post) {
      _liked = widget.post.isLikedByMe;
      _count = widget.post.likesCount;
    }
  }

  Future<void> _toggleLike() async {
    if (_liking) return;

    // Optimistic update — đổi UI ngay, không chờ API
    setState(() {
      _liking = true;
      _liked = !_liked;
      _count += _liked ? 1 : -1;
      if (_count < 0) _count = 0;
    });

    try {
      final ForumPost updated = await session.forumService.likePost(widget.post.id);
      if (mounted) {
        setState(() {
          _liked = updated.isLikedByMe;
          _count = updated.likesCount;
        });
        widget.onLikeChanged(updated);
      }
    } catch (_) {
      // Rollback nếu API thất bại
      if (mounted) {
        setState(() {
          _liked = widget.post.isLikedByMe;
          _count = widget.post.likesCount;
        });
      }
    } finally {
      if (mounted) setState(() => _liking = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final ForumPost post = widget.post;
    return GlassCard(
      style: GlassStyle.listRow,
      radius: 24,
      shadows: AgriShadows.card(.1),
      onTap: widget.onTap,
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
              // Nút like với hiệu ứng animated
              GestureDetector(
                onTap: _toggleLike,
                behavior: HitTestBehavior.opaque,
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                  child: Row(
                    children: <Widget>[
                      AnimatedSwitcher(
                        duration: const Duration(milliseconds: 200),
                        transitionBuilder: (Widget child, Animation<double> anim) =>
                            ScaleTransition(scale: anim, child: child),
                        child: SizedBox(
                          key: ValueKey<bool>(_liked),
                          width: 15,
                          height: 15,
                          child: AgriIcons.heart(
                            15,
                            filled: _liked,
                            color: _liked ? const Color(0xFFE53935) : AgriColors.inkA(.55),
                          ),
                        ),
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '$_count',
                        style: agriStyle(
                          size: 11.5,
                          weight: FontWeight.w600,
                          color: _liked ? const Color(0xFFE53935) : AgriColors.inkA(.6),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(width: 10),
              AgriIcons.tabForum(15, AgriColors.inkA(.55)),
              const SizedBox(width: 4),
              Text(
                '${post.displayCommentsCount}',
                style: agriStyle(size: 11.5, weight: FontWeight.w600, color: AgriColors.inkA(.6)),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
