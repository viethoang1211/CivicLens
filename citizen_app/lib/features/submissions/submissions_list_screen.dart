import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

class SubmissionsListScreen extends StatefulWidget {
  final CitizenApi citizenApi;

  const SubmissionsListScreen({super.key, required this.citizenApi});

  @override
  State<SubmissionsListScreen> createState() => _SubmissionsListScreenState();
}

class _SubmissionsListScreenState extends State<SubmissionsListScreen> {
  List<SubmissionDto> _submissions = [];
  bool _loading = true;
  String? _error;
  String _filter = 'all';

  @override
  void initState() {
    super.initState();
    _loadSubmissions();
  }

  Future<void> _loadSubmissions() async {
    setState(() { _loading = true; _error = null; });
    try {
      final resp = await widget.citizenApi.listSubmissions(
        status: _filter == 'all' ? null : _filter,
      );
      final rawItems = resp['items'];
      final items = (rawItems is List ? rawItems : <dynamic>[])
          .map((e) => SubmissionDto.fromJson(e as Map<String, dynamic>))
          .toList();
      if (mounted) setState(() { _submissions = items; _loading = false; });
    } catch (e) {
      if (mounted) setState(() { _error = e.toString(); _loading = false; });
    }
  }

  static const _filterLabels = {
    'all': 'Tất cả',
    'active': 'Đang xử lý',
    'completed': 'Hoàn thành',
  };

  static const _statusLabels = {
    'pending': 'Chờ xử lý',
    'ocr_processing': 'Đang OCR',
    'classifying': 'Đang phân loại',
    'pending_classification': 'Chờ xác nhận',
    'classified': 'Đã phân loại',
    'in_progress': 'Đang xử lý',
    'completed': 'Hoàn thành',
    'rejected': 'Bị từ chối',
  };

  Color _statusColor(String status) {
    switch (status) {
      case 'completed':
        return Colors.green;
      case 'rejected':
        return Colors.red;
      case 'in_progress':
      case 'classified':
        return Colors.blue;
      case 'pending_classification':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Hồ sơ đã quét'),
      ),
      body: Column(
        children: [
          // Filter chips
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _filterLabels.entries.map((e) => Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(e.value),
                    selected: _filter == e.key,
                    onSelected: (_) {
                      setState(() => _filter = e.key);
                      _loadSubmissions();
                    },
                  ),
                )).toList(),
              ),
            ),
          ),
          // List
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(Icons.error_outline, color: Colors.red, size: 48),
                            const SizedBox(height: 8),
                            Text(_error!, textAlign: TextAlign.center),
                            const SizedBox(height: 16),
                            ElevatedButton(onPressed: _loadSubmissions, child: const Text('Thử lại')),
                          ],
                        ),
                      )
                    : _submissions.isEmpty
                        ? const Center(
                            child: Column(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(Icons.inbox_outlined, size: 64, color: Colors.grey),
                                SizedBox(height: 8),
                                Text('Chưa có hồ sơ nào', style: TextStyle(color: Colors.grey)),
                              ],
                            ),
                          )
                        : RefreshIndicator(
                            onRefresh: _loadSubmissions,
                            child: ListView.builder(
                              itemCount: _submissions.length,
                              itemBuilder: (context, index) {
                                final sub = _submissions[index];
                                final statusLabel = _statusLabels[sub.status] ?? sub.status;
                                final steps = sub.totalSteps ?? 0;
                                final done = sub.completedSteps ?? 0;
                                return Card(
                                  margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                                  child: ListTile(
                                    leading: CircleAvatar(
                                      backgroundColor: _statusColor(sub.status),
                                      child: steps > 0
                                          ? Text('$done/$steps',
                                              style: const TextStyle(color: Colors.white, fontSize: 12))
                                          : const Icon(Icons.description, color: Colors.white, size: 18),
                                    ),
                                    title: Text(sub.documentTypeName?.isNotEmpty == true
                                        ? sub.documentTypeName!
                                        : 'Hồ sơ quét nhanh'),
                                    subtitle: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        Text(statusLabel),
                                        if (sub.currentStep != null)
                                          Text('Phòng: ${sub.currentStep!.departmentName}',
                                              style: const TextStyle(fontSize: 12)),
                                        Text(
                                          sub.submittedAt.toLocal().toString().split('.')[0],
                                          style: const TextStyle(fontSize: 11, color: Colors.grey),
                                        ),
                                      ],
                                    ),
                                    isThreeLine: true,
                                    trailing: sub.isDelayed
                                        ? const Icon(Icons.warning, color: Colors.orange)
                                        : const Icon(Icons.chevron_right),
                                  ),
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
    );
  }
}
