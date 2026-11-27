import 'dart:convert';
import 'dart:io';

import 'package:agrixai_farmer/services/api_client.dart';
import 'package:agrixai_farmer/services/auth_service.dart';
import 'package:agrixai_farmer/services/token_store.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

class _MemoryStore implements TokenStore {
  String? token;
  String? refresh;
  String? user;

  @override
  Future<String?> read() async => token;
  @override
  Future<void> write(String value) async => token = value;
  @override
  Future<void> delete() async => token = null;
  @override
  Future<String?> readRefresh() async => refresh;
  @override
  Future<void> writeRefresh(String value) async => refresh = value;
  @override
  Future<void> deleteRefresh() async => refresh = null;
  @override
  Future<String?> readUser() async => user;
  @override
  Future<void> writeUser(String userJson) async => user = userJson;
  @override
  Future<void> deleteUser() async => user = null;
}

const Map<String, dynamic> _farmer = <String, dynamic>{
  'id': 1,
  'username': 'nongdan',
  'full_name': 'Nông dân thử nghiệm',
  'role': 'farmer',
  'email': null,
  'phone': null,
};

http.Response _json(Object data, {int status = 200, bool expired = false}) => http.Response.bytes(
      utf8.encode(jsonEncode(data)),
      status,
      headers: <String, String>{
        'content-type': 'application/json',
        if (expired) 'www-authenticate': 'Bearer',
      },
    );

AuthService _service(_MemoryStore store, Future<http.Response> Function(http.Request) handler) =>
    AuthService(apiClient: ApiClient(httpClient: MockClient(handler)), tokenStore: store);

Future<http.Response> _offline(http.Request request) async =>
    throw const SocketException('offline');

Future<http.Response> _online(http.Request request) async {
  if (request.url.path.endsWith('/auth/login')) {
    return _json(<String, dynamic>{
      'access_token': 'a',
      'refresh_token': 'r',
      'user': _farmer,
    });
  }
  return _json(_farmer);
}

void main() {
  test('mở app khi mất mạng vẫn giữ phiên đã đăng nhập', () async {
    final _MemoryStore store = _MemoryStore();
    await _service(store, _online).login('nongdan', 'matkhau');

    final CurrentUser? restored = await _service(store, _offline).tryRestore();

    expect(restored?.username, 'nongdan');
    expect(restored?.fullName, 'Nông dân thử nghiệm');
    expect(store.token, 'a');
    expect(store.refresh, 'r');
  });

  test('chưa có hồ sơ đã lưu thì mất mạng vẫn về màn đăng nhập', () async {
    final _MemoryStore store = _MemoryStore()
      ..token = 'a'
      ..refresh = 'r';

    expect(await _service(store, _offline).tryRestore(), isNull);
    expect(store.token, 'a');
  });

  test('khôi phục phiên lúc có mạng thì lưu hồ sơ cho lần mất mạng sau', () async {
    final _MemoryStore store = _MemoryStore()
      ..token = 'a'
      ..refresh = 'r';
    await _service(store, _online).tryRestore();

    final CurrentUser? restored = await _service(store, _offline).tryRestore();

    expect(restored?.username, 'nongdan');
  });

  test('đăng xuất lúc mất mạng cũng xoá hồ sơ đã lưu', () async {
    final _MemoryStore store = _MemoryStore();
    await _service(store, _online).login('nongdan', 'matkhau');
    await _service(store, _offline).logout();

    expect(store.user, isNull);
    expect(await _service(store, _offline).tryRestore(), isNull);
  });

  test('phiên hết hạn thì xoá hồ sơ đã lưu', () async {
    final _MemoryStore store = _MemoryStore()
      ..token = 'cu'
      ..refresh = 'cu'
      ..user = jsonEncode(_farmer);

    final CurrentUser? restored = await _service(
      store,
      (http.Request request) async => _json(
        <String, dynamic>{'detail': 'Phiên đã hết hạn'},
        status: 401,
        expired: true,
      ),
    ).tryRestore();

    expect(restored, isNull);
    expect(store.user, isNull);
  });
}
