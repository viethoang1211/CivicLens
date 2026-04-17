import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

import 'document_review_screen.dart';

class DepartmentQueueScreen extends StatefulWidget {
  final String departmentId;
  final ApiClient apiClient;
  /// Staff member's clearance level used to filter visible submissions.
  final int staffClearanceLevel;

  const DepartmentQueueScreen({
    super.key,
    required this.departmentId,
    required this.apiClient,
    this.staffClearanceLevel = 0,
  });

  @override
  State<DepartmentQueueScreen> createState() => _DepartmentQueueScreenState();
}

class _DepartmentQueueScreenState extends State<DepartmentQueueScreen> {
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadQueue();
  }

  Future<void> _loadQueue() async {
    setState(() { _loading = true; _error = null; });
    try {
      final resp = await widget.apiClient.get(
        '/v1/staff/departments/${widget.departmentId}/queue',
      );
      final allItems = (resp.data['items'] as List?)
          ?.cast<Map<String, dynamic>>() ?? [];

      // Filter out submissions above staff's clearance level
      final filtered = allItems.where((item) {
        final classification = item['security_classification'] as int? ?? 0;
        return classification <= widget.staffClearanceLevel;
      }).toList();

      setState(() { _items = filtered; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  String _formatDateTime(String? iso) {
    if (iso == null) return 'N/A';
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day.toString().padLeft(2, '0')}/${dt.month.toString().padLeft(2, '0')}/${dt.year} ${dt.hour.toString().padLeft(2, '0')}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Hàng đợi phòng ban')),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 48, color: Colors.red),
            const SizedBox(height: 12),
            Text('Lỗi: $_error', textAlign: TextAlign.center),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              onPressed: _loadQueue,
              icon: const Icon(Icons.refresh),
              label: const Text('Thử lại'),
            ),
          ],
        ),
      );
    }
    if (_items.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.inbox_rounded, size: 64, color: Colors.grey.shade300),
            const SizedBox(height: 12),
            const Text('Không có hồ sơ trong hàng đợi', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadQueue,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: _items.length,
        itemBuilder: (context, index) {
          final item = _items[index];
          final isDelayed = item['is_delayed'] ?? false;
          final isUrgent = item['priority'] == 'urgent';
          final docTypeName = (item['document_type_name'] as String?)?.isNotEmpty == true
              ? item['document_type_name'] as String
              : 'Hồ sơ';
          final startedAt = _formatDateTime(item['started_at'] as String?);

          return Card(
            margin: const EdgeInsets.only(bottom: 10),
            elevation: 1,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: isDelayed
                  ? const BorderSide(color: Colors.red, width: 1)
                  : BorderSide.none,
            ),
            child: InkWell(
              borderRadius: BorderRadius.circular(12),
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (_) => DocumentReviewScreen(
                      apiClient: widget.apiClient,
                      stepId: item['workflow_step_id'] as String,
                    ),
                  ),
                );
              },
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Title row
                    Row(
                      children: [
                        Icon(Icons.description_outlined, size: 20, color: Theme.of(context).colorScheme.primary),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            docTypeName,
                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15),
                          ),
                        ),
                        if (isUrgent)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: Colors.red.shade50,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Row(mainAxisSize: MainAxisSize.min, children: [
                              Icon(Icons.priority_high, size: 14, color: Colors.red.shade700),
                              const SizedBox(width: 2),
                              Text('Khẩn', style: TextStyle(fontSize: 11, color: Colors.red.shade700, fontWeight: FontWeight.w600)),
                            ]),
                          ),
                        if (isDelayed)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                            decoration: BoxDecoration(
                              color: Colors.red,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: const Text('Trễ hạn', style: TextStyle(fontSize: 11, color: Colors.white, fontWeight: FontWeight.w600)),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    // Time row
                    Row(
                      children: [
                        Icon(Icons.access_time, size: 14, color: Colors.grey.shade600),
                        const SizedBox(width: 4),
                        Text(
                          startedAt,
                          style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
                        ),
                      ],
                    ),
                    // Summary
                    if (item['summary_preview'] != null) ...[
                      const SizedBox(height: 8),
                      Text(
                        item['summary_preview'] as String,
                        maxLines: 3,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(fontSize: 13, color: Colors.grey.shade700, height: 1.4),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
