import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

// Keys from template_data that are internal metadata — never shown to staff
const _hiddenPrefixes = ['_'];
const _hiddenKeys = {'type', 'required', 'properties', '\$schema', '\$defs'};

// Vietnamese display names for common OCR-extracted fields
const _fieldLabels = {
  'ho_ten': 'Họ và tên',
  'so_cccd': 'Số CCCD/CMND',
  'ngay_sinh': 'Ngày sinh',
  'gioi_tinh': 'Giới tính',
  'quoc_tich': 'Quốc tịch',
  'que_quan': 'Quê quán',
  'noi_thuong_tru': 'Nơi thường trú',
  'ngay_cap': 'Ngày cấp',
  'noi_cap': 'Nơi cấp',
  'ngay_het_han': 'Ngày hết hạn',
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

  @override
  void initState() {
    super.initState();
    _loadDetail();
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
    final stepStatus = step['status'] as String? ?? '';
    final isActive = stepStatus == 'active';

    // Only show real extracted fields — filter out schema structure and internal _ metadata
    final displayFields = templateData?.entries
        .where((e) => _shouldShowKey(e.key) && e.value != null && e.value.toString().trim().isNotEmpty)
        .toList() ?? [];

    return Stack(children: [
      SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 120),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [

          // ── Step header ─────────────────────────────────────
          _buildStepHeader(step, submission),
          const SizedBox(height: 16),

          // ── Extracted OCR fields ─────────────────────────────
          _sectionTitle('Thông tin trích xuất từ OCR'),
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
                          child: Text(_labelFor(e.key),
                              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13, color: Colors.black87)),
                        ),
                        Expanded(child: Text('${e.value}', style: const TextStyle(fontSize: 13))),
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
                          label: Text('OCR ${((page['ocr_confidence'] as num) * 100).toStringAsFixed(0)}%',
                              style: const TextStyle(fontSize: 11)),
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
