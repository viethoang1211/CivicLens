import 'package:flutter/material.dart';

class ManualClassifyScreen extends StatefulWidget {
  const ManualClassifyScreen({super.key});

  @override
  State<ManualClassifyScreen> createState() => _ManualClassifyScreenState();
}

class _ManualClassifyScreenState extends State<ManualClassifyScreen> {
  final _searchController = TextEditingController();
  // In production, this would be fetched from the API
  final List<Map<String, String>> _documentTypes = [];

  List<Map<String, String>> get _filtered {
    final query = _searchController.text.toLowerCase();
    if (query.isEmpty) return _documentTypes;
    return _documentTypes.where((dt) =>
        dt['name']!.toLowerCase().contains(query) ||
        dt['code']!.toLowerCase().contains(query)).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Select Document Type')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                hintText: 'Search document types...',
                prefixIcon: Icon(Icons.search),
                border: OutlineInputBorder(),
              ),
              onChanged: (_) => setState(() {}),
            ),
          ),
          Expanded(
            child: _filtered.isEmpty
                ? const Center(child: Text('No document types found'))
                : ListView.builder(
                    itemCount: _filtered.length,
                    itemBuilder: (context, index) {
                      final dt = _filtered[index];
                      return ListTile(
                        title: Text(dt['name']!),
                        subtitle: Text(dt['code']!),
                        onTap: () => Navigator.of(context).pop({
                          'document_type_id': dt['id'],
                          'classification_method': 'manual',
                        }),
                      );
                    },
                  ),
          ),
        ],
      ),
    );
  }
}
