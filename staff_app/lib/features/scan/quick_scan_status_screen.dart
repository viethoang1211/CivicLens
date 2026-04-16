import 'dart:async';
import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

/// Shows real-time processing status after a quick scan is finalized.
/// Polls the backend for OCR → Classification progress and allows
/// staff to manually review/classify when AI is done or stuck.
class QuickScanStatusScreen extends StatefulWidget {
  final String submissionId;
  final String? dossierId;
  final StaffSubmissionsApi submissionsApi;
  final StaffClassificationApi classificationApi;

  const QuickScanStatusScreen({
    super.key,
    required this.submissionId,
    this.dossierId,
    required this.submissionsApi,
    required this.classificationApi,
  });

  @override
  State<QuickScanStatusScreen> createState() => _QuickScanStatusScreenState();
}

class _QuickScanStatusScreenState extends State<QuickScanStatusScreen> {
  Timer? _pollTimer;
  String _status = 'ocr_processing';
  double? _confidence;
  String? _classificationMethod;
  String? _error;
  Map<String, dynamic>? _classificationResult;
  bool _loadingClassification = false;

  static const _statusLabels = {
    'ocr_processing': 'Đang trích xuất văn bản (OCR)...',
    'classifying': 'Đang phân loại tài liệu (AI)...',
    'pending_classification': 'Phân loại xong — chờ xác nhận',
    'classified': 'Đã phân loại xong',
  };

  static const _statusIcons = {
    'ocr_processing': Icons.document_scanner_rounded,
    'classifying': Icons.auto_awesome,
    'pending_classification': Icons.fact_check_rounded,
    'classified': Icons.check_circle_rounded,
  };

  @override
  void initState() {
    super.initState();
    _startPolling();
  }

  @override
  void dispose() {
    _pollTimer?.cancel();
    super.dispose();
  }

  void _startPolling() {
    _poll(); // immediate first poll
    _pollTimer = Timer.periodic(const Duration(seconds: 3), (_) => _poll());
  }

  Future<void> _poll() async {
    try {
      final result = await widget.submissionsApi.getStatus(widget.submissionId);
      if (!mounted) return;

      final newStatus = result['status'] as String? ?? _status;
      setState(() {
        _status = newStatus;
        _confidence = result['classification_confidence'] != null
            ? (result['classification_confidence'] as num).toDouble()
            : null;
        _classificationMethod = result['classification_method'] as String?;
        _error = null;
      });

      // Keep polling through ocr_processing and classifying;
      // stop only when classification result is ready
      if (newStatus == 'pending_classification' || newStatus == 'classified') {
        _pollTimer?.cancel();
        _loadClassificationDetails();
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = 'Không thể kiểm tra trạng thái');
      }
    }
  }

  Future<void> _loadClassificationDetails() async {
    setState(() => _loadingClassification = true);
    try {
      final result = await widget.classificationApi.getClassification(widget.submissionId);
      if (mounted) {
        setState(() {
          _classificationResult = result;
          _loadingClassification = false;
        });
      }
    } catch (_) {
      if (mounted) setState(() => _loadingClassification = false);
    }
  }

  Future<void> _confirmClassification(String documentTypeId) async {
    try {
      await widget.classificationApi.confirmClassification(
        submissionId: widget.submissionId,
        documentTypeId: documentTypeId,
      );
      if (mounted) {
        setState(() => _status = 'classified');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Đã xác nhận phân loại'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final isProcessing = _status == 'ocr_processing' || _status == 'classifying';
    final isPendingReview = _status == 'pending_classification';
    final isDone = _status == 'classified';

    return Scaffold(
      appBar: AppBar(title: const Text('Trạng thái xử lý')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          // ── Status indicator ──
          Center(
            child: Column(
              children: [
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: (isDone ? Colors.green : isProcessing ? Colors.blue : Colors.orange)
                        .withAlpha(25),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    _statusIcons[_status] ?? Icons.hourglass_top,
                    size: 48,
                    color: isDone ? Colors.green : isProcessing ? Colors.blue : Colors.orange,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  _statusLabels[_status] ?? _status,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
                  textAlign: TextAlign.center,
                ),
                if (isProcessing) ...[
                  const SizedBox(height: 16),
                  const SizedBox(
                    width: 200,
                    child: LinearProgressIndicator(),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    _status == 'classifying'
                        ? 'AI đang phân tích hình ảnh và nội dung...'
                        : 'Vui lòng chờ trong giây lát...',
                    style: TextStyle(color: cs.onSurface.withAlpha(150), fontSize: 13),
                  ),
                ],
              ],
            ),
          ),

          if (_error != null) ...[
            const SizedBox(height: 16),
            Card(
              color: Colors.red.shade50,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: Colors.red),
                    const SizedBox(width: 8),
                    Expanded(child: Text(_error!, style: const TextStyle(color: Colors.red))),
                    TextButton(onPressed: _poll, child: const Text('Thử lại')),
                  ],
                ),
              ),
            ),
          ],

          // ── Classification result ──
          if (isPendingReview || isDone) ...[
            const SizedBox(height: 24),
            const Divider(),
            const SizedBox(height: 16),
            Text(
              'Kết quả AI',
              style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w700),
            ),
            const SizedBox(height: 12),

            if (_loadingClassification)
              const Center(child: CircularProgressIndicator())
            else if (_classificationResult != null) ...[
              _buildCitizenCheckWarning(cs),
              _buildClassificationCard(cs),
              if (isPendingReview) ...[
                const SizedBox(height: 24),
                _buildActionButtons(cs),
              ],
            ] else if (_confidence != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Độ tin cậy: ${(_confidence! * 100).toStringAsFixed(0)}%'),
                      if (_classificationMethod != null)
                        Text('Phương pháp: $_classificationMethod'),
                    ],
                  ),
                ),
              ),
            ],
          ],

          if (isDone) ...[
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: FilledButton.icon(
                onPressed: () => Navigator.of(context).pop(),
                icon: const Icon(Icons.home),
                label: const Text('Về trang chủ'),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildCitizenCheckWarning(ColorScheme cs) {
    final citizenCheck = _classificationResult!['citizen_check'] as Map<String, dynamic>? ?? {};
    final warning = citizenCheck['missing_cccd_warning'] as String?;
    final isIdDocument = citizenCheck['is_id_document'] as bool? ?? false;
    final citizenIdentified = citizenCheck['citizen_identified'] as bool? ?? false;

    if (warning == null || isIdDocument || citizenIdentified) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Card(
        color: Colors.amber.shade50,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(color: Colors.amber.shade300),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(Icons.credit_card_off, color: Colors.amber.shade800, size: 28),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Thiếu ảnh CCCD',
                      style: TextStyle(
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                        color: Colors.amber.shade900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      warning,
                      style: TextStyle(fontSize: 13, color: Colors.amber.shade900),
                    ),
                    const SizedBox(height: 8),
                    OutlinedButton.icon(
                      onPressed: () => Navigator.of(context).pop('scan_cccd'),
                      icon: const Icon(Icons.camera_alt, size: 18),
                      label: const Text('Quét CCCD ngay'),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.amber.shade900,
                        side: BorderSide(color: Colors.amber.shade600),
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildClassificationCard(ColorScheme cs) {
    final classification = _classificationResult!['classification'] as Map<String, dynamic>? ?? {};
    final docTypeName = classification['document_type_name'] as String?;
    final confidence = classification['confidence'] as num?;
    final method = classification['method'] as String?;
    final alternatives = classification['alternatives'] as List<dynamic>? ?? [];
    final aiSummary = _classificationResult!['ai_summary'] as String?;
    final aiReasoning = _classificationResult!['ai_reasoning'] as Map<String, dynamic>? ?? {};

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (docTypeName != null) ...[
              Row(
                children: [
                  Icon(Icons.description, color: cs.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      docTypeName,
                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
            ] else ...[
              Row(
                children: [
                  const Icon(Icons.help_outline, color: Colors.orange),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'Không nhận dạng được loại tài liệu',
                      style: TextStyle(fontWeight: FontWeight.w600, fontSize: 16, color: Colors.orange),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
            ],
            if (confidence != null) ...[
              LinearProgressIndicator(
                value: confidence.toDouble(),
                backgroundColor: cs.surfaceContainerHighest,
                color: confidence > 0.8 ? Colors.green : confidence > 0.5 ? Colors.orange : Colors.red,
              ),
              const SizedBox(height: 4),
              Row(
                children: [
                  Text(
                    'Độ tin cậy: ${(confidence * 100).toStringAsFixed(0)}%',
                    style: TextStyle(fontSize: 13, color: cs.onSurface.withAlpha(150)),
                  ),
                  if (method != null) ...[
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: method.contains('agree') ? Colors.green.withAlpha(25) : Colors.orange.withAlpha(25),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        method == 'ensemble_agree' ? 'AI đồng thuận' :
                        method == 'ensemble_disagree' ? 'AI không đồng thuận' :
                        method == 'vision_only' ? 'Chỉ hình ảnh' :
                        method == 'text_only' ? 'Chỉ nội dung' : method,
                        style: TextStyle(
                          fontSize: 11,
                          color: method.contains('agree') ? Colors.green.shade700 : Colors.orange.shade700,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ],
            // ── AI reasoning ──
            if (aiReasoning['explanation'] != null) ...[
              const SizedBox(height: 12),
              Text(
                'Lý do phân loại:',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: cs.onSurface.withAlpha(180)),
              ),
              const SizedBox(height: 4),
              Text(
                aiReasoning['explanation'] as String,
                style: const TextStyle(fontSize: 13),
              ),
            ],
            if ((aiReasoning['visual_features'] as List?)?.isNotEmpty ?? false) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 4,
                runSpacing: 4,
                children: [
                  Icon(Icons.visibility, size: 14, color: cs.primary),
                  const SizedBox(width: 2),
                  ...(aiReasoning['visual_features'] as List).map((f) => Chip(
                    label: Text(f.toString(), style: const TextStyle(fontSize: 11)),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                    padding: EdgeInsets.zero,
                  )),
                ],
              ),
            ],
            if ((aiReasoning['key_signals'] as List?)?.isNotEmpty ?? false) ...[
              const SizedBox(height: 8),
              Wrap(
                spacing: 4,
                runSpacing: 4,
                children: [
                  Icon(Icons.text_snippet, size: 14, color: cs.secondary),
                  const SizedBox(width: 2),
                  ...(aiReasoning['key_signals'] as List).map((s) => Chip(
                    label: Text(s.toString(), style: const TextStyle(fontSize: 11)),
                    materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    visualDensity: VisualDensity.compact,
                    padding: EdgeInsets.zero,
                  )),
                ],
              ),
            ],
            if (aiSummary != null) ...[
              const SizedBox(height: 12),
              Text(
                'Tóm tắt AI:',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: cs.onSurface.withAlpha(180)),
              ),
              const SizedBox(height: 4),
              Text(aiSummary, style: const TextStyle(fontSize: 13)),
            ],
            if (alternatives.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(
                'Gợi ý khác:',
                style: TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: cs.onSurface.withAlpha(180)),
              ),
              const SizedBox(height: 4),
              ...alternatives.map((alt) {
                final altMap = alt as Map<String, dynamic>;
                return ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  title: Text(altMap['name'] as String? ?? 'Không rõ'),
                  trailing: TextButton(
                    onPressed: () => _confirmClassification(altMap['document_type_id'] as String),
                    child: const Text('Chọn'),
                  ),
                );
              }),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildActionButtons(ColorScheme cs) {
    final classification = _classificationResult!['classification'] as Map<String, dynamic>? ?? {};
    final docTypeId = classification['document_type_id'] as String?;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        if (docTypeId != null)
          FilledButton.icon(
            onPressed: () => _confirmClassification(docTypeId),
            icon: const Icon(Icons.check),
            label: const Text('Xác nhận phân loại'),
            style: FilledButton.styleFrom(
              minimumSize: const Size.fromHeight(48),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
          ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: () => Navigator.of(context).pop(),
          icon: const Icon(Icons.skip_next),
          label: const Text('Bỏ qua, xử lý sau'),
          style: OutlinedButton.styleFrom(
            minimumSize: const Size.fromHeight(48),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          ),
        ),
      ],
    );
  }
}
