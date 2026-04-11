import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

class WorkflowTrackerScreen extends StatelessWidget {
  final List<WorkflowStepDto> steps;
  final String submissionStatus;

  const WorkflowTrackerScreen({
    super.key,
    required this.steps,
    required this.submissionStatus,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Processing Status')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status header
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: _headerColor(submissionStatus).withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  Icon(_headerIcon(submissionStatus), color: _headerColor(submissionStatus), size: 32),
                  const SizedBox(width: 12),
                  Text(
                    _headerText(submissionStatus),
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: _headerColor(submissionStatus)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            // Workflow steps
            Expanded(
              child: ListView.builder(
                itemCount: steps.length,
                itemBuilder: (context, index) {
                  final step = steps[index];
                  return _buildStepNode(step, index == steps.length - 1);
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStepNode(WorkflowStepDto step, bool isLast) {
    final color = _stepColor(step.status);
    final icon = _stepIcon(step.status);

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Timeline line + dot
          SizedBox(
            width: 40,
            child: Column(
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: color,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(icon, size: 14, color: Colors.white),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(width: 2, color: color.withValues(alpha: 0.3)),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          // Content
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          step.departmentName,
                          style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: color),
                        ),
                      ),
                      if (step.isDelayed)
                        const Chip(
                          label: Text('Delayed', style: TextStyle(color: Colors.white, fontSize: 10)),
                          backgroundColor: Colors.red,
                          padding: EdgeInsets.zero,
                        ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _stepStatusText(step),
                    style: const TextStyle(fontSize: 13, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _stepColor(String status) {
    switch (status) {
      case 'completed': return Colors.green;
      case 'active': return Colors.blue;
      case 'delayed': return Colors.orange;
      default: return Colors.grey;
    }
  }

  IconData _stepIcon(String status) {
    switch (status) {
      case 'completed': return Icons.check;
      case 'active': return Icons.play_arrow;
      default: return Icons.circle;
    }
  }

  String _stepStatusText(WorkflowStepDto step) {
    if (step.completedAt != null) return 'Completed: ${step.completedAt!.toLocal().toString().split('.')[0]}';
    if (step.startedAt != null) return 'Started: ${step.startedAt!.toLocal().toString().split('.')[0]}';
    return 'Pending';
  }

  Color _headerColor(String status) {
    switch (status) {
      case 'completed': return Colors.green;
      case 'rejected': return Colors.red;
      case 'in_progress': return Colors.blue;
      default: return Colors.grey;
    }
  }

  IconData _headerIcon(String status) {
    switch (status) {
      case 'completed': return Icons.check_circle;
      case 'rejected': return Icons.cancel;
      case 'in_progress': return Icons.pending;
      default: return Icons.hourglass_empty;
    }
  }

  String _headerText(String status) {
    switch (status) {
      case 'completed': return 'Hoàn thành';
      case 'rejected': return 'Bị từ chối';
      case 'in_progress': return 'Đang xử lý';
      default: return 'Đang chờ';
    }
  }
}
