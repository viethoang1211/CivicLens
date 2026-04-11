import 'dart:io';
import 'dart:convert';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:path_provider/path_provider.dart';

class PendingScan {
  final String localId;
  final String submissionId;
  final int pageNumber;
  final String localImagePath;
  String status; // captured, uploading, synced

  PendingScan({
    required this.localId,
    required this.submissionId,
    required this.pageNumber,
    required this.localImagePath,
    this.status = 'captured',
  });

  Map<String, dynamic> toJson() => {
        'local_id': localId,
        'submission_id': submissionId,
        'page_number': pageNumber,
        'local_image_path': localImagePath,
        'status': status,
      };

  factory PendingScan.fromJson(Map<String, dynamic> json) => PendingScan(
        localId: json['local_id'],
        submissionId: json['submission_id'],
        pageNumber: json['page_number'],
        localImagePath: json['local_image_path'],
        status: json['status'],
      );
}

class OfflineQueue {
  static const _storage = FlutterSecureStorage();
  static const _queueKey = 'offline_scan_queue';

  static Future<List<PendingScan>> getQueue() async {
    final raw = await _storage.read(key: _queueKey);
    if (raw == null || raw.isEmpty) return [];
    final list = jsonDecode(raw) as List;
    return list.map((e) => PendingScan.fromJson(e)).toList();
  }

  static Future<void> _saveQueue(List<PendingScan> queue) async {
    final json = jsonEncode(queue.map((e) => e.toJson()).toList());
    await _storage.write(key: _queueKey, value: json);
  }

  static Future<String> saveImageLocally(String submissionId, int pageNumber, List<int> imageBytes) async {
    final dir = await getApplicationDocumentsDirectory();
    final path = '${dir.path}/scans/${submissionId}_page_$pageNumber.jpg';
    final file = File(path);
    await file.parent.create(recursive: true);
    await file.writeAsBytes(imageBytes);
    return path;
  }

  static Future<void> enqueue(PendingScan scan) async {
    final queue = await getQueue();
    queue.add(scan);
    await _saveQueue(queue);
  }

  static Future<void> markSynced(String localId) async {
    final queue = await getQueue();
    queue.removeWhere((s) => s.localId == localId);
    await _saveQueue(queue);
  }

  static Future<List<PendingScan>> getPending() async {
    final queue = await getQueue();
    return queue.where((s) => s.status == 'captured').toList();
  }
}
