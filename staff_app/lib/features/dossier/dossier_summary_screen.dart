import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';
import '../../core/widgets/ai_validation_badge.dart';

/// Pre-submit summary screen showing all captured documents with
/// validation status, and post-submit receipt with reference number.
class DossierSummaryScreen extends StatefulWidget {
  final DossierDto dossier;
  final DossierApi dossierApi;

  const DossierSummaryScreen({
    super.key,
    required this.dossier,
    required this.dossierApi,
  });

  @override
  State<DossierSummaryScreen> createState() => _DossierSummaryScreenState();
}

class _DossierSummaryScreenState extends State<DossierSummaryScreen> {
  bool _submitting = false;
  DossierDto? _submittedDossier;

  List<Map<String, dynamic>> get _groups {
    final snapshot = widget.dossier.requirementSnapshot;
    if (snapshot == null) return [];
    final groups = (snapshot['groups'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();
    groups.sort((a, b) => (a['group_order'] as int? ?? 0).compareTo(b['group_order'] as int? ?? 0));
    return groups;
  }

  List<DossierDocumentDto> _docsForGroup(Map<String, dynamic> group) {
    final slotIds = (group['slots'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>()
        .map((s) => s['id'] as String)
        .toSet();
    return widget.dossier.documents
        .where((d) => d.requirementSlotId != null && slotIds.contains(d.requirementSlotId))
        .toList();
  }

  String _statusLabel(Map<String, dynamic> group, List<DossierDocumentDto> docs) {
    if (docs.isEmpty) {
      return group['is_mandatory'] == true ? 'Thiếu (bắt buộc)' : 'Bỏ qua';
    }
    final doc = docs.first;
    if (doc.aiMatchOverridden) return 'Đã ghi đè AI';
    if (doc.aiMatchResult == null) return 'Chưa xác minh';
    final confidence = (doc.aiMatchResult!['confidence'] as num?)?.toDouble() ?? 0.0;
    if (confidence >= 0.7) return 'Đã xác minh';
    if (confidence >= 0.4) return 'Cần kiểm tra';
    return 'Không khớp';
  }

  IconData _statusIcon(Map<String, dynamic> group, List<DossierDocumentDto> docs) {
    if (docs.isEmpty) {
      return group['is_mandatory'] == true ? Icons.error : Icons.remove_circle_outline;
    }
    final doc = docs.first;
    if (doc.aiMatchOverridden) return Icons.verified_user;
    if (doc.aiMatchResult == null) return Icons.hourglass_empty;
    final confidence = (doc.aiMatchResult!['confidence'] as num?)?.toDouble() ?? 0.0;
    if (confidence >= 0.7) return Icons.check_circle;
    if (confidence >= 0.4) return Icons.warning_amber;
    return Icons.cancel;
  }

  Color _statusColor(Map<String, dynamic> group, List<DossierDocumentDto> docs) {
    if (docs.isEmpty) {
      return group['is_mandatory'] == true ? Colors.red : Colors.grey;
    }
    final doc = docs.first;
    if (doc.aiMatchOverridden) return Colors.blue;
    if (doc.aiMatchResult == null) return Colors.grey;
    final confidence = (doc.aiMatchResult!['confidence'] as num?)?.toDouble() ?? 0.0;
    if (confidence >= 0.7) return Colors.green;
    if (confidence >= 0.4) return Colors.orange;
    return Colors.red;
  }

  Future<void> _submit() async {
    setState(() => _submitting = true);
    try {
      final result = await widget.dossierApi.submitDossier(widget.dossier.id);
      if (mounted) setState(() => _submittedDossier = result);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_submittedDossier != null) {
      return _buildReceiptScreen(_submittedDossier!);
    }
    return _buildSummaryScreen();
  }

  Widget _buildSummaryScreen() {
    final caseTypeName =
        widget.dossier.requirementSnapshot?['case_type_name'] as String? ??
            widget.dossier.caseTypeName ??
            'Hồ sơ';

    return Scaffold(
      appBar: AppBar(title: const Text('Kiểm tra hồ sơ')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Case type header
          Card(
            color: Colors.blue.shade50,
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    caseTypeName,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'Trạng thái: ${widget.dossier.status}',
                    style: TextStyle(fontSize: 13, color: Colors.grey.shade700),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Document checklist
          Text(
            'Tài liệu đã chụp',
            style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 8),
          ..._groups.map((group) {
            final docs = _docsForGroup(group);
            final label = group['label'] as String? ?? '';
            final isMandatory = group['is_mandatory'] as bool? ?? true;

            return Card(
              child: ListTile(
                leading: Icon(
                  _statusIcon(group, docs),
                  color: _statusColor(group, docs),
                ),
                title: Text(label, style: const TextStyle(fontSize: 14)),
                subtitle: Row(
                  children: [
                    Text(
                      _statusLabel(group, docs),
                      style: TextStyle(
                        fontSize: 12,
                        color: _statusColor(group, docs),
                      ),
                    ),
                    if (docs.isNotEmpty) ...[
                      const Text(' • ', style: TextStyle(fontSize: 12)),
                      Text('${docs.first.pageCount} trang', style: const TextStyle(fontSize: 12)),
                    ],
                    if (!isMandatory) ...[
                      const Text(' • ', style: TextStyle(fontSize: 12)),
                      const Text('Tuỳ chọn', style: TextStyle(fontSize: 12, color: Colors.grey)),
                    ],
                  ],
                ),
                trailing: docs.isNotEmpty
                    ? AiValidationBadge(
                        aiMatchResult: docs.first.aiMatchResult,
                        aiMatchOverridden: docs.first.aiMatchOverridden,
                      )
                    : null,
              ),
            );
          }),
          const SizedBox(height: 24),
          // Submit button
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              onPressed: _submitting ? null : _submit,
              icon: _submitting
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.send),
              label: Text(_submitting ? 'Đang nộp...' : 'Nộp hồ sơ'),
            ),
          ),
          const SizedBox(height: 16),
        ],
      ),
    );
  }

  Widget _buildReceiptScreen(DossierDto submitted) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Biên nhận'),
        automaticallyImplyLeading: false,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 72),
              const SizedBox(height: 24),
              const Text(
                'Hồ sơ đã được nộp thành công',
                style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              if (submitted.referenceNumber != null) ...[
                const Text('Mã tham chiếu:', style: TextStyle(fontSize: 14, color: Colors.grey)),
                const SizedBox(height: 8),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  decoration: BoxDecoration(
                    color: Colors.blue.shade50,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: Colors.blue.shade200),
                  ),
                  child: SelectableText(
                    submitted.referenceNumber!,
                    style: const TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.bold,
                      letterSpacing: 2,
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                const Text(
                  'Công dân có thể tra cứu hồ sơ\nvới mã này trên ứng dụng.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey, fontSize: 14),
                ),
              ],
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: () {
                    Navigator.of(context).popUntil((route) => route.isFirst);
                  },
                  child: const Text('Về trang chính'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
