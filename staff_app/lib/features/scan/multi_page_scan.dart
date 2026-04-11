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
    return Scaffold(
      appBar: AppBar(
        title: Text('Pages (${_pages.length})'),
        actions: [
          if (_pages.isNotEmpty)
            TextButton(
              onPressed: _finalize,
              child: const Text('Done', style: TextStyle(color: Colors.white)),
            ),
        ],
      ),
      body: _pages.isEmpty
          ? const Center(child: Text('No pages scanned yet. Tap + to add.'))
          : ReorderableListView.builder(
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
                  title: Text('Page ${index + 1}'),
                  trailing: IconButton(
                    icon: const Icon(Icons.delete),
                    onPressed: () => _removePage(index),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(
        onPressed: _addPage,
        child: const Icon(Icons.add_a_photo),
      ),
    );
  }
}
