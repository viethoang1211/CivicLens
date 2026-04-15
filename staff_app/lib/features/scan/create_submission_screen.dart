import 'package:flutter/material.dart';

class CreateSubmissionScreen extends StatefulWidget {
  /// Staff member's clearance level (0-3). Used to validate classification selection.
  final int staffClearanceLevel;

  const CreateSubmissionScreen({super.key, this.staffClearanceLevel = 0});

  @override
  State<CreateSubmissionScreen> createState() => _CreateSubmissionScreenState();
}

class _CreateSubmissionScreenState extends State<CreateSubmissionScreen> {
  final _cccdController = TextEditingController();
  int? _securityClassification;
  String _priority = 'normal';

  final _classificationLabels = ['Công khai', 'Mật', 'Tối mật', 'Tuyệt mật'];

  bool get _classificationExceedsClearance =>
      _securityClassification != null && _securityClassification! > widget.staffClearanceLevel;

  void _submit() {
    if (_cccdController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vui lòng nhập số CCCD')),
      );
      return;
    }
    if (_securityClassification == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Vui lòng chọn mức độ bảo mật')),
      );
      return;
    }
    if (_classificationExceedsClearance) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Cảnh báo quyền truy cập'),
          content: Text(
            'Mức bảo mật "${_classificationLabels[_securityClassification!]}" '
            'vượt quá quyền hạn của bạn '
            '"${_classificationLabels[widget.staffClearanceLevel]}". '
            'Bạn sẽ không thể truy cập tài liệu này sau khi tải lên.',
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Huỷ')),
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                _doSubmit();
              },
              child: const Text('Tiếp tục'),
            ),
          ],
        ),
      );
      return;
    }
    _doSubmit();
  }

  void _doSubmit() {
    Navigator.of(context).pop({
      'citizen_id_number': _cccdController.text.trim(),
      'security_classification': _securityClassification,
      'priority': _priority,
    });
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(title: const Text('Quét nhanh')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _cccdController,
              decoration: InputDecoration(
                labelText: 'Số CCCD công dân',
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                hintText: 'Nhập số CCCD 12 chữ số',
                prefixIcon: const Icon(Icons.credit_card),
                filled: true,
                fillColor: cs.surfaceContainerHighest.withAlpha(80),
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 24),
            Text('Mức độ bảo mật *', style: TextStyle(fontWeight: FontWeight.w600, color: cs.onSurface)),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _securityClassification,
              decoration: InputDecoration(
                border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
                hintText: 'Chọn mức bảo mật',
                filled: true,
                fillColor: cs.surfaceContainerHighest.withAlpha(80),
              ),
              items: List.generate(4, (i) => DropdownMenuItem(value: i, child: Text(_classificationLabels[i]))),
              onChanged: (v) => setState(() => _securityClassification = v),
            ),
            if (_classificationExceedsClearance)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Row(
                  children: [
                    const Icon(Icons.warning_amber, color: Colors.orange, size: 18),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        'Mức bảo mật này vượt quá quyền hạn của bạn '
                        '(${_classificationLabels[widget.staffClearanceLevel]})',
                        style: const TextStyle(color: Colors.orange, fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 24),
            Text('Mức ưu tiên', style: TextStyle(fontWeight: FontWeight.w600, color: cs.onSurface)),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'normal', label: Text('Bình thường')),
                ButtonSegment(value: 'urgent', label: Text('Khẩn cấp')),
              ],
              selected: {_priority},
              onSelectionChanged: (v) => setState(() => _priority = v.first),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              height: 50,
              child: FilledButton.icon(
                onPressed: _submit,
                icon: const Icon(Icons.document_scanner_rounded),
                label: const Text('Tạo & Bắt đầu quét', style: TextStyle(fontSize: 16)),
                style: FilledButton.styleFrom(
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
