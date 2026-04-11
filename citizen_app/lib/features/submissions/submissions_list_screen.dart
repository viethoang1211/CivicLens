import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

class SubmissionsListScreen extends StatefulWidget {
  const SubmissionsListScreen({super.key});

  @override
  State<SubmissionsListScreen> createState() => _SubmissionsListScreenState();
}

class _SubmissionsListScreenState extends State<SubmissionsListScreen> {
  List<SubmissionDto> _submissions = [];
  bool _loading = true;
  String _filter = 'all';

  @override
  void initState() {
    super.initState();
    _loadSubmissions();
  }

  Future<void> _loadSubmissions() async {
    setState(() => _loading = true);
    // In production: fetch from API via citizen API client
    setState(() => _loading = false);
  }

  Color _statusColor(String status) {
    switch (status) {
      case 'completed':
        return Colors.green;
      case 'rejected':
        return Colors.red;
      case 'in_progress':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('My Submissions'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications),
            onPressed: () => Navigator.of(context).pushNamed('/notifications'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Filter chips
          Padding(
            padding: const EdgeInsets.all(8),
            child: Row(
              children: [
                for (final f in ['all', 'active', 'completed'])
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: FilterChip(
                      label: Text(f[0].toUpperCase() + f.substring(1)),
                      selected: _filter == f,
                      onSelected: (selected) {
                        setState(() => _filter = f);
                        _loadSubmissions();
                      },
                    ),
                  ),
              ],
            ),
          ),
          // List
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _submissions.isEmpty
                    ? const Center(child: Text('No submissions found'))
                    : RefreshIndicator(
                        onRefresh: _loadSubmissions,
                        child: ListView.builder(
                          itemCount: _submissions.length,
                          itemBuilder: (context, index) {
                            final sub = _submissions[index];
                            return Card(
                              margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                              child: ListTile(
                                leading: CircleAvatar(
                                  backgroundColor: _statusColor(sub.status),
                                  child: Text('${sub.completedSteps ?? 0}/${sub.totalSteps ?? 0}',
                                      style: const TextStyle(color: Colors.white, fontSize: 12)),
                                ),
                                title: Text(sub.documentTypeName ?? 'Submission'),
                                subtitle: Text('${sub.status} • ${sub.submittedAt.toLocal().toString().split('.')[0]}'),
                                trailing: sub.isDelayed
                                    ? const Icon(Icons.warning, color: Colors.orange)
                                    : const Icon(Icons.chevron_right),
                                onTap: () => Navigator.of(context).pushNamed('/submission/${sub.id}'),
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
