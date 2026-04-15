class DepartmentMetrics {
  final int totalSteps;
  final int completedSteps;
  final int pendingSteps;
  final int delayedSteps;
  final double avgProcessingHours;
  final double delayRate;
  final double completionRate;

  DepartmentMetrics({
    required this.totalSteps,
    required this.completedSteps,
    required this.pendingSteps,
    required this.delayedSteps,
    required this.avgProcessingHours,
    required this.delayRate,
    required this.completionRate,
  });

  factory DepartmentMetrics.fromJson(Map<String, dynamic> json) {
    return DepartmentMetrics(
      totalSteps: json['total_steps'],
      completedSteps: json['completed_steps'],
      pendingSteps: json['pending_steps'],
      delayedSteps: json['delayed_steps'],
      avgProcessingHours: (json['avg_processing_hours'] ?? 0.0).toDouble(),
      delayRate: (json['delay_rate'] ?? 0.0).toDouble(),
      completionRate: (json['completion_rate'] ?? 0.0).toDouble(),
    );
  }
}

class DepartmentSla {
  final String departmentId;
  final String departmentName;
  final String departmentCode;
  final DepartmentMetrics metrics;

  DepartmentSla({
    required this.departmentId,
    required this.departmentName,
    required this.departmentCode,
    required this.metrics,
  });

  factory DepartmentSla.fromJson(Map<String, dynamic> json) {
    return DepartmentSla(
      departmentId: json['department_id'],
      departmentName: json['department_name'],
      departmentCode: json['department_code'],
      metrics: DepartmentMetrics.fromJson(json['metrics']),
    );
  }
}

class SlaPeriod {
  final String from;
  final String to;

  SlaPeriod({required this.from, required this.to});

  factory SlaPeriod.fromJson(Map<String, dynamic> json) {
    return SlaPeriod(
      from: json['from'],
      to: json['to'],
    );
  }
}

class SlaMetricsResponse {
  final SlaPeriod period;
  final List<DepartmentSla> departments;
  final DepartmentMetrics totals;

  SlaMetricsResponse({
    required this.period,
    required this.departments,
    required this.totals,
  });

  factory SlaMetricsResponse.fromJson(Map<String, dynamic> json) {
    return SlaMetricsResponse(
      period: SlaPeriod.fromJson(json['period']),
      departments: (json['departments'] as List)
          .map((d) => DepartmentSla.fromJson(d))
          .toList(),
      totals: DepartmentMetrics.fromJson(json['totals']),
    );
  }
}
