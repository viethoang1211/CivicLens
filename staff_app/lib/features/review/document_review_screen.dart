import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

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

  @override
  void initState() {
    super.initState();
    _loadDetail();
  }

  Future<void> _loadDetail() async {
    setState(() { _loading = true; _error = null; });
    try {
      final resp = await widget.apiClient.get('/v1/staff/workflow-steps/${widget.stepId}');
      setState(() { _data = resp; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Document Review')),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Text('Error: $_error'));
    final data = _data!;

    final pages = (data['pages'] as List?) ?? [];
    final annotations = (data['annotations_by_department'] as Map?) ?? {};
    final submission = data['submission'] as Map<String, dynamic>? ?? {};
    final templateData = submission['template_data'] as Map<String, dynamic>?;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Template data
          if (templateData != null && templateData.isNotEmpty) ...[
            const Text('Template Data', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  children: templateData.entries.map((e) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        SizedBox(width: 120, child: Text('${e.key}:', style: const TextStyle(fontWeight: FontWeight.w500))),
                        Expanded(child: Text('${e.value}')),
                      ],
                    ),
                  )).toList(),
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],

          // Scanned pages
          const Text('Scanned Pages', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          ...pages.map<Widget>((p) {
            final page = p as Map<String, dynamic>;
            return Card(
              margin: const EdgeInsets.only(bottom: 12),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Page ${page['page_number']}', style: const TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 8),
                    if (page['image_url'] != null)
                      ClipRRect(
                        borderRadius: BorderRadius.circular(8),
                        child: Image.network(page['image_url'] as String, height: 200, fit: BoxFit.contain),
                      ),
                    const SizedBox(height: 8),
                    if (page['ocr_text'] != null)
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(4)),
                        child: Text(page['ocr_text'] as String, style: const TextStyle(fontSize: 13)),
                      ),
                    if (page['ocr_confidence'] != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 4),
                        child: Text('Confidence: ${(page['ocr_confidence'] as num).toStringAsFixed(2)}',
                            style: TextStyle(fontSize: 12, color: Colors.grey.shade600)),
                      ),
                  ],
                ),
              ),
            );
          }),

          // Prior annotations
          if (annotations.isNotEmpty) ...[
            const SizedBox(height: 16),
            const Text('Prior Annotations', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            ...(annotations as Map<String, dynamic>).entries.map<Widget>((entry) {
              final deptName = entry.key;
              final items = entry.value as List;
              return Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(deptName, style: const TextStyle(fontWeight: FontWeight.w600)),
                      const Divider(),
                      ...items.map<Widget>((a) {
                        final ann = a as Map<String, dynamic>;
                        return Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Chip(label: Text(ann['type'] as String? ?? '', style: const TextStyle(fontSize: 11))),
                              const SizedBox(width: 8),
                              Expanded(child: Text(ann['content'] as String? ?? '')),
                            ],
                          ),
                        );
                      }),
                    ],
                  ),
                ),
              );
            }),
          ],

          const SizedBox(height: 80), // Space for FAB
        ],
      ),
    );
  }
}
