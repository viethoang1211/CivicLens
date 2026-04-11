import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';

class VneidAuthScreen extends StatefulWidget {
  const VneidAuthScreen({super.key});

  @override
  State<VneidAuthScreen> createState() => _VneidAuthScreenState();
}

class _VneidAuthScreenState extends State<VneidAuthScreen> {
  final _storage = const FlutterSecureStorage();
  bool _loading = false;
  String? _error;

  Future<void> _authenticateWithVneid() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      // In production: launch VNeID OAuth flow
      // For now: simulate with a dialog for CCCD number
      final cccd = await _showCccdDialog();
      if (cccd == null || cccd.isEmpty) {
        setState(() => _loading = false);
        return;
      }

      final dio = Dio(BaseOptions(
        baseUrl: const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000'),
      ));

      final response = await dio.post('/v1/citizen/auth/vneid', data: {
        'vneid_auth_code': cccd,
        'redirect_uri': 'citizen-app://callback',
      });

      final data = response.data;
      await _storage.write(key: 'access_token', value: data['access_token']);
      await _storage.write(key: 'refresh_token', value: data['refresh_token']);
      await _storage.write(key: 'citizen_name', value: data['citizen']['full_name']);

      if (mounted) {
        Navigator.of(context).pushReplacementNamed('/submissions');
      }
    } on DioException catch (e) {
      setState(() {
        _error = e.response?.data?['detail'] ?? 'Authentication failed.';
      });
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<String?> _showCccdDialog() async {
    final controller = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('VNeID Authentication'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: 'Enter CCCD number'),
          keyboardType: TextInputType.number,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          TextButton(onPressed: () => Navigator.pop(context, controller.text), child: const Text('Login')),
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
              const Text('Citizen Portal', style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              const Text('Track your document submissions'),
              const SizedBox(height: 48),
              if (_error != null) ...[
                Text(_error!, style: const TextStyle(color: Colors.red)),
                const SizedBox(height: 16),
              ],
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  onPressed: _loading ? null : _authenticateWithVneid,
                  icon: _loading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Icon(Icons.fingerprint),
                  label: const Text('Login with VNeID'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
