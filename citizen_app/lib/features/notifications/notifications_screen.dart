import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

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

  @override
  void initState() {
    super.initState();
    _loadNotifications();
  }

  Future<void> _loadNotifications() async {
    setState(() { _loading = true; _error = null; });
    try {
      final resp = await widget.apiClient.get('/v1/citizen/notifications');
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
      await widget.apiClient.put('/v1/citizen/notifications/$notificationId/read', data: {});
      setState(() {
        final idx = _notifications.indexWhere((n) => n.id == notificationId);
        if (idx != -1) {
          _notifications[idx] = _notifications[idx].copyWith(isRead: true);
        }
      });
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Thông báo'),
        actions: [
          if (_notifications.any((n) => !n.isRead))
            TextButton(
              onPressed: () async {
                for (final n in _notifications.where((n) => !n.isRead)) {
                  await _markRead(n.id);
                }
              },
              child: const Text('Mark all read'),
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
            Text('Error: $_error'),
            const SizedBox(height: 8),
            ElevatedButton(onPressed: _loadNotifications, child: const Text('Retry')),
          ],
        ),
      );
    }
    if (_notifications.isEmpty) {
      return const Center(child: Text('No notifications yet'));
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
            onTap: () {
              if (!n.isRead) _markRead(n.id);
            },
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
    if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
    if (diff.inHours < 24) return '${diff.inHours}h ago';
    return '${diff.inDays}d ago';
  }
}
