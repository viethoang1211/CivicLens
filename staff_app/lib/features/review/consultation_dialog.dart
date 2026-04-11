import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

class ConsultationDialog extends StatefulWidget {
  final ApiClient apiClient;
  final String stepId;
  final List<Map<String, dynamic>> departments;

  const ConsultationDialog({
    super.key,
    required this.apiClient,
    required this.stepId,
    required this.departments,
  });

  @override
  State<ConsultationDialog> createState() => _ConsultationDialogState();
}

class _ConsultationDialogState extends State<ConsultationDialog> {
  String? _selectedDeptId;
  final _questionController = TextEditingController();
  bool _submitting = false;

  Future<void> _submit() async {
    if (_selectedDeptId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Select a department')),
      );
      return;
    }
    final question = _questionController.text.trim();
    if (question.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Enter a question')),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      await widget.apiClient.post(
        '/v1/staff/workflow-steps/${widget.stepId}/consultations',
        data: {
          'target_department_id': _selectedDeptId,
          'question': question,
        },
      );
      if (mounted) Navigator.of(context).pop(true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  void dispose() {
    _questionController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Cross-Department Consultation'),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          DropdownButtonFormField<String>(
            decoration: const InputDecoration(
              labelText: 'Target Department',
              border: OutlineInputBorder(),
            ),
            items: widget.departments.map((d) => DropdownMenuItem(
              value: d['id'] as String,
              child: Text(d['name'] as String),
            )).toList(),
            onChanged: (v) => setState(() => _selectedDeptId = v),
            value: _selectedDeptId,
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _questionController,
            decoration: const InputDecoration(
              labelText: 'Question',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
          ),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(false),
          child: const Text('Cancel'),
        ),
        if (_submitting)
          const Padding(
            padding: EdgeInsets.all(8),
            child: SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2)),
          )
        else
          ElevatedButton(
            onPressed: _submit,
            child: const Text('Send'),
          ),
      ],
    );
  }
}
