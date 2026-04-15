import 'dart:io';
import 'package:flutter/material.dart';
import 'scan_screen.dart';

class MultiPageScan extends StatefulWidget {
  final String submissionId;

  const MultiPageScan({super.key, required this.submissionId});

  @override
  State<MultiPageScan> createState() => _MultiPageScanState();
}

class _MultiPageScanState extends State<MultiPageScan> {
  final List<File> _pages = [];

  Future<void> _addPage() async {
    final result = await Navigator.of(context).push<File>(
      MaterialPageRoute(builder: (_) => const ScanScreen()),
    );
    if (result != null) {
      setState(() {
        _pages.add(result);
      });
    }
  }

  void _removePage(int index) {
    setState(() {
      _pages.removeAt(index);
    });
  }

  void _reorderPages(int oldIndex, int newIndex) {
    setState(() {
      if (newIndex > oldIndex) newIndex -= 1;
      final page = _pages.removeAt(oldIndex);
      _pages.insert(newIndex, page);
    });
  }

  void _finalize() {
    Navigator.of(context).pop(_pages);
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: Text('Trang đã chụp (${_pages.length})'),
      ),
      body: Column(
        children: [
          Expanded(
            child: _pages.isEmpty
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.document_scanner_outlined, size: 64, color: Colors.grey.shade300),
                        const SizedBox(height: 12),
                        const Text(
                          'Chưa có trang nào.\nNhấn nút camera để chụp.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: Colors.grey, fontSize: 15),
                        ),
                      ],
                    ),
                  )
                : ReorderableListView.builder(
                    itemCount: _pages.length,
                    onReorder: _reorderPages,
                    itemBuilder: (context, index) {
                      return ListTile(
                        key: ValueKey(index),
                        leading: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: SizedBox(
                            width: 50,
                            height: 50,
                            child: Image.file(_pages[index], fit: BoxFit.cover),
                          ),
                        ),
                        title: Text('Trang ${index + 1}'),
                        trailing: IconButton(
                          icon: const Icon(Icons.delete_outline, color: Colors.red),
                          onPressed: () => _removePage(index),
                        ),
                      );
                    },
                  ),
          ),
          if (_pages.isNotEmpty)
            SafeArea(
              child: Padding(
                padding: const EdgeInsets.fromLTRB(20, 8, 20, 16),
                child: SizedBox(
                  width: double.infinity,
                  height: 52,
                  child: FilledButton.icon(
                    onPressed: _finalize,
                    icon: const Icon(Icons.check_circle_outline),
                    label: Text(
                      'Hoàn tất (${_pages.length} trang)',
                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
                    ),
                  ),
                ),
              ),
            ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _addPage,
        icon: const Icon(Icons.add_a_photo),
        label: const Text('Chụp thêm'),
      ),
    );
  }
}
