import '../models/models.dart';
import 'api_client.dart';

/// Diễn đàn nông dân — cần đã đăng nhập cho mọi thao tác (xem CLAUDE.md).
class ForumService {
  ForumService({ApiClient? apiClient}) : _api = apiClient ?? ApiClient();

  final ApiClient _api;

  Future<({List<ForumPost> items, int total})> listPosts({
    String? diseaseKey,
    ForumPostKind? kind,
    int page = 1,
    int pageSize = 20,
  }) async {
    final Map<String, String> query = <String, String>{
      'page': page.toString(),
      'page_size': pageSize.toString(),
      if (diseaseKey != null) 'disease_key': diseaseKey,
      if (kind != null) 'type': forumPostKindToRaw(kind),
    };
    final String qs = query.entries.map((e) => '${e.key}=${e.value}').join('&');
    final dynamic body = await _api.get('/forum/posts?$qs');
    final Map<String, dynamic> map = body as Map<String, dynamic>;
    final List<ForumPost> items = (map['items'] as List<dynamic>)
        .map((dynamic j) => ForumPost.fromJson(j as Map<String, dynamic>))
        .toList();
    return (items: items, total: map['total'] as int);
  }

  /// Chi tiết một bài viết, kèm toàn bộ bình luận.
  Future<ForumPost> getPost(int id) async {
    final dynamic body = await _api.get('/forum/posts/$id');
    return ForumPost.fromJson(body as Map<String, dynamic>);
  }

  Future<ForumPost> createPost({
    String? diseaseKey,
    int? diagnosisId,
    required ForumPostKind kind,
    required String content,
  }) async {
    final dynamic body = await _api.postJson('/forum/posts', <String, dynamic>{
      if (diseaseKey != null) 'disease_key': diseaseKey,
      if (diagnosisId != null) 'diagnosis_id': diagnosisId,
      'type': forumPostKindToRaw(kind),
      'content': content,
    });
    return ForumPost.fromJson(body as Map<String, dynamic>);
  }

  Future<ForumComment> addComment(int postId, String content) async {
    final dynamic body = await _api.postJson(
      '/forum/posts/$postId/comments',
      <String, dynamic>{'content': content},
    );
    return ForumComment.fromJson(body as Map<String, dynamic>);
  }

  Future<ForumPost> likePost(int postId) async {
    final dynamic body = await _api.postJson('/forum/posts/$postId/like', <String, dynamic>{});
    return ForumPost.fromJson(body as Map<String, dynamic>);
  }
}
