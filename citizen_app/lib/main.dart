import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

import 'features/auth/vneid_auth_screen.dart';
import 'features/submissions/dossier_lookup_screen.dart';

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
      initialRoute: '/login',
      routes: {
        '/login': (_) => const VneidAuthScreen(),
        '/submissions': (_) => const _CitizenHomeScreen(),
      },
    );
  }
}

class _CitizenHomeScreen extends StatelessWidget {
  const _CitizenHomeScreen();

  @override
  Widget build(BuildContext context) {
    final apiClient = ApiClient(
      baseUrl: const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://10.0.2.2:8000',
      ),
    );
    final citizenDossierApi = CitizenDossierApi(apiClient);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dịch vụ công trực tuyến'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 24),
            _MenuCard(
              icon: Icons.search,
              title: 'Tra cứu hồ sơ',
              subtitle: 'Nhập mã tham chiếu để theo dõi tiến độ',
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => DossierLookupScreen(
                    citizenDossierApi: citizenDossierApi,
                  ),
                ),
              ),
            ),
            const Spacer(),
            Text(
              'v0.1.0 — Dịch vụ công trực tuyến',
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
  final VoidCallback onTap;

  const _MenuCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 1,
      child: ListTile(
        leading: Icon(icon, size: 36, color: Theme.of(context).colorScheme.primary),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      ),
    );
  }
}
