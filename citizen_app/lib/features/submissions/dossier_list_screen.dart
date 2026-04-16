import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

import 'dossier_status_screen.dart';

class DossierListScreen extends StatefulWidget {
  final CitizenDossierApi citizenDossierApi;

  const DossierListScreen({super.key, required this.citizenDossierApi});

  @override
  State<DossierListScreen> createState() => _DossierListScreenState();
}

class _DossierListScreenState extends State<DossierListScreen> {
  List<DossierTrackingListItemDto> _dossiers = [];
  bool _loading = true;
  String? _error;
  String? _statusFilter;

  static const _filters = <String?, String>{
    null: 'Tất cả',
    'in_progress': 'Đang xử lý',
    'completed': 'Hoàn thành',
    'rejected': 'Từ chối',
  };

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final items = await widget.citizenDossierApi.listMyDossiers(
        status: _statusFilter,
      );
      setState(() {
        _dossiers = items;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Hồ sơ của tôi')),
      body: Column(
        children: [
          // Filter chips
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Wrap(
              spacing: 8,
              runSpacing: 0,
              children: _filters.entries.map((e) {
                final selected = _statusFilter == e.key;
                return FilterChip(
                  label: Text(e.value),
                  selected: selected,
                  onSelected: (_) {
                    setState(() => _statusFilter = e.key);
                    _load();
                  },
                );
              }).toList(),
            ),
          ),
          Expanded(child: _buildBody()),
        ],
      ),
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
            Text(_error!, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            ElevatedButton(onPressed: _load, child: const Text('Thử lại')),
          ],
        ),
      );
    }
    if (_dossiers.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.folder_off, size: 64, color: Colors.grey),
              SizedBox(height: 16),
              Text(
                'Bạn chưa có hồ sơ nào.\nVui lòng liên hệ bộ phận tiếp nhận.',
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey, fontSize: 15),
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        itemCount: _dossiers.length,
        itemBuilder: (context, index) {
          final d = _dossiers[index];
          return Card(
            margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            child: ListTile(
              leading: _statusIcon(d.status),
              title: Text(d.caseTypeName),
              subtitle: Text(
                '${d.statusLabelVi} • ${_formatDate(d.submittedAt)}',
              ),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => DossierStatusScreen(
                    dossierId: d.id,
                    citizenDossierApi: widget.citizenDossierApi,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }

  Widget _statusIcon(String status) {
    final (IconData icon, Color color) = switch (status) {
      'completed' => (Icons.check_circle, Colors.green),
      'rejected' => (Icons.cancel, Colors.red),
      'in_progress' => (Icons.pending, Colors.blue),
      _ => (Icons.circle_outlined, Colors.grey),
    };
    return Icon(icon, color: color, size: 28);
  }

  String _formatDate(DateTime? dt) {
    if (dt == null) return '';
    return '${dt.day}/${dt.month}/${dt.year}';
  }
}
