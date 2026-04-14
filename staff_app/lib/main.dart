import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_dart/shared_dart.dart';

import 'features/auth/staff_auth_screen.dart';
import 'features/dossier/case_type_selector_screen.dart';
import 'features/dossier/guided_capture_screen.dart';
import 'features/review/department_queue_screen.dart';
import 'features/scan/create_submission_screen.dart';

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

class _StaffHomeScreen extends StatefulWidget {
  const _StaffHomeScreen();

  @override
  State<_StaffHomeScreen> createState() => _StaffHomeScreenState();
}

class _StaffHomeScreenState extends State<_StaffHomeScreen> {
  late final ApiClient apiClient;
  late final DossierApi dossierApi;
  List<DossierListItemDto> _draftDossiers = [];
  final _storage = const FlutterSecureStorage();

  @override
  void initState() {
    super.initState();
    apiClient = ApiClient(
      baseUrl: const String.fromEnvironment(
        'API_BASE_URL',
        defaultValue: 'http://10.0.2.2:8000',
      ),
    );
    dossierApi = DossierApi(apiClient);
    _loadTokenAndData();
  }

  Future<void> _loadTokenAndData() async {
    final token = await _storage.read(key: 'access_token');
    if (token != null) {
      apiClient.setToken(token);
    }
    _loadDraftDossiers();
  }

  Future<void> _loadDraftDossiers() async {
    try {
      final result = await dossierApi.listDossiers(status: 'draft', pageSize: 5);
      final drafts = result['items'] as List<DossierListItemDto>? ?? [];
      // Also load scanning dossiers
      final scanningResult = await dossierApi.listDossiers(status: 'scanning', pageSize: 5);
      final scanning = scanningResult['items'] as List<DossierListItemDto>? ?? [];
      if (mounted) {
        setState(() => _draftDossiers = [...drafts, ...scanning]);
      }
    } catch (_) {
      // Silently ignore — not critical
    }
  }

  Future<void> _resumeDossier(DossierListItemDto item) async {
    try {
      final dossier = await dossierApi.getDossier(item.id);
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => GuidedCaptureScreen(
            initialDossier: dossier,
            dossierApi: dossierApi,
          ),
        ),
      );
      unawaited(_loadDraftDossiers());
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
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
              subtitle: 'Chọn loại thủ tục và chụp tài liệu theo hướng dẫn',
              onTap: () async {
                final caseType = await Navigator.of(context).push<CaseTypeDto>(
                  MaterialPageRoute(
                    builder: (_) => CaseTypeSelectorScreen(dossierApi: dossierApi),
                  ),
                );
                if (caseType == null || !context.mounted) return;

                final citizenId = await _showCitizenIdDialog(context);
                if (citizenId == null || !context.mounted) return;

                try {
                  final dossier = await dossierApi.createDossier(
                    citizenIdNumber: citizenId,
                    caseTypeId: caseType.id,
                  );
                  if (!context.mounted) return;
                  await Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => GuidedCaptureScreen(
                        initialDossier: dossier,
                        dossierApi: dossierApi,
                      ),
                    ),
                  );
                  unawaited(_loadDraftDossiers());
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Lỗi: $e')),
                    );
                  }
                }
              },
            ),
            const SizedBox(height: 12),
            _MenuCard(
              icon: Icons.document_scanner,
              title: 'Quét nhanh',
              subtitle: 'Quét tài liệu đơn lẻ — hệ thống tự nhận dạng',
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const CreateSubmissionScreen(),
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
            if (_draftDossiers.isNotEmpty) ...[
              const SizedBox(height: 20),
              Text(
                'Hồ sơ đang xử lý',
                style: Theme.of(context).textTheme.titleSmall?.copyWith(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              Expanded(
                child: ListView.separated(
                  itemCount: _draftDossiers.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 4),
                  itemBuilder: (context, index) {
                    final item = _draftDossiers[index];
                    return Card(
                      child: ListTile(
                        leading: const Icon(Icons.edit_document, color: Colors.orange),
                        title: Text(item.caseTypeName, style: const TextStyle(fontSize: 14)),
                        subtitle: Text(
                          '${item.status == 'draft' ? 'Nháp' : 'Đang quét'} • ${item.createdAt.day}/${item.createdAt.month}/${item.createdAt.year}',
                          style: const TextStyle(fontSize: 12),
                        ),
                        trailing: const Icon(Icons.chevron_right),
                        onTap: () => _resumeDossier(item),
                        dense: true,
                      ),
                    );
                  },
                ),
              ),
            ] else
              const Spacer(),
            Text(
              'v0.2.0 — Public Sector Platform',
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

Future<String?> _showCitizenIdDialog(BuildContext context) {
  final controller = TextEditingController();
  return showDialog<String>(
    context: context,
    builder: (ctx) => AlertDialog(
      title: const Text('Nhập số CCCD công dân'),
      content: TextField(
        controller: controller,
        keyboardType: TextInputType.number,
        maxLength: 12,
        autofocus: true,
        decoration: const InputDecoration(
          hintText: '012345678901',
          border: OutlineInputBorder(),
          labelText: 'Số CCCD',
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(ctx),
          child: const Text('Huỷ'),
        ),
        ElevatedButton(
          onPressed: () {
            final value = controller.text.trim();
            if (value.isEmpty) return;
            Navigator.pop(ctx, value);
          },
          child: const Text('Tiếp tục'),
        ),
      ],
    ),
  );
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
