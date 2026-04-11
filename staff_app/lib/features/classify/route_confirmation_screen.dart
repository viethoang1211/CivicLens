import 'package:flutter/material.dart';

class RouteConfirmationScreen extends StatelessWidget {
  final String submissionId;
  final List<Map<String, dynamic>> workflowSteps;

  const RouteConfirmationScreen({
    super.key,
    required this.submissionId,
    required this.workflowSteps,
  });

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Confirm Routing')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Proposed Department Workflow:',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            Expanded(
              child: ListView.builder(
                itemCount: workflowSteps.length,
                itemBuilder: (context, index) {
                  final step = workflowSteps[index];
                  return Card(
                    child: ListTile(
                      leading: CircleAvatar(child: Text('${index + 1}')),
                      title: Text(step['department'] ?? ''),
                      subtitle: Text('Status: ${step['status'] ?? 'pending'}'),
                      trailing: index == 0
                          ? const Chip(label: Text('First', style: TextStyle(fontSize: 12)))
                          : null,
                    ),
                  );
                },
              ),
            ),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () => Navigator.of(context).pop(true),
                child: const Text('Confirm & Route'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
