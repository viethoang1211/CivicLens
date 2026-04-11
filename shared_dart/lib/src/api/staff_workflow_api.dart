import 'package:shared_dart/shared_dart.dart';

/// API client methods for staff workflow step operations.
class StaffWorkflowApi {
  final ApiClient _client;

  StaffWorkflowApi({required ApiClient client}) : _client = client;

  /// Get full review context for a workflow step.
  Future<Map<String, dynamic>> getStepDetail(String stepId) async {
    final response = await _client.get('/v1/staff/workflow-steps/$stepId');
    return response.data;
  }

  /// Complete a workflow step with review decision.
  Future<Map<String, dynamic>> completeStep({
    required String stepId,
    required String result,
    required String comment,
    bool targetCitizen = false,
  }) async {
    final response = await _client.post(
      '/v1/staff/workflow-steps/$stepId/complete',
      data: {
        'result': result,
        'comment': comment,
        'target_citizen': targetCitizen,
      },
    );
    return response.data;
  }

  /// Create a cross-department consultation.
  Future<Map<String, dynamic>> createConsultation({
    required String stepId,
    required String targetDepartmentId,
    required String question,
  }) async {
    final response = await _client.post(
      '/v1/staff/workflow-steps/$stepId/consultations',
      data: {
        'target_department_id': targetDepartmentId,
        'question': question,
      },
    );
    return response.data;
  }
}
