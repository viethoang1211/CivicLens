// Shared Dart models for case types and document requirements (Feature 002)

class DocumentRequirementSlotDto {
  final String id;
  final String? documentTypeId;
  final String? documentTypeCode;
  final String label;
  final String? labelOverride;
  final String? fulfilledByDocumentId;

  DocumentRequirementSlotDto({
    required this.id,
    this.documentTypeId,
    this.documentTypeCode,
    required this.label,
    this.labelOverride,
    this.fulfilledByDocumentId,
  });

  factory DocumentRequirementSlotDto.fromJson(Map<String, dynamic> json) {
    return DocumentRequirementSlotDto(
      id: json['id'] as String,
      documentTypeId: json['document_type_id'] as String?,
      documentTypeCode: json['document_type_code'] as String?,
      label: (json['label'] ?? json['label_override'] ?? '') as String,
      labelOverride: json['label_override'] as String?,
      fulfilledByDocumentId: json['fulfilled_by_document_id'] as String?,
    );
  }
}

class DocumentRequirementGroupDto {
  final String id;
  final int groupOrder;
  final String label;
  final bool isMandatory;
  final bool isFulfilled;
  final List<DocumentRequirementSlotDto> slots;

  DocumentRequirementGroupDto({
    required this.id,
    required this.groupOrder,
    required this.label,
    required this.isMandatory,
    required this.isFulfilled,
    required this.slots,
  });

  factory DocumentRequirementGroupDto.fromJson(Map<String, dynamic> json) {
    return DocumentRequirementGroupDto(
      id: json['id'] as String,
      groupOrder: json['group_order'] as int,
      label: json['label'] as String,
      isMandatory: json['is_mandatory'] as bool? ?? true,
      isFulfilled: json['is_fulfilled'] as bool? ?? false,
      slots: (json['slots'] as List<dynamic>? ?? [])
          .map((s) => DocumentRequirementSlotDto.fromJson(s as Map<String, dynamic>))
          .toList(),
    );
  }
}

class CaseTypeRoutingStepDto {
  final String id;
  final int stepOrder;
  final String departmentId;
  final String? departmentName;
  final int? expectedDurationHours;
  final int requiredClearanceLevel;

  CaseTypeRoutingStepDto({
    required this.id,
    required this.stepOrder,
    required this.departmentId,
    this.departmentName,
    this.expectedDurationHours,
    required this.requiredClearanceLevel,
  });

  factory CaseTypeRoutingStepDto.fromJson(Map<String, dynamic> json) {
    return CaseTypeRoutingStepDto(
      id: json['id'] as String,
      stepOrder: json['step_order'] as int,
      departmentId: json['department_id'] as String,
      departmentName: json['department_name'] as String?,
      expectedDurationHours: json['expected_duration_hours'] as int?,
      requiredClearanceLevel: json['required_clearance_level'] as int? ?? 0,
    );
  }
}

class CaseTypeDto {
  final String id;
  final String name;
  final String code;
  final String? description;
  final bool isActive;
  final int retentionYears;
  final bool retentionPermanent;
  final List<DocumentRequirementGroupDto> requirementGroups;
  final List<CaseTypeRoutingStepDto> routingSteps;

  CaseTypeDto({
    required this.id,
    required this.name,
    required this.code,
    this.description,
    required this.isActive,
    required this.retentionYears,
    required this.retentionPermanent,
    required this.requirementGroups,
    required this.routingSteps,
  });

  factory CaseTypeDto.fromJson(Map<String, dynamic> json) {
    return CaseTypeDto(
      id: json['id'] as String,
      name: json['name'] as String,
      code: json['code'] as String,
      description: json['description'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      retentionYears: json['retention_years'] as int? ?? 5,
      retentionPermanent: json['retention_permanent'] as bool? ?? false,
      requirementGroups: (json['requirement_groups'] as List<dynamic>? ?? [])
          .map((g) => DocumentRequirementGroupDto.fromJson(g as Map<String, dynamic>))
          .toList(),
      routingSteps: (json['routing_steps'] as List<dynamic>? ?? [])
          .map((s) => CaseTypeRoutingStepDto.fromJson(s as Map<String, dynamic>))
          .toList(),
    );
  }
}
