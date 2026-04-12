import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

/// Screen that lets a staff member pick a case type to create a new dossier.
class CaseTypeSelectorScreen extends StatefulWidget {
  final DossierApi dossierApi;
  final int staffClearanceLevel;

  const CaseTypeSelectorScreen({
    super.key,
    required this.dossierApi,
    this.staffClearanceLevel = 0,
  });

  @override
  State<CaseTypeSelectorScreen> createState() => _CaseTypeSelectorScreenState();
}

class _CaseTypeSelectorScreenState extends State<CaseTypeSelectorScreen> {
  List<CaseTypeDto> _caseTypes = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadCaseTypes();
  }

  Future<void> _loadCaseTypes() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final types = await widget.dossierApi.listCaseTypes(activeOnly: true);
      setState(() {
        _caseTypes = types;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  void _selectCaseType(CaseTypeDto caseType) {
    Navigator.of(context).pop(caseType);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Chọn loại hồ sơ')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline, size: 48, color: Colors.red),
                      const SizedBox(height: 16),
                      Text(_error!, textAlign: TextAlign.center),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadCaseTypes,
                        child: const Text('Thử lại'),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadCaseTypes,
                  child: ListView.separated(
                    padding: const EdgeInsets.all(16),
                    itemCount: _caseTypes.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final ct = _caseTypes[index];
                      return Card(
                        child: ListTile(
                          onTap: () => _selectCaseType(ct),
                          title: Text(ct.name, style: const TextStyle(fontWeight: FontWeight.bold)),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              if (ct.description != null) ...[
                                const SizedBox(height: 4),
                                Text(ct.description!),
                              ],
                              const SizedBox(height: 4),
                              Text(
                                '${ct.requirementGroups.length} nhóm tài liệu • '
                                '${ct.routingSteps.length} bước xử lý',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                          trailing: const Icon(Icons.chevron_right),
                        ),
                      );
                    },
                  ),
                ),
    );
  }
}
