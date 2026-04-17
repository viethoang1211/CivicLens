import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

class SubmissionDetailScreen extends StatefulWidget {
  final CitizenApi citizenApi;
  final String submissionId;

  const SubmissionDetailScreen({
    super.key,
    required this.citizenApi,
    required this.submissionId,
  });

  @override
  State<SubmissionDetailScreen> createState() => _SubmissionDetailScreenState();
}

class _SubmissionDetailScreenState extends State<SubmissionDetailScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final resp = await widget.citizenApi.getSubmission(widget.submissionId);
      setState(() { _data = resp; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  static const _statusLabels = {
    'pending': 'Chờ xử lý',
    'ocr_processing': 'Đang OCR',
    'classifying': 'Đang phân loại',
    'pending_classification': 'Chờ xác nhận',
    'classified': 'Đã phân loại',
    'in_progress': 'Đang xử lý',
    'completed': 'Hoàn thành',
    'rejected': 'Bị từ chối',
  };

  Color _statusColor(String status) => switch (status) {
    'completed' => Colors.green,
    'rejected' => Colors.red,
    'in_progress' => Colors.blue,
    _ => Colors.grey,
  };

  IconData _stepIcon(String status) => switch (status) {
    'completed' => Icons.check_circle,
    'active' => Icons.play_circle_fill,
    'pending' => Icons.radio_button_unchecked,
    _ => Icons.circle_outlined,
  };

  Color _stepColor(String status) => switch (status) {
    'completed' => Colors.green,
    'active' => Colors.blue,
    _ => Colors.grey.shade400,
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chi tiết hồ sơ')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.error_outline, size: 48, color: Colors.red),
                    const SizedBox(height: 8),
                    Text(_error!, textAlign: TextAlign.center),
                    const SizedBox(height: 16),
                    ElevatedButton(onPressed: _load, child: const Text('Thử lại')),
                  ],
                ))
              : RefreshIndicator(
                  onRefresh: _load,
                  child: _buildContent(),
                ),
    );
  }

  Widget _buildContent() {
    final data = _data!;
    final status = data['status'] as String? ?? '';
    final statusLabel = _statusLabels[status] ?? status;
    final docTypeName = data['document_type_name'] as String?;
    final submittedAt = data['submitted_at'] as String?;
    final completedAt = data['completed_at'] as String?;
    final workflow = (data['workflow'] as List?) ?? [];
    final annotations = (data['citizen_annotations'] as List?) ?? [];

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Status card
        Card(
          color: _statusColor(status).withOpacity(0.1),
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Icon(
                    status == 'completed' ? Icons.check_circle
                        : status == 'rejected' ? Icons.cancel
                        : Icons.hourglass_top,
                    color: _statusColor(status),
                    size: 28,
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(statusLabel,
                            style: TextStyle(
                              fontSize: 18, fontWeight: FontWeight.bold,
                              color: _statusColor(status),
                            )),
                        if (docTypeName != null && docTypeName.isNotEmpty)
                          Text(docTypeName, style: const TextStyle(fontSize: 14, color: Colors.black54)),
                      ],
                    ),
                  ),
                ]),
                const SizedBox(height: 12),
                if (submittedAt != null)
                  _infoRow('Ngày nộp', _formatDate(submittedAt)),
                if (completedAt != null)
                  _infoRow('Ngày hoàn thành', _formatDate(completedAt)),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),

        // Workflow timeline
        if (workflow.isNotEmpty) ...[
          const Text('Tiến trình xử lý',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 12),
          ...List.generate(workflow.length, (i) {
            final step = workflow[i] as Map<String, dynamic>;
            final stepStatus = step['status'] as String? ?? 'pending';
            final deptName = step['department_name'] as String? ?? '';
            final result = step['result'] as String?;
            final isLast = i == workflow.length - 1;
            return IntrinsicHeight(
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 32,
                    child: Column(children: [
                      Icon(_stepIcon(stepStatus), color: _stepColor(stepStatus), size: 24),
                      if (!isLast)
                        Expanded(
                          child: Container(
                            width: 2,
                            color: stepStatus == 'completed' ? Colors.green : Colors.grey.shade300,
                          ),
                        ),
                    ]),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 20),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(deptName, style: const TextStyle(fontWeight: FontWeight.w600)),
                          Text(
                            stepStatus == 'completed' ? (result == 'rejected' ? 'Từ chối' : 'Hoàn thành')
                                : stepStatus == 'active' ? 'Đang xử lý'
                                : 'Chờ',
                            style: TextStyle(fontSize: 13, color: _stepColor(stepStatus)),
                          ),
                          if (step['completed_at'] != null)
                            Text(_formatDate(step['completed_at'] as String),
                                style: const TextStyle(fontSize: 11, color: Colors.grey)),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            );
          }),
        ],

        // Citizen-visible annotations (rejection reasons, info requests)
        if (annotations.isNotEmpty) ...[
          const SizedBox(height: 8),
          const Text('Ghi chú từ phòng ban',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...annotations.map<Widget>((a) {
            final ann = a as Map<String, dynamic>;
            final type = ann['type'] as String? ?? '';
            final isRejection = type == 'rejected';
            final isInfo = type == 'needs_info';
            return Card(
              color: isRejection ? Colors.red.shade50
                  : isInfo ? Colors.orange.shade50
                  : Colors.grey.shade50,
              margin: const EdgeInsets.only(bottom: 8),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Icon(
                        isRejection ? Icons.cancel : isInfo ? Icons.info_outline : Icons.comment,
                        color: isRejection ? Colors.red : isInfo ? Colors.orange : Colors.grey,
                        size: 18,
                      ),
                      const SizedBox(width: 8),
                      Text(ann['department_name'] as String? ?? '',
                          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
                    ]),
                    const SizedBox(height: 6),
                    Text(ann['content'] as String? ?? '',
                        style: const TextStyle(fontSize: 14)),
                    if (ann['created_at'] != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text(_formatDate(ann['created_at'] as String),
                            style: const TextStyle(fontSize: 11, color: Colors.grey)),
                      ),
                  ],
                ),
              ),
            );
          }),
        ],
      ],
    );
  }

  Widget _infoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(children: [
        SizedBox(width: 120, child: Text(label, style: const TextStyle(color: Colors.black54, fontSize: 13))),
        Expanded(child: Text(value, style: const TextStyle(fontSize: 13))),
      ]),
    );
  }

  String _formatDate(String iso) {
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }
}
