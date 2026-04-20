// Citizen-facing dossier tracking models (Feature 002 - Case-Based Submission)

const _statusLabelsVi = {
  'draft': 'Bản nháp',
  'in_progress': 'Đang xử lý',
  'completed': 'Hoàn thành',
  'rejected': 'Bị từ chối',
};

class DossierTrackingStepDto {
  final int stepOrder;
  final String departmentName;
  final String status;
  final DateTime? startedAt;
  final DateTime? completedAt;

  DossierTrackingStepDto({
    required this.stepOrder,
    required this.departmentName,
    required this.status,
    this.startedAt,
    this.completedAt,
  });

  factory DossierTrackingStepDto.fromJson(Map<String, dynamic> json) {
    return DossierTrackingStepDto(
      stepOrder: json['step_order'] as int,
      departmentName: json['department_name'] as String,
      status: json['status'] as String,
      startedAt: json['started_at'] != null
          ? DateTime.parse(json['started_at'] as String)
          : null,
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'] as String)
          : null,
    );
  }
}

class DossierTrackingDto {
  final String? id;
  final String? referenceNumber;
  final String caseTypeName;
  final String status;
  final DateTime? submittedAt;
  final DateTime? completedAt;
  final String? rejectionReason;
  final List<DossierTrackingStepDto> steps;

  DossierTrackingDto({
    this.id,
    this.referenceNumber,
    required this.caseTypeName,
    required this.status,
    this.submittedAt,
    this.completedAt,
    this.rejectionReason,
    required this.steps,
  });

  String get statusLabelVi => _statusLabelsVi[status] ?? status;

  bool get isCompleted => status == 'completed';
  bool get isRejected => status == 'rejected';
  bool get isInProgress => status == 'in_progress';

  int get totalSteps => steps.length;
  int get completedSteps => steps.where((s) => s.status == 'completed').length;
  double get progressFraction =>
      totalSteps > 0 ? completedSteps / totalSteps : 0;

  factory DossierTrackingDto.fromJson(Map<String, dynamic> json) {
    return DossierTrackingDto(
      id: json['id'] as String?,
      referenceNumber: json['reference_number'] as String?,
      caseTypeName: json['case_type_name'] as String? ?? '',
      status: json['status'] as String,
      submittedAt: json['submitted_at'] != null
          ? DateTime.parse(json['submitted_at'] as String)
          : null,
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'] as String)
          : null,
      rejectionReason: json['rejection_reason'] as String?,
      steps: (json['workflow_steps'] as List<dynamic>? ?? [])
          .map((s) => DossierTrackingStepDto.fromJson(s as Map<String, dynamic>))
          .toList(),
    );
  }
}

class DossierTrackingListItemDto {
  final String id;
  final String? referenceNumber;
  final String caseTypeName;
  final String status;
  final DateTime? submittedAt;

  DossierTrackingListItemDto({
    required this.id,
    this.referenceNumber,
    required this.caseTypeName,
    required this.status,
    this.submittedAt,
  });

  String get statusLabelVi => _statusLabelsVi[status] ?? status;

  factory DossierTrackingListItemDto.fromJson(Map<String, dynamic> json) {
    return DossierTrackingListItemDto(
      id: json['id'] as String,
      referenceNumber: json['reference_number'] as String?,
      caseTypeName: json['case_type_name'] as String? ?? '',
      status: json['status'] as String,
      submittedAt: json['submitted_at'] != null
          ? DateTime.parse(json['submitted_at'] as String)
          : null,
    );
  }
}
