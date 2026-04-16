// Shared Dart models for dossiers (Feature 002 - Case-Based Submission)

import 'case_type.dart';

class DossierDocumentDto {
  final String id;
  final String dossierId;
  final String? requirementSlotId;
  final String? documentTypeId;
  final String? documentTypeName;
  final Map<String, dynamic>? aiMatchResult;
  final bool aiMatchOverridden;
  final String? staffNotes;
  final int pageCount;
  final DateTime createdAt;

  DossierDocumentDto({
    required this.id,
    required this.dossierId,
    this.requirementSlotId,
    this.documentTypeId,
    this.documentTypeName,
    this.aiMatchResult,
    this.aiMatchOverridden = false,
    this.staffNotes,
    required this.pageCount,
    required this.createdAt,
  });

  bool get aiMatch => aiMatchResult?['match'] as bool? ?? false;
  double get aiConfidence => (aiMatchResult?['confidence'] as num?)?.toDouble() ?? 0.0;
  String? get aiReason => aiMatchResult?['reason'] as String?;

  factory DossierDocumentDto.fromJson(Map<String, dynamic> json) {
    return DossierDocumentDto(
      id: json['id'] as String,
      dossierId: json['dossier_id'] as String,
      requirementSlotId: json['requirement_slot_id'] as String?,
      documentTypeId: json['document_type_id'] as String?,
      documentTypeName: json['document_type_name'] as String?,
      aiMatchResult: json['ai_match_result'] as Map<String, dynamic>?,
      aiMatchOverridden: json['ai_match_overridden'] as bool? ?? false,
      staffNotes: json['staff_notes'] as String?,
      pageCount: json['page_count'] as int? ?? 0,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }
}

class MissingGroupDto {
  final String groupId;
  final String label;
  final int groupOrder;

  MissingGroupDto({
    required this.groupId,
    required this.label,
    required this.groupOrder,
  });

  factory MissingGroupDto.fromJson(Map<String, dynamic> json) {
    return MissingGroupDto(
      groupId: json['group_id'] as String,
      label: json['label'] as String,
      groupOrder: json['group_order'] as int? ?? 0,
    );
  }
}

class DossierCompletenessDto {
  final bool complete;
  final List<MissingGroupDto> missingGroups;

  DossierCompletenessDto({required this.complete, required this.missingGroups});

  factory DossierCompletenessDto.fromJson(Map<String, dynamic> json) {
    return DossierCompletenessDto(
      complete: json['complete'] as bool,
      missingGroups: (json['missing_groups'] as List<dynamic>? ?? [])
          .map((g) => MissingGroupDto.fromJson(g as Map<String, dynamic>))
          .toList(),
    );
  }
}

class DossierCurrentStepDto {
  final int stepOrder;
  final String departmentName;
  final String status;

  DossierCurrentStepDto({
    required this.stepOrder,
    required this.departmentName,
    required this.status,
  });

  factory DossierCurrentStepDto.fromJson(Map<String, dynamic> json) {
    return DossierCurrentStepDto(
      stepOrder: json['step_order'] as int,
      departmentName: json['department_name'] as String,
      status: json['status'] as String,
    );
  }
}

class DossierDto {
  final String id;
  final String? referenceNumber;
  final String? citizenId;
  final String? citizenName;
  final String caseTypeId;
  final String? caseTypeName;
  final String status;
  final String priority;
  final int securityClassification;
  final String? rejectionReason;
  final DateTime createdAt;
  final DateTime? submittedAt;
  final DateTime? completedAt;
  final List<DocumentRequirementGroupDto> requirementGroups;
  final List<DossierDocumentDto> documents;
  final DossierCompletenessDto? completeness;
  final DossierCurrentStepDto? currentStep;
  final int? totalSteps;
  final int? completedSteps;
  final Map<String, dynamic>? requirementSnapshot;

  DossierDto({
    required this.id,
    this.referenceNumber,
    this.citizenId,
    this.citizenName,
    required this.caseTypeId,
    this.caseTypeName,
    required this.status,
    required this.priority,
    required this.securityClassification,
    this.rejectionReason,
    required this.createdAt,
    this.submittedAt,
    this.completedAt,
    required this.requirementGroups,
    required this.documents,
    this.completeness,
    this.currentStep,
    this.totalSteps,
    this.completedSteps,
    this.requirementSnapshot,
  });

  bool get isDraft => status == 'draft';
  bool get isSubmitted => status != 'draft';
  bool get isCompleted => status == 'completed';
  bool get isRejected => status == 'rejected';

  factory DossierDto.fromJson(Map<String, dynamic> json) {
    return DossierDto(
      id: json['id'] as String,
      referenceNumber: json['reference_number'] as String?,
      citizenId: json['citizen_id'] as String?,
      citizenName: json['citizen_name'] as String?,
      caseTypeId: json['case_type_id'] as String,
      caseTypeName: json['case_type_name'] as String?,
      status: json['status'] as String,
      priority: json['priority'] as String? ?? 'normal',
      securityClassification: json['security_classification'] as int? ?? 0,
      rejectionReason: json['rejection_reason'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
      submittedAt: json['submitted_at'] != null
          ? DateTime.parse(json['submitted_at'] as String)
          : null,
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'] as String)
          : null,
      requirementGroups: (json['requirement_groups'] as List<dynamic>? ?? [])
          .map((g) => DocumentRequirementGroupDto.fromJson(g as Map<String, dynamic>))
          .toList(),
      documents: (json['documents'] as List<dynamic>? ?? [])
          .map((d) => DossierDocumentDto.fromJson(d as Map<String, dynamic>))
          .toList(),
      completeness: json['completeness'] != null
          ? DossierCompletenessDto.fromJson(json['completeness'] as Map<String, dynamic>)
          : null,
      currentStep: json['current_step'] != null
          ? DossierCurrentStepDto.fromJson(json['current_step'] as Map<String, dynamic>)
          : null,
      totalSteps: json['total_steps'] as int?,
      completedSteps: json['completed_steps'] as int?,
      requirementSnapshot: json['requirement_snapshot'] as Map<String, dynamic>?,
    );
  }
}

class DossierListItemDto {
  final String id;
  final String? referenceNumber;
  final String citizenName;
  final String caseTypeName;
  final String status;
  final String priority;
  final DateTime createdAt;
  final DateTime? submittedAt;

  DossierListItemDto({
    required this.id,
    this.referenceNumber,
    required this.citizenName,
    required this.caseTypeName,
    required this.status,
    required this.priority,
    required this.createdAt,
    this.submittedAt,
  });

  factory DossierListItemDto.fromJson(Map<String, dynamic> json) {
    return DossierListItemDto(
      id: json['id'] as String,
      referenceNumber: json['reference_number'] as String?,
      citizenName: json['citizen_name'] as String? ?? '',
      caseTypeName: json['case_type_name'] as String? ?? '',
      status: json['status'] as String,
      priority: json['priority'] as String? ?? 'normal',
      createdAt: DateTime.parse(json['created_at'] as String),
      submittedAt: json['submitted_at'] != null
          ? DateTime.parse(json['submitted_at'] as String)
          : null,
    );
  }
}
