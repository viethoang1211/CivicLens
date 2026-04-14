import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';
import 'capture_step_widget.dart';
import 'dossier_summary_screen.dart';

/// Step-by-step guided document capture screen.
///
/// Receives a [DossierDto] after creation, renders vertical list of
/// [CaptureStepWidget] from `requirementSnapshot.groups`, tracks which
/// steps have documents, shows completeness progress, and FAB for submit.
class GuidedCaptureScreen extends StatefulWidget {
  final DossierDto initialDossier;
  final DossierApi dossierApi;

  const GuidedCaptureScreen({
    super.key,
    required this.initialDossier,
    required this.dossierApi,
  });

  @override
  State<GuidedCaptureScreen> createState() => _GuidedCaptureScreenState();
}

class _GuidedCaptureScreenState extends State<GuidedCaptureScreen> {
  late DossierDto _dossier;
  bool _loading = false;
  Timer? _pollTimer;
  int _pollCount = 0;
  static const int _maxPolls = 10;

  @override
  void initState() {
    super.initState();
    _dossier = widget.initialDossier;
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  List<Map<String, dynamic>> get _groups {
    final snapshot = _dossier.requirementSnapshot;
    if (snapshot != null) {
      final groups = (snapshot['groups'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();
      groups.sort((a, b) => (a['group_order'] as int? ?? 0).compareTo(b['group_order'] as int? ?? 0));
      return groups;
    }
    // Fallback for pre-migration dossiers: convert requirementGroups DTOs to maps
    return _dossier.requirementGroups.map((g) => {
      'id': g.id,
      'group_order': g.groupOrder,
      'label': g.label,
      'is_mandatory': g.isMandatory,
      'slots': g.slots.map((s) => {
        'id': s.id,
        'document_type_id': s.documentTypeId,
        'document_type_code': s.documentTypeCode,
        'document_type_name': s.label,
        'description': null,
        'classification_prompt': null,
        'label_override': s.labelOverride,
      }).toList(),
    }).toList();
  }

  int get _mandatoryCount => _groups.where((g) => g['is_mandatory'] == true).length;

  int get _fulfilledMandatoryCount {
    int count = 0;
    for (final group in _groups) {
      if (group['is_mandatory'] != true) continue;
      final slotIds = (group['slots'] as List<dynamic>? ?? [])
          .cast<Map<String, dynamic>>()
          .map((s) => s['id'] as String)
          .toSet();
      final hasFulfilled = _dossier.documents.any(
        (d) => d.requirementSlotId != null && slotIds.contains(d.requirementSlotId),
      );
      if (hasFulfilled) count++;
    }
    return count;
  }

  bool get _isComplete => _mandatoryCount > 0 && _fulfilledMandatoryCount == _mandatoryCount;

  double get _progress => _mandatoryCount > 0 ? _fulfilledMandatoryCount / _mandatoryCount : 0.0;

  Future<void> _refreshDossier() async {
    setState(() => _loading = true);
    try {
      final updated = await widget.dossierApi.getDossier(_dossier.id);
      if (mounted) setState(() => _dossier = updated);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi tải dữ liệu: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _startPollingForValidation() {
    _pollTimer?.cancel();
    _pollCount = 0;
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (timer) async {
      _pollCount++;
      if (_pollCount >= _maxPolls) {
        timer.cancel();
        return;
      }
      try {
        final updated = await widget.dossierApi.getDossier(_dossier.id);
        if (mounted) {
          setState(() => _dossier = updated);
          // Stop polling if all documents have AI results
          final hasPending = updated.documents.any(
            (d) => d.aiMatchResult == null,
          );
          if (!hasPending) timer.cancel();
        }
      } catch (_) {
        // Polling is best-effort
      }
    });
  }

  void _onDocumentChanged() async {
    await _refreshDossier();
    _startPollingForValidation();
  }

  List<DossierDocumentDto> _docsForGroup(Map<String, dynamic> group) {
    final slotIds = (group['slots'] as List<dynamic>? ?? [])
        .cast<Map<String, dynamic>>()
        .map((s) => s['id'] as String)
        .toSet();
    return _dossier.documents
        .where((d) => d.requirementSlotId != null && slotIds.contains(d.requirementSlotId))
        .toList();
  }

  Future<void> _submitDossier() async {
    if (!_isComplete) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Hồ sơ chưa đầy đủ — vui lòng chụp tất cả tài liệu bắt buộc')),
      );
      return;
    }

    // Navigate to summary screen for review before submission
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => DossierSummaryScreen(
          dossier: _dossier,
          dossierApi: widget.dossierApi,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final caseTypeName =
        _dossier.requirementSnapshot?['case_type_name'] as String? ??
            _dossier.caseTypeName ??
            'Hồ sơ';

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(caseTypeName, style: const TextStyle(fontSize: 16)),
            Text(
              '$_fulfilledMandatoryCount / $_mandatoryCount bắt buộc',
              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.normal),
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: _loading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh),
            onPressed: _loading ? null : _refreshDossier,
          ),
        ],
      ),
      body: Column(
        children: [
          // Progress bar
          LinearProgressIndicator(
            value: _progress,
            backgroundColor: Colors.grey.shade200,
            color: _isComplete ? Colors.green : Colors.blue,
          ),
          // Completeness status
          Container(
            width: double.infinity,
            color: _isComplete ? Colors.green.shade50 : Colors.orange.shade50,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Icon(
                  _isComplete ? Icons.check_circle : Icons.info_outline,
                  size: 18,
                  color: _isComplete ? Colors.green : Colors.orange,
                ),
                const SizedBox(width: 8),
                Text(
                  _isComplete
                      ? 'Hồ sơ đầy đủ — sẵn sàng nộp'
                      : 'Vui lòng chụp tất cả tài liệu bắt buộc',
                  style: TextStyle(
                    fontSize: 13,
                    color: _isComplete ? Colors.green.shade800 : Colors.orange.shade800,
                  ),
                ),
              ],
            ),
          ),
          // Step list
          Expanded(
            child: RefreshIndicator(
              onRefresh: _refreshDossier,
              child: ListView.builder(
                padding: const EdgeInsets.all(12),
                itemCount: _groups.length,
                itemBuilder: (context, index) {
                  final group = _groups[index];
                  final docs = _docsForGroup(group);
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: CaptureStepWidget(
                      group: group,
                      uploadedDocuments: docs,
                      dossierId: _dossier.id,
                      dossierApi: widget.dossierApi,
                      onDocumentChanged: _onDocumentChanged,
                      initiallyExpanded: index == 0,
                    ),
                  );
                },
              ),
            ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _submitDossier,
        icon: const Icon(Icons.checklist),
        label: const Text('Kiểm tra & Nộp'),
        backgroundColor: _isComplete ? null : Colors.grey,
      ),
    );
  }
}
