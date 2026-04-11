import '../api/api_client.dart';

class StaffClassificationApi {
  final ApiClient _client;

  StaffClassificationApi(this._client);

  Future<Map<String, dynamic>> getClassification(String submissionId) async {
    final response = await _client.get('/v1/staff/submissions/$submissionId/classification');
    return response.data;
  }

  Future<Map<String, dynamic>> confirmClassification({
    required String submissionId,
    required String documentTypeId,
    Map<String, dynamic>? templateData,
    String classificationMethod = 'ai_confirmed',
  }) async {
    final response = await _client.post(
      '/v1/staff/submissions/$submissionId/confirm-classification',
      data: {
        'document_type_id': documentTypeId,
        'template_data': templateData,
        'classification_method': classificationMethod,
      },
    );
    return response.data;
  }
}
