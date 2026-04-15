import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_dart/shared_dart.dart';

import 'features/auth/staff_auth_screen.dart';
import 'features/dossier/case_type_selector_screen.dart';
import 'features/dossier/guided_capture_screen.dart';
import 'features/review/department_queue_screen.dart';
import 'features/scan/create_submission_screen.dart';
import 'features/scan/multi_page_scan.dart';
import 'features/search/search_screen.dart';

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
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
        cardTheme: CardThemeData(
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
            side: BorderSide(color: Colors.grey.shade200),
          ),
        ),
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
  late final StaffSubmissionsApi submissionsApi;
  late final SearchApiClient searchApiClient;
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
    submissionsApi = StaffSubmissionsApi(apiClient);
    searchApiClient = SearchApiClient(apiClient);
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
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      backgroundColor: cs.surfaceContainerLowest,
      body: SafeArea(
        child: CustomScrollView(
          slivers: [
            // ── Header ──
            SliverToBoxAdapter(
              child: Container(
                padding: const EdgeInsets.fromLTRB(24, 24, 24, 20),
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [cs.primary, cs.primary.withAlpha(200)],
                  ),
                  borderRadius: const BorderRadius.only(
                    bottomLeft: Radius.circular(28),
                    bottomRight: Radius.circular(28),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: Colors.white.withAlpha(50),
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: const Icon(Icons.account_balance, color: Colors.white, size: 28),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Hệ thống Quản lý Hồ sơ',
                                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                  color: Colors.white,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Nền tảng xử lý hồ sơ công',
                                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                  color: Colors.white70,
                                ),
                              ),
                            ],
                          ),
                        ),
                        IconButton(
                          onPressed: () async {
                            await _storage.deleteAll();
                            if (context.mounted) {
                              Navigator.of(context).pushReplacementNamed('/login');
                            }
                          },
                          icon: const Icon(Icons.logout, color: Colors.white70),
                          tooltip: 'Đăng xuất',
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            // ── Menu grid ──
            SliverPadding(
              padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
              sliver: SliverToBoxAdapter(
                child: Text(
                  'Chức năng',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w700,
                    color: cs.onSurface.withAlpha(180),
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ),
            SliverPadding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              sliver: SliverGrid.count(
                crossAxisCount: 2,
                crossAxisSpacing: 14,
                mainAxisSpacing: 14,
                childAspectRatio: 1.05,
                children: [
                  _FeatureTile(
                    icon: Icons.folder_open_rounded,
                    label: 'Tạo Hồ sơ mới',
                    description: 'Chọn thủ tục & chụp tài liệu',
                    color: const Color(0xFF1565C0),
                    onTap: _startNewDossier,
                  ),
                  _FeatureTile(
                    icon: Icons.document_scanner_rounded,
                    label: 'Quét nhanh',
                    description: 'Quét đơn lẻ, AI nhận dạng',
                    color: const Color(0xFF00897B),
                    onTap: _startQuickScan,
                  ),
                  _FeatureTile(
                    icon: Icons.assignment_rounded,
                    label: 'Hàng đợi',
                    description: 'Hồ sơ được phân công',
                    color: const Color(0xFFE65100),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => DepartmentQueueScreen(
                          departmentId: 'default',
                          apiClient: apiClient,
                        ),
                      ),
                    ),
                  ),
                  _FeatureTile(
                    icon: Icons.search_rounded,
                    label: 'Tìm kiếm',
                    description: 'Tra cứu hồ sơ & tài liệu',
                    color: const Color(0xFF6A1B9A),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => SearchScreen(searchApiClient: searchApiClient),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // ── Draft dossiers section ──
            if (_draftDossiers.isNotEmpty) ...[
              SliverPadding(
                padding: const EdgeInsets.fromLTRB(20, 24, 20, 8),
                sliver: SliverToBoxAdapter(
                  child: Row(
                    children: [
                      Icon(Icons.edit_note_rounded, size: 20, color: cs.primary),
                      const SizedBox(width: 8),
                      Text(
                        'Hồ sơ đang xử lý',
                        style: Theme.of(context).textTheme.titleSmall?.copyWith(
                          fontWeight: FontWeight.w700,
                          color: cs.onSurface.withAlpha(180),
                          letterSpacing: 0.5,
                        ),
                      ),
                      const Spacer(),
                      Text(
                        '${_draftDossiers.length} hồ sơ',
                        style: Theme.of(context).textTheme.bodySmall?.copyWith(
                          color: cs.onSurface.withAlpha(130),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              SliverPadding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                sliver: SliverList.separated(
                  itemCount: _draftDossiers.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final item = _draftDossiers[index];
                    final isDraft = item.status == 'draft';
                    return Card(
                      child: InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: () => _resumeDossier(item),
                        child: Padding(
                          padding: const EdgeInsets.all(14),
                          child: Row(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(10),
                                decoration: BoxDecoration(
                                  color: (isDraft ? Colors.orange : Colors.blue).withAlpha(25),
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                child: Icon(
                                  isDraft ? Icons.edit_document : Icons.scanner,
                                  color: isDraft ? Colors.orange.shade700 : Colors.blue.shade700,
                                  size: 22,
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      item.caseTypeName,
                                      style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    const SizedBox(height: 3),
                                    Text(
                                      '${isDraft ? 'Nháp' : 'Đang quét'} • ${item.createdAt.day}/${item.createdAt.month}/${item.createdAt.year}',
                                      style: TextStyle(fontSize: 12, color: cs.onSurface.withAlpha(150)),
                                    ),
                                  ],
                                ),
                              ),
                              Icon(Icons.chevron_right_rounded, color: cs.onSurface.withAlpha(100)),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
              ),
            ],

            // ── Footer ──
            SliverFillRemaining(
              hasScrollBody: false,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  const SizedBox(height: 32),
                  Text(
                    'v0.3.0 — Public Sector Platform',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: cs.onSurface.withAlpha(100),
                    ),
                  ),
                  const SizedBox(height: 16),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ── New Dossier flow ──
  Future<void> _startNewDossier() async {
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
  }

  // ── Quick Scan flow (fixed: now actually continues to scan) ──
  Future<void> _startQuickScan() async {
    // Step 1: Collect submission metadata
    final metadata = await Navigator.of(context).push<Map<String, dynamic>>(
      MaterialPageRoute(
        builder: (_) => const CreateSubmissionScreen(),
      ),
    );
    if (metadata == null || !context.mounted) return;

    // Step 2: Create submission via API
    try {
      final submission = await submissionsApi.createSubmission(
        citizenIdNumber: metadata['citizen_id_number'] as String,
        securityClassification: metadata['security_classification'] as int? ?? 0,
        priority: metadata['priority'] as String? ?? 'normal',
      );
      final submissionId = submission['id'] as String;

      if (!context.mounted) return;

      // Step 3: Navigate to multi-page scan
      final pages = await Navigator.of(context).push<List<File>>(
        MaterialPageRoute(
          builder: (_) => MultiPageScan(submissionId: submissionId),
        ),
      );
      if (pages == null || pages.isEmpty || !context.mounted) return;

      // Step 4: Upload pages
      _showProgressDialog(context, 'Đang tải lên ${pages.length} trang...');
      for (int i = 0; i < pages.length; i++) {
        await submissionsApi.uploadPage(
          submissionId: submissionId,
          pageNumber: i + 1,
          imageFile: pages[i],
        );
      }

      // Step 5: Finalize scan (triggers OCR)
      await submissionsApi.finalizeScan(submissionId);

      if (context.mounted) {
        Navigator.of(context).pop(); // dismiss progress dialog
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Đã tải lên ${pages.length} trang. OCR đang xử lý...'),
            backgroundColor: Colors.green,
          ),
        );
      }
    } catch (e) {
      if (context.mounted) {
        // Dismiss progress dialog if open
        Navigator.of(context).popUntil((route) => route.isFirst || route.settings.name == '/home');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  void _showProgressDialog(BuildContext context, String message) {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (_) => AlertDialog(
        content: Row(
          children: [
            const CircularProgressIndicator(),
            const SizedBox(width: 20),
            Expanded(child: Text(message)),
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

class _FeatureTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String description;
  final Color color;
  final VoidCallback onTap;

  const _FeatureTile({
    required this.icon,
    required this.label,
    required this.description,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: color.withAlpha(25),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: color, size: 26),
              ),
              const Spacer(),
              Text(
                label,
                style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 3),
              Text(
                description,
                style: TextStyle(
                  fontSize: 11.5,
                  color: Theme.of(context).colorScheme.onSurface.withAlpha(140),
                  height: 1.3,
                ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
