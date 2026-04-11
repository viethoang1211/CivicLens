import '../api/api_client.dart';

class StaffRoutingApi {
  final ApiClient _client;

  StaffRoutingApi(this._client);

  Future<Map<String, dynamic>> routeSubmission(String submissionId) async {
    final response = await _client.post('/v1/staff/submissions/$submissionId/route');
    return response.data;
  }

  Future<Map<String, dynamic>> getDepartmentQueue({
    required String departmentId,
    String status = 'active',
    String priority = 'all',
    int page = 1,
    int perPage = 20,
  }) async {
    final response = await _client.get(
      '/v1/staff/departments/$departmentId/queue',
      queryParameters: {
        'status': status,
        'priority': priority,
        'page': page,
        'per_page': perPage,
      },
    );
    return response.data;
  }
}
