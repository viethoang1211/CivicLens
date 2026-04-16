import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

/// Public lookup screen — citizens can enter a reference number (HS-YYYYMMDD-NNNNN)
/// to check their dossier status without logging in.
class DossierLookupScreen extends StatefulWidget {
  final CitizenDossierApi citizenDossierApi;

  const DossierLookupScreen({super.key, required this.citizenDossierApi});

  @override
  State<DossierLookupScreen> createState() => _DossierLookupScreenState();
}

class _DossierLookupScreenState extends State<DossierLookupScreen> {
  final _referenceController = TextEditingController();
  DossierTrackingDto? _result;
  bool _loading = false;
  String? _error;

  static final _refPattern = RegExp(r'^HS-\d{8}-[A-Za-z0-9]{5}$');

  Future<void> _lookup() async {
    final ref = _referenceController.text.trim().toUpperCase();
    if (!_refPattern.hasMatch(ref)) {
      setState(() => _error = 'Mã tham chiếu phải có dạng HS-YYYYMMDD-XXXXX');
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });
    try {
      final tracking = await widget.citizenDossierApi.lookupByReference(ref);
      setState(() {
        _result = tracking;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Không tìm thấy hồ sơ với mã tham chiếu này.';
        _loading = false;
      });
    }
  }

  @override
  void dispose() {
    _referenceController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tra cứu hồ sơ')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          const Text(
            'Nhập mã tham chiếu để kiểm tra trạng thái hồ sơ của bạn.',
            style: TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _referenceController,
            decoration: InputDecoration(
              labelText: 'Mã tham chiếu',
              hintText: 'HS-20250101-00001',
              border: const OutlineInputBorder(),
              errorText: _error,
              suffixIcon: IconButton(
                icon: const Icon(Icons.clear),
                onPressed: () {
                  _referenceController.clear();
                  setState(() {
                    _result = null;
                    _error = null;
                  });
                },
              ),
            ),
            textCapitalization: TextCapitalization.characters,
            onSubmitted: (_) => _lookup(),
          ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: _loading ? null : _lookup,
            icon: _loading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.search),
            label: Text(_loading ? 'Đang tìm kiếm...' : 'Tra cứu'),
          ),
          if (_result != null) ...[
            const SizedBox(height: 24),
            _buildResult(_result!),
          ],
        ],
      ),
    );
  }

  Widget _buildResult(DossierTrackingDto dossier) {
    final statusColor = dossier.isCompleted
        ? Colors.green
        : dossier.isRejected
            ? Colors.red
            : Colors.blue;

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: statusColor, width: 1.5),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  dossier.isCompleted
                      ? Icons.check_circle
                      : dossier.isRejected
                          ? Icons.cancel
                          : Icons.pending,
                  color: statusColor,
                ),
                const SizedBox(width: 8),
                Text(
                  dossier.statusLabelVi,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: statusColor,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text('Loại hồ sơ: ${dossier.caseTypeName}'),
            if (dossier.submittedAt != null)
              Text(
                'Ngày nộp: ${dossier.submittedAt!.day}/${dossier.submittedAt!.month}/${dossier.submittedAt!.year}',
              ),
            if (dossier.rejectionReason != null) ...[
              const SizedBox(height: 8),
              Text(
                'Lý do từ chối: ${dossier.rejectionReason}',
                style: const TextStyle(color: Colors.red),
              ),
            ],
            if (dossier.totalSteps > 0) ...[
              const SizedBox(height: 12),
              LinearProgressIndicator(
                value: dossier.progressFraction,
                minHeight: 6,
                borderRadius: BorderRadius.circular(3),
                backgroundColor: Colors.grey.shade200,
                valueColor: AlwaysStoppedAnimation<Color>(statusColor),
              ),
              const SizedBox(height: 4),
              Text(
                '${dossier.completedSteps}/${dossier.totalSteps} bước hoàn thành',
                style: const TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
