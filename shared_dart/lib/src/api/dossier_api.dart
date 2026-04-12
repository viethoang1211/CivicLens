import 'dart:io';
import 'package:dio/dio.dart';
import '../api/api_client.dart';
import '../models/case_type.dart';
import '../models/dossier.dart';

class DossierApi {
  final ApiClient _client;

  DossierApi(this._client);

  // ── Case Types ──────────────────────────────────────────────────────────

  Future<List<CaseTypeDto>> listCaseTypes({bool activeOnly = true}) async {
    final response = await _client.get<Map<String, dynamic>>(
      '/v1/staff/admin/case-types',
      queryParameters: {'active_only': activeOnly},
    );
    final data = response.data as Map<String, dynamic>;
    final items = data['items'] as List<dynamic>? ?? [];
    return items
        .map((e) => CaseTypeDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<CaseTypeDto> getCaseType(String caseTypeId) async {
    final response = await _client.get<Map<String, dynamic>>(
      '/v1/staff/admin/case-types/$caseTypeId',
    );
    return CaseTypeDto.fromJson(response.data as Map<String, dynamic>);
  }

  // ── Staff Dossier Operations ─────────────────────────────────────────────

  Future<DossierDto> createDossier({
    required String citizenIdNumber,
    required String caseTypeId,
    int securityClassification = 0,
    String priority = 'normal',
  }) async {
    final response = await _client.post<Map<String, dynamic>>(
      '/v1/staff/dossiers',
      data: {
        'citizen_id_number': citizenIdNumber,
        'case_type_id': caseTypeId,
        'security_classification': securityClassification,
        'priority': priority,
      },
    );
    return DossierDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<DossierDto> getDossier(String dossierId) async {
    final response = await _client.get<Map<String, dynamic>>(
      '/v1/staff/dossiers/$dossierId',
    );
    return DossierDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> listDossiers({
    String? status,
    String? caseTypeId,
    String? citizenId,
    int page = 1,
    int pageSize = 20,
  }) async {
    final params = <String, dynamic>{
      'page': page,
      'page_size': pageSize,
    };
    if (status != null) params['status'] = status;
    if (caseTypeId != null) params['case_type_id'] = caseTypeId;
    if (citizenId != null) params['citizen_id'] = citizenId;

    final response = await _client.get<Map<String, dynamic>>(
      '/v1/staff/dossiers',
      queryParameters: params,
    );
    final data = response.data as Map<String, dynamic>;
    final items = (data['items'] as List<dynamic>? ?? [])
        .map((e) => DossierListItemDto.fromJson(e as Map<String, dynamic>))
        .toList();
    return {'items': items, 'total': data['total'], 'page': data['page']};
  }

  Future<DossierDocumentDto> uploadDocument({
    required String dossierId,
    required String? requirementSlotId,
    required List<File> pages,
  }) async {
    final fields = <String, dynamic>{};
    if (requirementSlotId != null) {
      fields['requirement_slot_id'] = requirementSlotId;
    }
    final multipartPages = await Future.wait(
      pages.asMap().entries.map(
        (entry) async => MapEntry(
          'pages',
          await MultipartFile.fromFile(
            entry.value.path,
            filename: 'page_${entry.key + 1}.jpg',
          ),
        ),
      ),
    );
    final formData = FormData.fromMap({
      ...fields,
      'pages': multipartPages.map((e) => e.value).toList(),
    });
    final response = await _client.dio.post<Map<String, dynamic>>(
      '/v1/staff/dossiers/$dossierId/documents',
      data: formData,
    );
    return DossierDocumentDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> deleteDocument({
    required String dossierId,
    required String documentId,
  }) async {
    await _client.dio.delete(
      '/v1/staff/dossiers/$dossierId/documents/$documentId',
    );
  }

  Future<DossierDocumentDto> overrideAiDecision({
    required String dossierId,
    required String documentId,
    String? staffNotes,
  }) async {
    final response = await _client.dio.patch<Map<String, dynamic>>(
      '/v1/staff/dossiers/$dossierId/documents/$documentId/override-ai',
      data: {'staff_notes': staffNotes},
    );
    return DossierDocumentDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<DossierDto> submitDossier(String dossierId) async {
    final response = await _client.post<Map<String, dynamic>>(
      '/v1/staff/dossiers/$dossierId/submit',
    );
    return DossierDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<DossierDto> updatePriority({
    required String dossierId,
    required String priority,
  }) async {
    final response = await _client.dio.patch<Map<String, dynamic>>(
      '/v1/staff/dossiers/$dossierId',
      data: {'priority': priority},
    );
    return DossierDto.fromJson(response.data as Map<String, dynamic>);
  }

  // ── Admin Case Type Management ───────────────────────────────────────────

  Future<CaseTypeDto> adminCreateCaseType({
    required String name,
    required String code,
    String? description,
    int retentionYears = 5,
    bool retentionPermanent = false,
    required List<Map<String, dynamic>> requirementGroups,
    required List<Map<String, dynamic>> routingSteps,
  }) async {
    final response = await _client.post<Map<String, dynamic>>(
      '/v1/staff/admin/case-types',
      data: {
        'name': name,
        'code': code,
        if (description != null) 'description': description,
        'retention_years': retentionYears,
        'retention_permanent': retentionPermanent,
        'requirement_groups': requirementGroups,
        'routing_steps': routingSteps,
      },
    );
    return CaseTypeDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<CaseTypeDto> adminUpdateCaseType({
    required String caseTypeId,
    String? name,
    String? description,
    int? retentionYears,
    bool? retentionPermanent,
  }) async {
    final body = <String, dynamic>{};
    if (name != null) body['name'] = name;
    if (description != null) body['description'] = description;
    if (retentionYears != null) body['retention_years'] = retentionYears;
    if (retentionPermanent != null) body['retention_permanent'] = retentionPermanent;
    final response = await _client.put<Map<String, dynamic>>(
      '/v1/staff/admin/case-types/$caseTypeId',
      data: body,
    );
    return CaseTypeDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<void> adminDeactivateCaseType(String caseTypeId) async {
    await _client.post('/v1/staff/admin/case-types/$caseTypeId/deactivate');
  }

  Future<void> adminActivateCaseType(String caseTypeId) async {
    await _client.post('/v1/staff/admin/case-types/$caseTypeId/activate');
  }

  Future<CaseTypeDto> adminUpdateRequirementGroups({
    required String caseTypeId,
    required List<Map<String, dynamic>> requirementGroups,
  }) async {
    final response = await _client.put<Map<String, dynamic>>(
      '/v1/staff/admin/case-types/$caseTypeId/requirement-groups',
      data: {'requirement_groups': requirementGroups},
    );
    return CaseTypeDto.fromJson(response.data as Map<String, dynamic>);
  }

  Future<CaseTypeDto> adminUpdateRoutingSteps({
    required String caseTypeId,
    required List<Map<String, dynamic>> routingSteps,
  }) async {
    final response = await _client.put<Map<String, dynamic>>(
      '/v1/staff/admin/case-types/$caseTypeId/routing-steps',
      data: {'routing_steps': routingSteps},
    );
    return CaseTypeDto.fromJson(response.data as Map<String, dynamic>);
  }
}
