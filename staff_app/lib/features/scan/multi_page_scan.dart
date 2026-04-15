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
        title: Text('Trang đã quét (${_pages.length})'),
      ),
      body: _pages.isEmpty
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.document_scanner_outlined, size: 64, color: cs.onSurface.withAlpha(100)),
                  const SizedBox(height: 16),
                  Text('Chưa có trang nào. Nhấn + để quét.', style: TextStyle(color: cs.onSurface.withAlpha(150))),
                ],
              ),
            )
          : Column(
              children: [
                Expanded(
                  child: ReorderableListView.builder(
                    itemCount: _pages.length,
                    onReorder: _reorderPages,
                    itemBuilder: (context, index) {
                      return ListTile(
                        key: ValueKey(index),
                        leading: SizedBox(
                          width: 50,
                          height: 50,
                          child: Image.file(_pages[index], fit: BoxFit.cover),
                        ),
                        title: Text('Trang ${index + 1}'),
                        trailing: IconButton(
                          icon: const Icon(Icons.delete),
                          onPressed: () => _removePage(index),
                        ),
                      );
                    },
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: FilledButton.icon(
                      onPressed: _finalize,
                      icon: const Icon(Icons.check_circle_outline),
                      label: Text('Hoàn tất (${_pages.length} trang)', style: const TextStyle(fontSize: 16)),
                      style: FilledButton.styleFrom(
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      ),
                    ),
                  ),
                ),
              ],
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addPage,
        child: const Icon(Icons.add_a_photo),
      ),
    );
  }
}
