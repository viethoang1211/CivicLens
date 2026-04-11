import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

/// Shows full progress tracking for a citizen's dossier.
class DossierStatusScreen extends StatefulWidget {
  final String dossierId;
  final CitizenDossierApi citizenDossierApi;

  const DossierStatusScreen({
    super.key,
    required this.dossierId,
    required this.citizenDossierApi,
  });

  @override
  State<DossierStatusScreen> createState() => _DossierStatusScreenState();
}

class _DossierStatusScreenState extends State<DossierStatusScreen> {
  DossierTrackingDto? _dossier;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDossier();
  }

  Future<void> _loadDossier() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final dossier = await widget.citizenDossierApi.getDossier(widget.dossierId);
      setState(() {
        _dossier = dossier;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Trạng thái hồ sơ'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadDossier),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? _buildError()
              : _buildContent(),
    );
  }

  Widget _buildError() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 16),
          Text(_error!, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: _loadDossier, child: const Text('Thử lại')),
        ],
      ),
    );
  }

  Widget _buildContent() {
    final dossier = _dossier!;
    final statusColor = dossier.isCompleted
        ? Colors.green
        : dossier.isRejected
            ? Colors.red
            : Colors.blue;

    return RefreshIndicator(
      onRefresh: _loadDossier,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Status card
          Card(
            color: statusColor.withOpacity(0.08),
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
                        size: 32,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              dossier.statusLabelVi,
                              style: TextStyle(
                                fontSize: 18,
                                fontWeight: FontWeight.bold,
                                color: statusColor,
                              ),
                            ),
                            Text(
                              dossier.caseTypeName,
                              style: const TextStyle(color: Colors.grey),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  if (dossier.referenceNumber != null) ...[
                    const SizedBox(height: 12),
                    const Divider(),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Text('Mã tham chiếu: ', style: TextStyle(fontWeight: FontWeight.bold)),
                        SelectableText(dossier.referenceNumber!),
                      ],
                    ),
                  ],
                  if (dossier.rejectionReason != null) ...[
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: Colors.red.shade50,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Icon(Icons.info_outline, color: Colors.red, size: 16),
                          const SizedBox(width: 8),
                          Expanded(child: Text(dossier.rejectionReason!)),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Progress bar
          if (dossier.totalSteps > 0) ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text('Tiến độ xử lý', style: TextStyle(fontWeight: FontWeight.w600)),
                Text('${dossier.completedSteps}/${dossier.totalSteps} bước'),
              ],
            ),
            const SizedBox(height: 8),
            LinearProgressIndicator(
              value: dossier.progressFraction,
              minHeight: 8,
              borderRadius: BorderRadius.circular(4),
              backgroundColor: Colors.grey.shade200,
              valueColor: AlwaysStoppedAnimation<Color>(statusColor),
            ),
            const SizedBox(height: 16),
          ],
          // Step-by-step list
          if (dossier.steps.isNotEmpty) ...[
            const Text('Chi tiết từng bước:', style: TextStyle(fontWeight: FontWeight.w600)),
            const SizedBox(height: 8),
            for (final step in dossier.steps) _buildStepTile(step),
          ],
        ],
      ),
    );
  }

  Widget _buildStepTile(DossierTrackingStepDto step) {
    final isCompleted = step.status == 'completed';
    final isActive = step.status == 'in_progress';

    final icon = isCompleted
        ? Icons.check_circle
        : isActive
            ? Icons.play_circle
            : Icons.radio_button_unchecked;
    final color = isCompleted
        ? Colors.green
        : isActive
            ? Colors.blue
            : Colors.grey;

    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              Icon(icon, color: color, size: 24),
              if (step != _dossier!.steps.last)
                Container(width: 2, height: 32, color: Colors.grey.shade300),
            ],
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(top: 4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Bước ${step.stepOrder}: ${step.departmentName}',
                    style: const TextStyle(fontWeight: FontWeight.w500),
                  ),
                  if (isActive)
                    const Text('Đang xử lý', style: TextStyle(color: Colors.blue, fontSize: 12)),
                  if (isCompleted && step.completedAt != null)
                    Text(
                      'Hoàn thành: ${_formatDate(step.completedAt!)}',
                      style: const TextStyle(color: Colors.green, fontSize: 12),
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  String _formatDate(DateTime dt) {
    return '${dt.day}/${dt.month}/${dt.year}';
  }
}
