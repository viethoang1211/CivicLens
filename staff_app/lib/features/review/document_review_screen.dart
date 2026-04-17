import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

// Keys from template_data that are internal metadata — never shown to staff
const _hiddenPrefixes = ['_'];
const _hiddenKeys = {'type', 'required', 'properties', '\$schema', '\$defs'};

// Vietnamese display names for common OCR-extracted fields
const _fieldLabels = {
  'ho_ten': 'Họ và tên',
  'full_name': 'Họ và tên',
  'so_cccd': 'Số CCCD/CMND',
  'id_number': 'Số CCCD/CMND',
  'ngay_sinh': 'Ngày sinh',
  'date_of_birth': 'Ngày sinh',
  'gioi_tinh': 'Giới tính',
  'sex': 'Giới tính',
  'quoc_tich': 'Quốc tịch',
  'nationality': 'Quốc tịch',
  'que_quan': 'Quê quán',
  'place_of_origin': 'Quê quán',
  'noi_thuong_tru': 'Nơi thường trú',
  'place_of_residence': 'Nơi thường trú',
  'ngay_cap': 'Ngày cấp',
  'noi_cap': 'Nơi cấp',
  'ngay_het_han': 'Ngày hết hạn',
  'date_of_expiry': 'Ngày hết hạn',
  'ho_ten_cha': 'Họ tên cha',
  'ho_ten_me': 'Họ tên mẹ',
  'ten_tre': 'Tên trẻ',
  'ngay_khai_sinh': 'Ngày khai sinh',
  'noi_khai_sinh': 'Nơi đăng ký khai sinh',
  'so_dang_ky': 'Số đăng ký',
  'quyen_so': 'Quyển số',
  'so_to_khai': 'Số tờ khai',
  'ten': 'Tên',
  'dia_chi': 'Địa chỉ',
  'so_ho_chieu': 'Số hộ chiếu',
  'ai_summary': 'Tóm tắt AI',
};

bool _shouldShowKey(String key) {
  if (_hiddenPrefixes.any((p) => key.startsWith(p))) return false;
  if (_hiddenKeys.contains(key)) return false;
  return true;
}

String _labelFor(String key) => _fieldLabels[key] ?? key.replaceAll('_', ' ');

class DocumentReviewScreen extends StatefulWidget {
  final ApiClient apiClient;
  final String stepId;

  const DocumentReviewScreen({
    super.key,
    required this.apiClient,
    required this.stepId,
  });

  @override
  State<DocumentReviewScreen> createState() => _DocumentReviewScreenState();
}

class _DocumentReviewScreenState extends State<DocumentReviewScreen> {
  Map<String, dynamic>? _data;
  bool _loading = true;
  String? _error;
  bool _submitting = false;
  bool _editingTemplate = false;
  Map<String, TextEditingController> _editControllers = {};

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  @override
  void dispose() {
    for (final c in _editControllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  void _startEditing(List<MapEntry<String, dynamic>> fields) {
    _editControllers = {
      for (final e in fields) e.key: TextEditingController(text: '${e.value}'),
    };
    setState(() => _editingTemplate = true);
  }

  Future<void> _saveTemplateEdits() async {
    final submissionId = (_data?['submission'] as Map?)?['id'] as String?;
    if (submissionId == null) return;

    final changes = <String, dynamic>{};
    for (final entry in _editControllers.entries) {
      changes[entry.key] = entry.value.text;
    }

    setState(() => _submitting = true);
    try {
      await widget.apiClient.patch(
        '/v1/staff/submissions/$submissionId/template-data',
        data: {'template_data': changes},
      );
      setState(() => _editingTemplate = false);
      await _loadDetail(); // Reload fresh data
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã lưu chỉnh sửa'), backgroundColor: Colors.green),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi: $e'), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  Future<void> _loadDetail() async {
    setState(() { _loading = true; _error = null; });
    try {
      final resp = await widget.apiClient.get('/v1/staff/workflow-steps/${widget.stepId}');
      setState(() { _data = resp.data as Map<String, dynamic>; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _submitDecision(String result, String comment, bool targetCitizen) async {
    setState(() => _submitting = true);
    try {
      await widget.apiClient.post(
        '/v1/staff/workflow-steps/${widget.stepId}/complete',
        data: {'result': result, 'comment': comment, 'target_citizen': targetCitizen},
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(_resultSuccessMsg(result)),
          backgroundColor: result == 'approved' ? Colors.green : Colors.orange,
        ));
        Navigator.of(context).pop(true);
      }
    } catch (e) {
      if (mounted) {
        setState(() => _submitting = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  String _resultSuccessMsg(String result) => switch (result) {
    'approved' => 'Đã phê duyệt hồ sơ',
    'rejected' => 'Đã từ chối hồ sơ',
    'needs_info' => 'Đã yêu cầu bổ sung thông tin',
    _ => 'Đã gửi quyết định',
  };

  void _showDecisionSheet(String result) {
    final commentCtrl = TextEditingController();
    bool targetCitizen = result == 'needs_info';
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(16))),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setModal) => Padding(
          padding: EdgeInsets.only(
            left: 16, right: 16, top: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(_resultTitle(result),
                  style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              TextField(
                controller: commentCtrl,
                maxLines: 3,
                decoration: InputDecoration(
                  labelText: 'Ghi chú',
                  hintText: _resultHint(result),
                  border: const OutlineInputBorder(),
                ),
              ),
              if (result == 'needs_info') ...[
                const SizedBox(height: 12),
                StatefulBuilder(builder: (_, setCheck) => CheckboxListTile(
                  value: targetCitizen,
                  onChanged: (v) => setCheck(() => targetCitizen = v ?? false),
                  title: const Text('Thông báo tới công dân'),
                  contentPadding: EdgeInsets.zero,
                )),
              ],
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _resultColor(result),
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  onPressed: () {
                    Navigator.of(ctx).pop();
                    _submitDecision(result, commentCtrl.text, targetCitizen);
                  },
                  child: Text(_resultTitle(result)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _resultTitle(String result) => switch (result) {
    'approved' => 'Phê duyệt',
    'rejected' => 'Từ chối',
    'needs_info' => 'Yêu cầu bổ sung',
    _ => result,
  };

  String _resultHint(String result) => switch (result) {
    'approved' => 'Nhận xét (không bắt buộc)',
    'rejected' => 'Lý do từ chối...',
    'needs_info' => 'Thông tin cần bổ sung...',
    _ => '',
  };

  Color _resultColor(String result) => switch (result) {
    'approved' => Colors.green,
    'rejected' => Colors.red,
    'needs_info' => Colors.orange,
    _ => Colors.blue,
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Xem xét hồ sơ')),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.error_outline, size: 48, color: Colors.red),
        const SizedBox(height: 12),
        Text('Lỗi: $_error', textAlign: TextAlign.center),
        const SizedBox(height: 12),
        ElevatedButton.icon(onPressed: _loadDetail, icon: const Icon(Icons.refresh), label: const Text('Thử lại')),
      ]));
    }

    final data = _data!;
    final step = data['step'] as Map<String, dynamic>? ?? {};
    final pages = (data['pages'] as List?) ?? [];
    final annotations = (data['annotations_by_department'] as Map?) ?? {};
    final submission = data['submission'] as Map<String, dynamic>? ?? {};
    final templateData = submission['template_data'] as Map<String, dynamic>?;
    final templateSchema = submission['template_schema'] as Map<String, dynamic>?;
    final stepStatus = step['status'] as String? ?? '';
    final isActive = stepStatus == 'active';

    // Build display fields using template_schema from document type (authoritative source)
    final displayFields = <MapEntry<String, dynamic>>[];
    final schemaTitles = <String, String>{};
    if (templateData != null) {
      // Collect flat extracted values
      final flatValues = <String, dynamic>{};
      for (final e in templateData.entries) {
        if (_shouldShowKey(e.key) && e.value != null && e.value is! Map && e.value is! List) {
          flatValues[e.key] = e.value;
        }
      }

      // Use template_schema.properties from document_type (preferred),
      // fall back to template_data.properties (legacy)
      final schemaProps = (templateSchema?['properties'] as Map<String, dynamic>?)
          ?? (templateData['properties'] as Map<String, dynamic>?);

      if (schemaProps != null) {
        for (final entry in schemaProps.entries) {
          final key = entry.key;
          final spec = entry.value;
          if (spec is Map && spec['title'] != null) {
            schemaTitles[key] = spec['title'] as String;
          }
          // Value from extracted data
          final value = flatValues.remove(key) ?? templateData[key];
          displayFields.add(MapEntry(key, (value is Map || value is List) ? '' : (value ?? '')));
        }
      }

      // Add remaining flat values not in schema
      for (final e in flatValues.entries) {
        if (e.value.toString().trim().isNotEmpty) {
          displayFields.add(e);
        }
      }
    }

    // Label resolver: schema title > static labels > formatted key
    String labelFor(String key) => schemaTitles[key] ?? _fieldLabels[key] ?? key.replaceAll('_', ' ');

    return Stack(children: [
      SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 120),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [

          // ── Step header ─────────────────────────────────────
          _buildStepHeader(step, submission),
          const SizedBox(height: 16),

          // ── Extracted OCR fields ─────────────────────────────
          Row(
            children: [
              Expanded(child: _sectionTitle('Thông tin trích xuất từ OCR')),
              if (isActive && displayFields.isNotEmpty && !_editingTemplate)
                TextButton.icon(
                  onPressed: () => _startEditing(displayFields),
                  icon: const Icon(Icons.edit, size: 16),
                  label: const Text('Chỉnh sửa'),
                ),
              if (_editingTemplate) ...[
                TextButton(
                  onPressed: () => setState(() => _editingTemplate = false),
                  child: const Text('Hủy'),
                ),
                const SizedBox(width: 4),
                FilledButton.icon(
                  onPressed: _submitting ? null : _saveTemplateEdits,
                  icon: const Icon(Icons.save, size: 16),
                  label: const Text('Lưu'),
                ),
              ],
            ],
          ),
          const SizedBox(height: 8),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(12),
              child: displayFields.isEmpty
                  ? const Text('Chưa có dữ liệu trích xuất.', style: TextStyle(color: Colors.grey))
                  : Column(children: displayFields.map((e) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 6),
                      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                        SizedBox(
                          width: 140,
                          child: Text(labelFor(e.key),
                              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: Colors.black87)),
                        ),
                        Expanded(
                          child: _editingTemplate && _editControllers.containsKey(e.key)
                              ? TextField(
                                  controller: _editControllers[e.key],
                                  style: const TextStyle(fontSize: 13),
                                  decoration: InputDecoration(
                                    isDense: true,
                                    hintText: 'Nhập ${labelFor(e.key).toLowerCase()}',
                                    contentPadding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(4)),
                                  ),
                                )
                              : Text(
                                  e.value.toString().isEmpty ? 'Chưa có' : '${e.value}',
                                  style: TextStyle(
                                    fontSize: 13,
                                    color: e.value.toString().isEmpty ? Colors.grey : null,
                                    fontStyle: e.value.toString().isEmpty ? FontStyle.italic : null,
                                  ),
                                ),
                        ),
                      ]),
                    )).toList()),
            ),
          ),
          const SizedBox(height: 16),

          // ── Scanned pages ────────────────────────────────────
          _sectionTitle('Ảnh tài liệu đã quét (${pages.length} trang)'),
          const SizedBox(height: 8),
          ...pages.map<Widget>((p) {
            final page = p as Map<String, dynamic>;
            return Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                if (page['image_url'] != null)
                  ClipRRect(
                    borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                    child: Image.network(page['image_url'] as String,
                        width: double.infinity, fit: BoxFit.contain,
                        errorBuilder: (_, __, ___) => const Padding(
                          padding: EdgeInsets.all(16),
                          child: Icon(Icons.broken_image, size: 48, color: Colors.grey),
                        )),
                  ),
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Row(children: [
                      const Icon(Icons.description_outlined, size: 16, color: Colors.grey),
                      const SizedBox(width: 4),
                      Text('Trang ${page['page_number']}', style: const TextStyle(fontWeight: FontWeight.w600)),
                      if (page['ocr_confidence'] != null) ...[
                        const SizedBox(width: 8),
                        Chip(
                          label: Text('Độ tin cậy: ${((page['ocr_confidence'] as num) * 100).toStringAsFixed(0)}%',
                              style: const TextStyle(fontSize: 11)),
                          avatar: Icon(
                            ((page['ocr_confidence'] as num) >= 0.8) ? Icons.check_circle : Icons.warning_amber,
                            size: 14,
                            color: ((page['ocr_confidence'] as num) >= 0.8) ? Colors.green : Colors.orange,
                          ),
                          padding: EdgeInsets.zero, visualDensity: VisualDensity.compact,
                        ),
                      ],
                    ]),
                    if (page['ocr_text'] != null && (page['ocr_text'] as String).isNotEmpty) ...[
                      const SizedBox(height: 8),
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(4)),
                        child: Text(page['ocr_text'] as String, style: const TextStyle(fontSize: 12)),
                      ),
                    ],
                  ]),
                ),
              ]),
            );
          }),

          // ── Prior annotations ────────────────────────────────
          if (annotations.isNotEmpty) ...[
            const SizedBox(height: 8),
            _sectionTitle('Nhận xét từ các phòng ban'),
            const SizedBox(height: 8),
            ...(annotations as Map<String, dynamic>).entries.map<Widget>((entry) {
              final items = entry.value as List;
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    Text(entry.key, style: const TextStyle(fontWeight: FontWeight.w600)),
                    const Divider(),
                    ...items.map<Widget>((a) {
                      final ann = a as Map<String, dynamic>;
                      return Padding(
                        padding: const EdgeInsets.symmetric(vertical: 4),
                        child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          _annotationChip(ann['type'] as String? ?? ''),
                          const SizedBox(width: 8),
                          Expanded(child: Text(ann['content'] as String? ?? '')),
                        ]),
                      );
                    }),
                  ]),
                ),
              );
            }),
          ],
        ]),
      ),

      // ── Action bar ──────────────────────────────────────────
      Positioned(
        bottom: 0, left: 0, right: 0,
        child: Container(
          decoration: BoxDecoration(
            color: Theme.of(context).scaffoldBackgroundColor,
            boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 8, offset: const Offset(0, -2))],
          ),
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
          child: _submitting
              ? const Center(child: CircularProgressIndicator())
              : isActive
                  ? Row(children: [
                      Expanded(child: OutlinedButton.icon(
                        onPressed: () => _showDecisionSheet('rejected'),
                        icon: const Icon(Icons.cancel_outlined, color: Colors.red),
                        label: const Text('Từ chối', style: TextStyle(color: Colors.red)),
                        style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.red), padding: const EdgeInsets.symmetric(vertical: 12)),
                      )),
                      const SizedBox(width: 8),
                      Expanded(child: OutlinedButton.icon(
                        onPressed: () => _showDecisionSheet('needs_info'),
                        icon: const Icon(Icons.help_outline, color: Colors.orange),
                        label: const Text('Bổ sung', style: TextStyle(color: Colors.orange)),
                        style: OutlinedButton.styleFrom(side: const BorderSide(color: Colors.orange), padding: const EdgeInsets.symmetric(vertical: 12)),
                      )),
                      const SizedBox(width: 8),
                      Expanded(child: ElevatedButton.icon(
                        onPressed: () => _showDecisionSheet('approved'),
                        icon: const Icon(Icons.check_circle_outline),
                        label: const Text('Phê duyệt'),
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.green, foregroundColor: Colors.white, padding: const EdgeInsets.symmetric(vertical: 12)),
                      )),
                    ])
                  : Row(children: [
                      Icon(
                        stepStatus == 'completed' || stepStatus == 'approved' ? Icons.check_circle : Icons.info_outline,
                        color: stepStatus == 'completed' || stepStatus == 'approved' ? Colors.green : Colors.grey,
                      ),
                      const SizedBox(width: 8),
                      Text(switch (stepStatus) {
                        'completed' || 'approved' => 'Bước này đã được phê duyệt',
                        'rejected' => 'Bước này đã bị từ chối',
                        'pending' => 'Đang chờ xử lý',
                        _ => 'Trạng thái: $stepStatus',
                      }, style: TextStyle(
                        color: stepStatus == 'completed' || stepStatus == 'approved' ? Colors.green : Colors.grey.shade700,
                        fontWeight: FontWeight.w500,
                      )),
                    ]),
        ),
      ),
    ]);
  }

  Widget _buildStepHeader(Map<String, dynamic> step, Map<String, dynamic> submission) {
    final deptName = step['department_name'] as String? ?? 'Phòng ban';
    final status = step['status'] as String? ?? '';
    final docType = submission['document_type_name'] as String?;
    return Card(
      color: Theme.of(context).colorScheme.primaryContainer.withOpacity(0.3),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Row(children: [
            const Icon(Icons.account_balance_outlined, size: 18),
            const SizedBox(width: 6),
            Expanded(child: Text(deptName, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15))),
            _statusChip(status),
          ]),
          if (docType != null && docType.isNotEmpty) ...[
            const SizedBox(height: 6),
            Row(children: [
              const Icon(Icons.description_outlined, size: 16, color: Colors.grey),
              const SizedBox(width: 6),
              Text(docType, style: const TextStyle(fontSize: 13, color: Colors.black87)),
            ]),
          ],
        ]),
      ),
    );
  }

  Widget _statusChip(String status) {
    final (label, color) = switch (status) {
      'active' => ('Đang xử lý', Colors.blue),
      'completed' || 'approved' => ('Hoàn thành', Colors.green),
      'rejected' => ('Từ chối', Colors.red),
      'pending' => ('Chờ xử lý', Colors.grey),
      _ => (status, Colors.grey),
    };
    return Chip(
      label: Text(label, style: const TextStyle(color: Colors.white, fontSize: 11)),
      backgroundColor: color, padding: EdgeInsets.zero, visualDensity: VisualDensity.compact,
    );
  }

  Widget _annotationChip(String type) {
    final (label, color) = switch (type) {
      'approved' => ('Duyệt', Colors.green),
      'rejected' => ('Từ chối', Colors.red),
      'needs_info' => ('Bổ sung', Colors.orange),
      'consultation' => ('Tham vấn', Colors.blue),
      _ => (type, Colors.grey),
    };
    return Chip(
      label: Text(label, style: const TextStyle(color: Colors.white, fontSize: 11)),
      backgroundColor: color, padding: EdgeInsets.zero, visualDensity: VisualDensity.compact,
    );
  }

  Widget _sectionTitle(String title) =>
      Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold));
}
