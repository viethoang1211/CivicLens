import 'package:flutter/material.dart';

class OcrReviewScreen extends StatefulWidget {
  final String submissionId;
  final List<Map<String, dynamic>> pages;

  const OcrReviewScreen({super.key, required this.submissionId, required this.pages});

  @override
  State<OcrReviewScreen> createState() => _OcrReviewScreenState();
}

class _OcrReviewScreenState extends State<OcrReviewScreen> {
  late List<TextEditingController> _controllers;
  int _currentPage = 0;

  @override
  void initState() {
    super.initState();
    _controllers = widget.pages.map((p) {
      return TextEditingController(text: p['ocr_raw_text'] ?? '');
    }).toList();
  }

  @override
  void dispose() {
    for (final c in _controllers) {
      c.dispose();
    }
    super.dispose();
  }

  void _submitCorrections() {
    final corrections = <Map<String, dynamic>>[];
    for (int i = 0; i < widget.pages.length; i++) {
      if (_controllers[i].text != widget.pages[i]['ocr_raw_text']) {
        corrections.add({
          'page_number': widget.pages[i]['page_number'],
          'corrected_text': _controllers[i].text,
        });
      }
    }
    Navigator.of(context).pop(corrections);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('OCR Review - Page ${_currentPage + 1}/${widget.pages.length}'),
        actions: [
          TextButton(
            onPressed: _submitCorrections,
            child: const Text('Submit', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: Column(
        children: [
          // Page navigation
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              IconButton(
                onPressed: _currentPage > 0 ? () => setState(() => _currentPage--) : null,
                icon: const Icon(Icons.arrow_back),
              ),
              Text('Page ${_currentPage + 1} of ${widget.pages.length}'),
              IconButton(
                onPressed: _currentPage < widget.pages.length - 1
                    ? () => setState(() => _currentPage++)
                    : null,
                icon: const Icon(Icons.arrow_forward),
              ),
            ],
          ),
          // Confidence indicator
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              children: [
                const Text('Confidence: '),
                Text(
                  '${((widget.pages[_currentPage]['ocr_confidence'] ?? 0) * 100).toStringAsFixed(0)}%',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: (widget.pages[_currentPage]['ocr_confidence'] ?? 0) >= 0.7
                        ? Colors.green
                        : Colors.orange,
                  ),
                ),
              ],
            ),
          ),
          const Divider(),
          // Editable text
          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                controller: _controllers[_currentPage],
                maxLines: null,
                expands: true,
                textAlignVertical: TextAlignVertical.top,
                decoration: const InputDecoration(
                  border: OutlineInputBorder(),
                  hintText: 'OCR extracted text',
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
