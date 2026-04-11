import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

import 'features/auth/staff_auth_screen.dart';
import 'features/dossier/case_type_selector_screen.dart';
import 'features/review/department_queue_screen.dart';

void main() {
  runApp(const StaffApp());
}

class StaffApp extends StatelessWidget {
  const StaffApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Public Sector - Staff',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: const Color(0xFF1565C0),
        useMaterial3: true,
        brightness: Brightness.light,
      ),
      initialRoute: '/login',
      routes: {
        '/login': (_) => const StaffAuthScreen(),
        '/home': (_) => const _StaffHomeScreen(),
      },
    );
  }
}

class _StaffHomeScreen extends StatelessWidget {
  const _StaffHomeScreen();

  @override
  Widget build(BuildContext context) {
    final apiClient = ApiClient(
      baseUrl: const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://10.0.2.2:8000',
      ),
    );
    final dossierApi = DossierApi(apiClient);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Hệ thống Quản lý Hồ sơ'),
        centerTitle: true,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const SizedBox(height: 24),
            _MenuCard(
              icon: Icons.folder_open,
              title: 'Tạo Hồ sơ mới',
              subtitle: 'Chọn loại thủ tục và nộp hồ sơ',
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => CaseTypeSelectorScreen(
                    dossierApi: dossierApi,
                  ),
                ),
              ),
            ),
            const SizedBox(height: 12),
            _MenuCard(
              icon: Icons.assignment,
              title: 'Hàng đợi xử lý',
              subtitle: 'Xem và xử lý các hồ sơ được phân công',
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => DepartmentQueueScreen(
                    departmentId: 'default',
                    apiClient: apiClient,
                  ),
                ),
              ),
            ),
            const Spacer(),
            Text(
              'v0.1.0 — Public Sector Platform',
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
