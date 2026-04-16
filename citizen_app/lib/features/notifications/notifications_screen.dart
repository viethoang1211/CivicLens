import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

import '../submissions/dossier_status_screen.dart';

class NotificationsScreen extends StatefulWidget {
  final ApiClient apiClient;

  const NotificationsScreen({super.key, required this.apiClient});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<NotificationDto> _notifications = [];
  bool _loading = true;
  String? _error;

  late final CitizenApi _citizenApi = CitizenApi(client: widget.apiClient);
  late final CitizenDossierApi _dossierApi = CitizenDossierApi(widget.apiClient);

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    setState(() { _loading = true; _error = null; });
    try {
      final resp = await _citizenApi.listNotifications();
      final items = (resp['notifications'] as List)
          .map((e) => NotificationDto.fromJson(e as Map<String, dynamic>))
          .toList();
      setState(() { _notifications = items; _loading = false; });
    } catch (e) {
      setState(() { _error = e.toString(); _loading = false; });
    }
  }

  Future<void> _markRead(String notificationId) async {
    try {
      await _citizenApi.markNotificationRead(notificationId);
      setState(() {
        final idx = _notifications.indexWhere((n) => n.id == notificationId);
        if (idx != -1) {
          _notifications[idx] = _notifications[idx].copyWith(isRead: true);
        }
      });
    } catch (_) {}
  }

  Future<void> _markAllRead() async {
    for (final n in _notifications.where((n) => !n.isRead)) {
      await _markRead(n.id);
    }
  }

  void _onNotificationTap(NotificationDto n) {
    if (!n.isRead) _markRead(n.id);
    if (n.dossierId != null) {
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => DossierStatusScreen(
            dossierId: n.dossierId!,
            citizenDossierApi: _dossierApi,
          ),
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Thông báo'),
        actions: [
          if (_notifications.any((n) => !n.isRead))
            TextButton(
              onPressed: _markAllRead,
              child: const Text('Đánh dấu tất cả đã đọc'),
            ),
        ],
      ),
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
            Text('Lỗi: $_error'),
            const SizedBox(height: 8),
            ElevatedButton(onPressed: _loadNotifications, child: const Text('Thử lại')),
          ],
        ),
      );
    }
    if (_notifications.isEmpty) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.notifications_off, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('Chưa có thông báo', style: TextStyle(color: Colors.grey, fontSize: 15)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadNotifications,
      child: ListView.separated(
        itemCount: _notifications.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (context, index) {
          final n = _notifications[index];
          return ListTile(
            leading: CircleAvatar(
              backgroundColor: n.isRead ? Colors.grey.shade300 : Colors.blue,
              child: Icon(_iconForType(n.type), color: Colors.white, size: 18),
            ),
            title: Text(n.title, style: TextStyle(fontWeight: n.isRead ? FontWeight.normal : FontWeight.bold)),
            subtitle: Text(n.body, maxLines: 2, overflow: TextOverflow.ellipsis),
            trailing: Text(
              _formatRelative(n.sentAt),
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
            onTap: () => _onNotificationTap(n),
          );
        },
      ),
    );
  }

  IconData _iconForType(String type) {
    switch (type) {
      case 'step_advanced': return Icons.arrow_forward;
      case 'completed': return Icons.check_circle;
      case 'info_requested': return Icons.info;
      case 'delayed': return Icons.warning;
      default: return Icons.notifications;
    }
  }

  String _formatRelative(DateTime dt) {
    final diff = DateTime.now().difference(dt);
    if (diff.inMinutes < 60) return '${diff.inMinutes} phút trước';
    if (diff.inHours < 24) return '${diff.inHours} giờ trước';
    return '${diff.inDays} ngày trước';
  }
}
