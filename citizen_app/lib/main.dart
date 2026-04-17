import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_dart/shared_dart.dart';

import 'features/auth/vneid_auth_screen.dart';
import 'features/submissions/dossier_list_screen.dart';
import 'features/submissions/dossier_lookup_screen.dart';
import 'features/submissions/submissions_list_screen.dart';
import 'features/notifications/notifications_screen.dart';

/// Single source of truth for backend URL across entire citizen app.
const kApiBaseUrl = String.fromEnvironment(
  'API_BASE_URL',
  defaultValue: 'http://10.0.2.2:8000',
);

/// Global ApiClient singleton — token set after login or startup check.
final apiClient = ApiClient(baseUrl: kApiBaseUrl);

void main() {
  runApp(const CitizenApp());
}

class CitizenApp extends StatelessWidget {
  const CitizenApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Dịch vụ công trực tuyến',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF2E7D32),
        useMaterial3: true,
        brightness: Brightness.light,
      ),
      home: const _StartupGate(),
    );
  }
}

/// Checks secure storage for existing token; skips login if valid.
class _StartupGate extends StatefulWidget {
  const _StartupGate();

  @override
  State<_StartupGate> createState() => _StartupGateState();
}

class _StartupGateState extends State<_StartupGate> {
  @override
  void initState() {
    super.initState();
    _checkToken();
  }

  Future<void> _checkToken() async {
    const storage = FlutterSecureStorage();
    final token = await storage.read(key: 'access_token');
    final name = await storage.read(key: 'citizen_name');
    if (token != null && token.isNotEmpty && mounted) {
      apiClient.setToken(token);
      if (!mounted) return;
      await Navigator.of(context).pushReplacement(
        MaterialPageRoute(
          builder: (_) => CitizenHomeScreen(
            apiClient: apiClient,
            citizenName: name ?? 'Công dân',
          ),
        ),
      );
    } else if (mounted) {
      await Navigator.of(context).pushReplacement(
        MaterialPageRoute(builder: (_) => const VneidAuthScreen()),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(child: CircularProgressIndicator()),
    );
  }
}

class CitizenHomeScreen extends StatefulWidget {
  final ApiClient apiClient;
  final String citizenName;

  const CitizenHomeScreen({
    super.key,
    required this.apiClient,
    required this.citizenName,
  });

  @override
  State<CitizenHomeScreen> createState() => _CitizenHomeScreenState();
}

class _CitizenHomeScreenState extends State<CitizenHomeScreen> {
  int _dossierCount = 0;
  int _submissionCount = 0;
  int _unreadCount = 0;

  late final CitizenDossierApi _dossierApi = CitizenDossierApi(widget.apiClient);
  late final CitizenApi _citizenApi = CitizenApi(client: widget.apiClient);

  @override
  void initState() {
    super.initState();
    _loadBadges();
  }

  Future<void> _loadBadges() async {
    try {
      final dossiers = await _dossierApi.listMyDossiers(pageSize: 1);
      if (mounted) setState(() => _dossierCount = dossiers.length);
    } catch (_) {}
    try {
      final resp = await _citizenApi.listSubmissions(limit: 100);
      final items = resp['items'] as List? ?? [];
      if (mounted) setState(() => _submissionCount = items.length);
    } catch (_) {}
    try {
      final resp = await _citizenApi.listNotifications(perPage: 1);
      final unread = resp['unread_count'] as int? ?? 0;
      if (mounted) setState(() => _unreadCount = unread);
    } catch (_) {}
  }

  Future<void> _logout() async {
    const storage = FlutterSecureStorage();
    await storage.deleteAll();
    widget.apiClient.clearToken();
    if (mounted) {
      await Navigator.of(context).pushAndRemoveUntil(
        MaterialPageRoute(builder: (_) => const VneidAuthScreen()),
        (_) => false,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dịch vụ công trực tuyến'),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Đăng xuất',
            onPressed: _logout,
          ),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Xin chào, ${widget.citizenName}',
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
            ),
            const SizedBox(height: 24),
            _MenuCard(
              icon: Icons.folder_open,
              title: 'Hồ sơ của tôi',
              subtitle: 'Xem danh sách hồ sơ đã nộp',
              badge: _dossierCount > 0 ? '$_dossierCount' : null,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => DossierListScreen(
                    citizenDossierApi: _dossierApi,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            _MenuCard(
              icon: Icons.document_scanner,
              title: 'Hồ sơ Quick Scan',
              subtitle: 'Xem hồ sơ từ quét nhanh tại quầy',
              badge: _submissionCount > 0 ? '$_submissionCount' : null,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => SubmissionsListScreen(
                    citizenApi: _citizenApi,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            _MenuCard(
              icon: Icons.search,
              title: 'Tra cứu hồ sơ',
              subtitle: 'Nhập mã tham chiếu để theo dõi tiến độ',
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => DossierLookupScreen(
                    citizenDossierApi: _dossierApi,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 8),
            _MenuCard(
              icon: Icons.notifications,
              title: 'Thông báo',
              subtitle: 'Xem các thông báo từ hệ thống',
              badge: _unreadCount > 0 ? '$_unreadCount' : null,
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => NotificationsScreen(
                    apiClient: widget.apiClient,
                  ),
                ),
              ),
            ),
            const Spacer(),
            Text(
              'v0.2.0 — Dịch vụ công trực tuyến',
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}

class _MenuCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final String? badge;
  final VoidCallback onTap;

  const _MenuCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    this.badge,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 1,
      child: ListTile(
        leading: Badge(
          isLabelVisible: badge != null,
          label: badge != null ? Text(badge!) : null,
          child: Icon(icon, size: 36, color: Theme.of(context).colorScheme.primary),
        ),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),
    );
  }
}
