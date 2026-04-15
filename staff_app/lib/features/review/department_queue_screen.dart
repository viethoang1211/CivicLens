import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

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
        itemCount: _items.length,
        itemBuilder: (context, index) {
          final item = _items[index];
          final isDelayed = item['is_delayed'] ?? false;
          final isUrgent = item['priority'] == 'urgent';

          return Card(
            color: isDelayed ? Colors.red.shade50 : null,
            child: ListTile(
              leading: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  if (isUrgent) const Icon(Icons.priority_high, color: Colors.red),
                  if (isDelayed) const Icon(Icons.warning, color: Colors.orange, size: 16),
                ],
              ),
              title: Text(item['document_type_name'] ?? 'Document'),
              subtitle: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('Bắt đầu: ${item['started_at'] ?? 'N/A'}'),
                  if (item['summary_preview'] != null) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                          margin: const EdgeInsets.only(right: 4),
                          decoration: BoxDecoration(
                            color: Colors.purple.shade50,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: const Text(
                            'AI tạo',
                            style: TextStyle(fontSize: 10, color: Colors.purple),
                          ),
                        ),
                        Expanded(
                          child: Text(
                            item['summary_preview'],
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 12, color: Colors.black54),
                          ),
                        ),
                      ],
                    ),
                  ] else ...[
                    const SizedBox(height: 4),
                    const Text(
                      'Đang tạo tóm tắt...',
                      style: TextStyle(fontSize: 12, fontStyle: FontStyle.italic, color: Colors.grey),
                    ),
                  ],
                ],
              ),
              isThreeLine: true,
              trailing: isDelayed
                  ? const Chip(
                      label: Text('Trễ hạn', style: TextStyle(color: Colors.white, fontSize: 11)),
                      backgroundColor: Colors.red,
                    )
                  : null,
              onTap: () {
                Navigator.of(context).pushNamed(
                  '/review',
                  arguments: item['workflow_step_id'],
                );
              },
            ),
          );
        },
      ),
    );
  }
}
