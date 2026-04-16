import 'package:shared_dart/shared_dart.dart';

/// API client methods for citizen-facing endpoints.
class CitizenApi {
  final ApiClient _client;

  CitizenApi({required ApiClient client}) : _client = client;

  // ── Auth ──────────────────────────────────────────────

  /// Exchange VNeID authorization code for JWT token.
  Future<Map<String, dynamic>> authenticateVneid({
    required String code,
    String? idNumber,
  }) async {
    final response = await _client.post('/v1/citizen/auth/vneid', data: {
      'code': code,
      if (idNumber != null) 'id_number': idNumber,
    });
    return response.data;
  }

  // ── Submissions ───────────────────────────────────────

  /// List citizen's own submissions with pagination.
  Future<Map<String, dynamic>> listSubmissions({
    int skip = 0,
    int limit = 20,
    String? status,
  }) async {
    final params = <String, dynamic>{'skip': skip, 'limit': limit};
    if (status != null) params['status'] = status;
    final response = await _client.get('/v1/citizen/submissions', queryParameters: params);
    return response.data;
  }

  /// Get detailed submission with workflow steps and annotations.
  Future<Map<String, dynamic>> getSubmission(String submissionId) async {
    final response = await _client.get('/v1/citizen/submissions/$submissionId');
    return response.data;
  }

  // ── Notifications ─────────────────────────────────────

  /// List notifications with unread count.
  Future<Map<String, dynamic>> listNotifications({
    int page = 1,
    int perPage = 20,
  }) async {
    return await _client.get('/v1/citizen/notifications', queryParameters: {
      'page': page,
      'per_page': perPage,
    }).then((r) => r.data);
  }

  /// Mark a notification as read.
  Future<void> markNotificationRead(String notificationId) async {
    await _client.put('/v1/citizen/notifications/$notificationId/read', data: {});
  }

  // ── Push Token ────────────────────────────────────────

  /// Register device push token for EMAS push delivery.
  Future<void> registerPushToken(String token) async {
    await _client.put('/v1/citizen/push-token', data: {'token': token});
  }
}
