import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';
import 'document_slot_card.dart';

/// Main dossier screen showing checklist of document requirement groups
/// and allowing staff to upload documents for each slot.
class DossierScreen extends StatefulWidget {
  final String dossierId;
  final DossierApi dossierApi;

  const DossierScreen({
    super.key,
    required this.dossierId,
    required this.dossierApi,
  });

  @override
  State<DossierScreen> createState() => _DossierScreenState();
}

class _DossierScreenState extends State<DossierScreen> {
  DossierDto? _dossier;
  bool _loading = true;
  bool _submitting = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDossier();
  }

  Future<void> _loadDossier() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final dossier = await widget.dossierApi.getDossier(widget.dossierId);
      setState(() {
        _dossier = dossier;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  Future<void> _onDocumentUploaded() async {
    await _loadDossier();
  }

  Future<void> _onDocumentDeleted() async {
    await _loadDossier();
  }

  Future<void> _confirmAndSubmit() async {
    final dossier = _dossier;
    if (dossier == null) return;

    final completeness = dossier.completeness;
    if (completeness != null && !completeness.complete) {
      final missing = completeness.missingGroups.map((g) => '• ${g.label}').join('\n');
      final proceed = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Hồ sơ chưa đầy đủ'),
          content: Text('Các nhóm tài liệu còn thiếu:\n$missing\n\nBạn có muốn nộp hồ sơ không?'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Huỷ')),
            TextButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Vẫn nộp'),
            ),
          ],
        ),
      );
      if (proceed != true) return;
    } else {
      final confirm = await showDialog<bool>(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Xác nhận nộp hồ sơ'),
          content: const Text('Hồ sơ sẽ được nộp và bắt đầu quy trình xử lý. Tiếp tục?'),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Huỷ')),
            ElevatedButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Nộp hồ sơ'),
            ),
          ],
        ),
      );
      if (confirm != true) return;
    }

    setState(() => _submitting = true);
    try {
      final submitted = await widget.dossierApi.submitDossier(widget.dossierId);
      if (!mounted) return;
      await showDialog(
        context: context,
        barrierDismissible: false,
        builder: (ctx) => AlertDialog(
          title: const Text('Đã nộp hồ sơ'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.check_circle, color: Colors.green, size: 48),
              const SizedBox(height: 16),
              if (submitted.referenceNumber != null) ...[
                const Text('Mã tham chiếu:'),
                const SizedBox(height: 4),
                SelectableText(
                  submitted.referenceNumber!,
                  style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Công dân có thể tra cứu hồ sơ với mã này.',
                  textAlign: TextAlign.center,
                  style: TextStyle(color: Colors.grey),
                ),
              ],
            ],
          ),
          actions: [
            ElevatedButton(
              onPressed: () {
                Navigator.pop(ctx);
                Navigator.of(context).pop(true); // Return to caller with success=true
              },
              child: const Text('Xong'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Lỗi: ${e.toString()}')),
      );
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Hồ sơ')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Hồ sơ')),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: _loadDossier, child: const Text('Thử lại')),
            ],
          ),
        ),
      );
    }

    final dossier = _dossier!;
    final completeness = dossier.completeness;
    final isComplete = completeness?.complete ?? false;

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(dossier.caseTypeName ?? 'Hồ sơ'),
            if (dossier.referenceNumber != null)
              Text(
                dossier.referenceNumber!,
                style: const TextStyle(fontSize: 12, fontWeight: FontWeight.normal),
              ),
          ],
        ),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadDossier),
        ],
      ),
      body: dossier.isSubmitted
          ? _buildSubmittedView(dossier)
          : RefreshIndicator(
              onRefresh: _loadDossier,
              child: CustomScrollView(
                slivers: [
                  if (completeness != null)
                    SliverToBoxAdapter(
                      child: _buildCompletenessHeader(completeness, isComplete),
                    ),
                  SliverPadding(
                    padding: const EdgeInsets.all(16),
                    sliver: SliverList(
                      delegate: SliverChildBuilderDelegate(
                        (context, index) {
                          final group = dossier.requirementGroups[index];
                          final groupDocs = dossier.documents
                              .where((d) => group.slots.any((s) => s.id == d.requirementSlotId))
                              .toList();
                          return Padding(
                            padding: const EdgeInsets.only(bottom: 12),
                            child: DocumentSlotCard(
                              group: group,
                              uploadedDocuments: groupDocs,
                              dossierId: dossier.id,
                              dossierApi: widget.dossierApi,
                              onDocumentUploaded: _onDocumentUploaded,
                              onDocumentDeleted: _onDocumentDeleted,
                            ),
                          );
                        },
                        childCount: dossier.requirementGroups.length,
                      ),
                    ),
                  ),
                  const SliverToBoxAdapter(child: SizedBox(height: 80)),
                ],
              ),
            ),
      floatingActionButton: dossier.isDraft
          ? FloatingActionButton.extended(
              onPressed: _submitting ? null : _confirmAndSubmit,
              icon: _submitting
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : const Icon(Icons.send),
              label: Text(_submitting ? 'Đang nộp...' : 'Nộp hồ sơ'),
              backgroundColor: isComplete ? null : Colors.orange,
            )
          : null,
    );
  }

  Widget _buildCompletenessHeader(DossierCompletenessDto completeness, bool isComplete) {
    return Container(
      color: isComplete ? Colors.green.shade50 : Colors.orange.shade50,
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Icon(
            isComplete ? Icons.check_circle : Icons.warning_amber,
            color: isComplete ? Colors.green : Colors.orange,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: isComplete
                ? const Text('Hồ sơ đầy đủ, sẵn sàng nộp')
                : Text(
                    'Còn thiếu ${completeness.missingGroups.length} nhóm tài liệu bắt buộc',
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildSubmittedView(DossierDto dossier) {
    final statusColors = {
      'in_progress': Colors.blue,
      'completed': Colors.green,
      'rejected': Colors.red,
    };
    final statusLabels = {
      'in_progress': 'Đang xử lý',
      'completed': 'Hoàn thành',
      'rejected': 'Bị từ chối',
    };
    final color = statusColors[dossier.status] ?? Colors.grey;
    final label = statusLabels[dossier.status] ?? dossier.status;

    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.assignment, size: 64, color: color),
            const SizedBox(height: 16),
            Text(label, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold, color: color)),
            if (dossier.referenceNumber != null) ...[
              const SizedBox(height: 8),
              Text(dossier.referenceNumber!, style: const TextStyle(fontSize: 18)),
            ],
            if (dossier.rejectionReason != null) ...[
              const SizedBox(height: 16),
              Text('Lý do: ${dossier.rejectionReason}', textAlign: TextAlign.center),
            ],
          ],
        ),
      ),
    );
  }
}
