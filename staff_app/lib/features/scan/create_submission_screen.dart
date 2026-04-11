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

  final _classificationLabels = ['Unclassified', 'Confidential', 'Secret', 'Top Secret'];

  bool get _classificationExceedsClearance =>
      _securityClassification != null && _securityClassification! > widget.staffClearanceLevel;

  void _submit() {
    if (_cccdController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter citizen CCCD number')),
      );
      return;
    }
    if (_securityClassification == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a security classification')),
      );
      return;
    }
    if (_classificationExceedsClearance) {
      showDialog(
        context: context,
        builder: (ctx) => AlertDialog(
          title: const Text('Clearance Warning'),
          content: Text(
            'You are assigning classification "${_classificationLabels[_securityClassification!]}" '
            'which exceeds your clearance level '
            '"${_classificationLabels[widget.staffClearanceLevel]}". '
            'You will not be able to access this document after submission.',
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            TextButton(
              onPressed: () {
                Navigator.pop(ctx);
                _doSubmit();
              },
              child: const Text('Proceed Anyway'),
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
    return Scaffold(
      appBar: AppBar(title: const Text('New Submission')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _cccdController,
              decoration: const InputDecoration(
                labelText: 'Citizen CCCD Number',
                border: OutlineInputBorder(),
                hintText: 'Enter 12-digit CCCD number',
              ),
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 24),
            const Text('Security Classification *', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _securityClassification,
              decoration: InputDecoration(
                border: const OutlineInputBorder(),
                hintText: 'Select classification',
                errorText: _securityClassification == null ? null : null,
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
                        'This classification exceeds your clearance level '
                        '(${_classificationLabels[widget.staffClearanceLevel]})',
                        style: const TextStyle(color: Colors.orange, fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
            const SizedBox(height: 24),
            const Text('Priority', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'normal', label: Text('Normal')),
                ButtonSegment(value: 'urgent', label: Text('Urgent')),
              ],
              selected: {_priority},
              onSelectionChanged: (v) => setState(() => _priority = v.first),
            ),
            const Spacer(),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: _submit,
                child: const Text('Create & Start Scanning'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
