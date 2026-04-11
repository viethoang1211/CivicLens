import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

class ReviewActionSheet extends StatefulWidget {
  final ApiClient apiClient;
  final String stepId;
  final VoidCallback? onCompleted;

  const ReviewActionSheet({
    super.key,
    required this.apiClient,
    required this.stepId,
    this.onCompleted,
  });

  @override
  State<ReviewActionSheet> createState() => _ReviewActionSheetState();
}

class _ReviewActionSheetState extends State<ReviewActionSheet> {
  final _commentController = TextEditingController();
  bool _targetCitizen = false;
  bool _submitting = false;

  Future<void> _submit(String result) async {
    final comment = _commentController.text.trim();
    if (comment.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a comment')),
      );
      return;
    }

    setState(() => _submitting = true);
    try {
      await widget.apiClient.post(
        '/v1/staff/workflow-steps/${widget.stepId}/complete',
        data: {
          'result': result,
          'comment': comment,
          'target_citizen': _targetCitizen,
        },
      );
      if (mounted) {
        Navigator.of(context).pop();
        widget.onCompleted?.call();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  @override
  void dispose() {
    _commentController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16, right: 16, top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Review Decision', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 16),
          TextField(
            controller: _commentController,
            decoration: const InputDecoration(
              labelText: 'Comment / Annotation',
              border: OutlineInputBorder(),
            ),
            maxLines: 3,
          ),
          const SizedBox(height: 8),
          SwitchListTile(
            title: const Text('Visible to citizen'),
            value: _targetCitizen,
            onChanged: (v) => setState(() => _targetCitizen = v),
            contentPadding: EdgeInsets.zero,
          ),
          const SizedBox(height: 12),
          if (_submitting)
            const Center(child: CircularProgressIndicator())
          else
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => _submit('rejected'),
                    style: OutlinedButton.styleFrom(foregroundColor: Colors.red),
                    child: const Text('Reject'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => _submit('needs_info'),
                    style: OutlinedButton.styleFrom(foregroundColor: Colors.orange),
                    child: const Text('Need Info'),
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () => _submit('approved'),
                    style: ElevatedButton.styleFrom(backgroundColor: Colors.green),
                    child: const Text('Approve'),
                  ),
                ),
              ],
            ),
        ],
      ),
    );
  }
}
