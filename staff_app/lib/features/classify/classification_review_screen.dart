import 'package:flutter/material.dart';

class ClassificationReviewScreen extends StatefulWidget {
  final String submissionId;
  final Map<String, dynamic> classificationData;

  const ClassificationReviewScreen({
    super.key,
    required this.submissionId,
    required this.classificationData,
  });

  @override
  State<ClassificationReviewScreen> createState() => _ClassificationReviewScreenState();
}

class _ClassificationReviewScreenState extends State<ClassificationReviewScreen> {
  late String? _selectedTypeId;
  late double _confidence;
  late Map<String, dynamic> _templateData;

  @override
  void initState() {
    super.initState();
    final classification = widget.classificationData['classification'] ?? {};
    _selectedTypeId = classification['document_type_id'];
    _confidence = (classification['confidence'] ?? 0).toDouble();
    _templateData = Map<String, dynamic>.from(widget.classificationData['template_data'] ?? {});
  }

  void _confirm() {
    Navigator.of(context).pop({
      'document_type_id': _selectedTypeId,
      'template_data': _templateData,
      'classification_method': 'ai_confirmed',
    });
  }

  void _manualClassify() async {
    final result = await Navigator.of(context).pushNamed('/manual-classify');
    if (result != null && result is Map<String, dynamic>) {
      setState(() {
        _selectedTypeId = result['document_type_id'];
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final classification = widget.classificationData['classification'] ?? {};
    final alternatives = (classification['alternatives'] as List?) ?? [];

    return Scaffold(
      appBar: AppBar(title: const Text('Classification Review')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Classification result
            Card(
              child: ListTile(
                title: Text(classification['document_type_name'] ?? 'Unknown'),
                subtitle: Text('Confidence: ${(_confidence * 100).toStringAsFixed(0)}%'),
                leading: Icon(
                  _confidence >= 0.7 ? Icons.check_circle : Icons.warning,
                  color: _confidence >= 0.7 ? Colors.green : Colors.orange,
                ),
              ),
            ),

            // Alternatives
            if (alternatives.isNotEmpty) ...[
              const SizedBox(height: 16),
              const Text('Alternatives:', style: TextStyle(fontWeight: FontWeight.bold)),
              ...alternatives.map((alt) => ListTile(
                    title: Text(alt['name'] ?? ''),
                    subtitle: Text('Confidence: ${((alt['confidence'] ?? 0) * 100).toStringAsFixed(0)}%'),
                    onTap: () => setState(() => _selectedTypeId = alt['document_type_id']),
                  )),
            ],

            const Divider(height: 32),

            // Template data
            const Text('Extracted Data:', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ..._templateData.entries.map((entry) => Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: TextFormField(
                    initialValue: entry.value?.toString() ?? '',
                    decoration: InputDecoration(
                      labelText: entry.key,
                      border: const OutlineInputBorder(),
                    ),
                    onChanged: (v) => _templateData[entry.key] = v,
                  ),
                )),

            const SizedBox(height: 24),
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _manualClassify,
                    child: const Text('Manual Classify'),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _confirm,
                    child: const Text('Confirm'),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
