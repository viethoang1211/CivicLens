import 'dart:io';
import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:workmanager/workmanager.dart';
import 'package:shared_dart/shared_dart.dart';
import 'offline_queue.dart';

const syncTaskName = 'sync_scanned_pages';

void callbackDispatcher() {
  Workmanager().executeTask((task, inputData) async {
    if (task == syncTaskName) {
      await SyncEngine.syncPendingScans();
    }
    return true;
  });
}

class SyncEngine {
  static Future<void> initialize() async {
    await Workmanager().initialize(callbackDispatcher);
    await Workmanager().registerPeriodicTask(
      'sync_scans',
      syncTaskName,
      frequency: const Duration(minutes: 15),
      constraints: Constraints(networkType: NetworkType.connected),
    );
  }

  static Future<void> syncPendingScans() async {
    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity.contains(ConnectivityResult.none)) return;

    final pending = await OfflineQueue.getPending();
    if (pending.isEmpty) return;

    final client = ApiClient(
      baseUrl: const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000'),
    );
    final api = StaffSubmissionsApi(client);

    for (final scan in pending) {
      try {
        scan.status = 'uploading';
        await api.uploadPage(
          submissionId: scan.submissionId,
          pageNumber: scan.pageNumber,
          imageFile: File(scan.localImagePath),
        );
        await OfflineQueue.markSynced(scan.localId);
      } catch (_) {
        scan.status = 'captured'; // Will retry next cycle
      }
    }
  }
}

class StaffSubmissionsApi {
  final ApiClient _client;
  StaffSubmissionsApi(this._client);

  Future<void> uploadPage({
    required String submissionId,
    required int pageNumber,
    required File imageFile,
  }) async {
    // Delegate to shared_dart API client
    final formData = {
      'page_number': pageNumber,
      'image': imageFile,
    };
    await _client.post('/v1/staff/submissions/$submissionId/pages', data: formData);
  }
}
