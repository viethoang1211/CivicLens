import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import 'package:url_launcher/url_launcher.dart';

class VneidAuthScreen extends StatefulWidget {
  const VneidAuthScreen({super.key});

  @override
  State<VneidAuthScreen> createState() => _VneidAuthScreenState();
}

class _VneidAuthScreenState extends State<VneidAuthScreen> {
  final _storage = const FlutterSecureStorage();
  bool _loading = false;
  String? _error;

  static const _apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );

  static const _callbackUri = 'citizen-app://auth/callback';

  late final Dio _dio = Dio(BaseOptions(baseUrl: _apiBaseUrl));

  Future<void> _authenticateWithVneid() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // Step 1: Get the VNeID authorize URL from backend
      final urlResp = await _dio.get('/v1/citizen/auth/vneid/authorize-url', queryParameters: {
        'redirect_uri': _callbackUri,
      });

      final authorizeUrl = urlResp.data['authorize_url'] as String;

      // Step 2: Open VNeID login page in browser
      final uri = Uri.parse(authorizeUrl);
      if (!await launchUrl(uri, mode: LaunchMode.externalApplication)) {
        setState(() => _error = 'Không thể mở trang đăng nhập VNeID');
        return;
      }

      // The auth code will come back via deep link handled by _handleAuthCode
      // For now, show a dialog to paste the code (deep link setup varies by platform)
      if (mounted) {
        final code = await _showCodeInputDialog();
        if (code != null && code.isNotEmpty) {
          await _exchangeCode(code);
        }
      }
    } on DioException catch (e) {
      setState(() {
        _error = e.response?.data?['detail'] ?? 'Lỗi kết nối. Vui lòng thử lại.';
      });
    } catch (e) {
      setState(() => _error = 'Đã xảy ra lỗi: $e');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  /// Called when we have an auth code (from deep link or manual input)
  Future<void> _exchangeCode(String code) async {
    final response = await _dio.post('/v1/citizen/auth/vneid', data: {
      'vneid_auth_code': code,
      'redirect_uri': _callbackUri,
    });

    final data = response.data;
    await _storage.write(key: 'access_token', value: data['access_token']);
    await _storage.write(key: 'refresh_token', value: data['refresh_token']);
    await _storage.write(key: 'citizen_name', value: data['citizen']['full_name']);

    if (mounted) {
      Navigator.of(context).pushReplacementNamed('/submissions');
    }
  }

  /// Fallback: dialog to paste auth code when deep link is not configured.
  Future<String?> _showCodeInputDialog() async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Nhập mã xác thực'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Sau khi đăng nhập VNeID thành công, '
              'nhập mã code từ URL callback:',
              style: TextStyle(fontSize: 13, color: Colors.black54),
            ),
            const SizedBox(height: 12),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: 'Dán mã code tại đây',
                border: OutlineInputBorder(),
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Hủy')),
          FilledButton(onPressed: () => Navigator.pop(context, controller.text), child: const Text('Xác nhận')),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.account_balance, size: 80, color: Colors.blue),
              const SizedBox(height: 24),
              const Text(
                'Dịch vụ công trực tuyến',
                style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              const Text('Theo dõi hồ sơ của bạn'),
              const SizedBox(height: 48),
              if (_error != null) ...[
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.red.shade50,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline, color: Colors.red, size: 20),
                      const SizedBox(width: 8),
                      Expanded(child: Text(_error!, style: const TextStyle(color: Colors.red))),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _loading ? null : _authenticateWithVneid,
                  icon: _loading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.fingerprint),
                  label: const Text('Đăng nhập bằng VNeID'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
