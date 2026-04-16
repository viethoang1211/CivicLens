import 'dart:io';
import 'package:dio/dio.dart';
import '../api/api_client.dart';

class StaffSubmissionsApi {
  final ApiClient _client;

  StaffSubmissionsApi(this._client);

  Future<Map<String, dynamic>> createSubmission({
    String? citizenIdNumber,
    int securityClassification = 0,
    String priority = 'normal',
  }) async {
    final data = <String, dynamic>{
      'security_classification': securityClassification,
      'priority': priority,
    };
    if (citizenIdNumber != null) {
      data['citizen_id_number'] = citizenIdNumber;
    }
    final response = await _client.post('/v1/staff/submissions', data: data);
    return response.data;
  }

  Future<Map<String, dynamic>> uploadPage({
    required String submissionId,
    required int pageNumber,
    required File imageFile,
  }) async {
    final formData = FormData.fromMap({
      'page_number': pageNumber,
      'image': await MultipartFile.fromFile(imageFile.path),
    });
    final response = await _client.dio.post(
      '/v1/staff/submissions/$submissionId/pages',
      data: formData,
    );
    return response.data;
  }

  Future<Map<String, dynamic>> finalizeScan(String submissionId) async {
    final response = await _client.post('/v1/staff/submissions/$submissionId/finalize-scan');
    return response.data;
  }

  Future<Map<String, dynamic>> getOcrResults(String submissionId) async {
    final response = await _client.get('/v1/staff/submissions/$submissionId/ocr-results');
    return response.data;
  }

  Future<void> submitCorrections({
    required String submissionId,
    required List<Map<String, dynamic>> pages,
  }) async {
    await _client.put('/v1/staff/submissions/$submissionId/ocr-corrections', data: {
      'pages': pages,
    });
  }
}
