class SubmissionDto {
  final String id;
  final String? documentTypeName;
  final String status;
  final String priority;
  final DateTime submittedAt;
  final DateTime? completedAt;
  final CurrentStepDto? currentStep;
  final int? totalSteps;
  final int? completedSteps;
  final bool isDelayed;
  final Map<String, dynamic>? templateData;
  final int securityClassification;

  SubmissionDto({
    required this.id,
    this.documentTypeName,
    required this.status,
    required this.priority,
    required this.submittedAt,
    this.completedAt,
    this.currentStep,
    this.totalSteps,
    this.completedSteps,
    this.isDelayed = false,
    this.templateData,
    required this.securityClassification,
  });

  factory SubmissionDto.fromJson(Map<String, dynamic> json) {
    return SubmissionDto(
      id: json['id'],
      documentTypeName: json['document_type_name'],
      status: json['status'],
      priority: json['priority'],
      submittedAt: DateTime.parse(json['submitted_at']),
      completedAt: json['completed_at'] != null ? DateTime.parse(json['completed_at']) : null,
      currentStep: json['current_step'] != null ? CurrentStepDto.fromJson(json['current_step']) : null,
      totalSteps: json['total_steps'],
      completedSteps: json['completed_steps'],
      isDelayed: json['is_delayed'] ?? false,
      templateData: json['template_data'],
      securityClassification: json['security_classification'] ?? 0,
    );
  }
}

class CurrentStepDto {
  final int stepOrder;
  final String departmentName;
  final String status;

  CurrentStepDto({required this.stepOrder, required this.departmentName, required this.status});

  factory CurrentStepDto.fromJson(Map<String, dynamic> json) {
    return CurrentStepDto(
      stepOrder: json['step_order'],
      departmentName: json['department_name'],
      status: json['status'],
    );
  }
}

class ScannedPageDto {
  final String id;
  final String submissionId;
  final int pageNumber;
  final String? imageUrl;
  final String? ocrRawText;
  final String? ocrCorrectedText;
  final double? ocrConfidence;
  final double? imageQualityScore;

  ScannedPageDto({
    required this.id,
    required this.submissionId,
    required this.pageNumber,
    this.imageUrl,
    this.ocrRawText,
    this.ocrCorrectedText,
    this.ocrConfidence,
    this.imageQualityScore,
  });

  factory ScannedPageDto.fromJson(Map<String, dynamic> json) {
    return ScannedPageDto(
      id: json['id'],
      submissionId: json['submission_id'],
      pageNumber: json['page_number'],
      imageUrl: json['image_url'],
      ocrRawText: json['ocr_raw_text'],
      ocrCorrectedText: json['ocr_corrected_text'],
      ocrConfidence: json['ocr_confidence']?.toDouble(),
      imageQualityScore: json['image_quality_score']?.toDouble(),
    );
  }
}

class WorkflowStepDto {
  final String id;
  final int stepOrder;
  final String departmentName;
  final String status;
  final DateTime? startedAt;
  final DateTime? completedAt;
  final DateTime? expectedCompleteBy;
  final bool isDelayed;
  final String? result;

  WorkflowStepDto({
    required this.id,
    required this.stepOrder,
    required this.departmentName,
    required this.status,
    this.startedAt,
    this.completedAt,
    this.expectedCompleteBy,
    this.isDelayed = false,
    this.result,
  });

  factory WorkflowStepDto.fromJson(Map<String, dynamic> json) {
    return WorkflowStepDto(
      id: json['id'] ?? '',
      stepOrder: json['step_order'],
      departmentName: json['department_name'],
      status: json['status'],
      startedAt: json['started_at'] != null ? DateTime.parse(json['started_at']) : null,
      completedAt: json['completed_at'] != null ? DateTime.parse(json['completed_at']) : null,
      expectedCompleteBy: json['expected_complete_by'] != null ? DateTime.parse(json['expected_complete_by']) : null,
      isDelayed: json['is_delayed'] ?? false,
      result: json['result'],
    );
  }
}

class NotificationDto {
  final String id;
  final String? submissionId;
  final String type;
  final String title;
  final String body;
  final bool isRead;
  final DateTime sentAt;
  final DateTime? readAt;

  NotificationDto({
    required this.id,
    this.submissionId,
    required this.type,
    required this.title,
    required this.body,
    required this.isRead,
    required this.sentAt,
    this.readAt,
  });

  factory NotificationDto.fromJson(Map<String, dynamic> json) {
    return NotificationDto(
      id: json['id'],
      submissionId: json['submission_id'],
      type: json['type'],
      title: json['title'],
      body: json['body'],
      isRead: json['is_read'],
      sentAt: DateTime.parse(json['sent_at']),
      readAt: json['read_at'] != null ? DateTime.parse(json['read_at']) : null,
    );
  }

  NotificationDto copyWith({
    String? id,
    String? submissionId,
    String? type,
    String? title,
    String? body,
    bool? isRead,
    DateTime? sentAt,
    DateTime? readAt,
  }) {
    return NotificationDto(
      id: id ?? this.id,
      submissionId: submissionId ?? this.submissionId,
      type: type ?? this.type,
      title: title ?? this.title,
      body: body ?? this.body,
      isRead: isRead ?? this.isRead,
      sentAt: sentAt ?? this.sentAt,
      readAt: readAt ?? this.readAt,
    );
  }
}

class ClassificationResultDto {
  final String documentTypeId;
  final String documentTypeName;
  final double confidence;
  final List<ClassificationAlternativeDto> alternatives;
  final Map<String, dynamic>? templateData;

  ClassificationResultDto({
    required this.documentTypeId,
    required this.documentTypeName,
    required this.confidence,
    required this.alternatives,
    this.templateData,
  });

  factory ClassificationResultDto.fromJson(Map<String, dynamic> json) {
    return ClassificationResultDto(
      documentTypeId: json['classification']['document_type_id'],
      documentTypeName: json['classification']['document_type_name'],
      confidence: json['classification']['confidence'].toDouble(),
      alternatives: (json['classification']['alternatives'] as List)
          .map((a) => ClassificationAlternativeDto.fromJson(a))
          .toList(),
      templateData: json['template_data'],
    );
  }
}

class ClassificationAlternativeDto {
  final String documentTypeId;
  final String name;
  final double confidence;

  ClassificationAlternativeDto({required this.documentTypeId, required this.name, required this.confidence});

  factory ClassificationAlternativeDto.fromJson(Map<String, dynamic> json) {
    return ClassificationAlternativeDto(
      documentTypeId: json['document_type_id'],
      name: json['name'],
      confidence: json['confidence'].toDouble(),
    );
  }
}
