import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:shared_dart/shared_dart.dart';

/// Manages push notification registration and handling via Alibaba Cloud EMAS.
///
/// In production, this would integrate with the aliyun_push SDK.
/// Currently provides the interface with placeholder implementations.
class PushService {
  final ApiClient _apiClient;
  String? _deviceToken;
  final StreamController<Map<String, dynamic>> _messageController =
      StreamController<Map<String, dynamic>>.broadcast();

  PushService({required ApiClient apiClient}) : _apiClient = apiClient;

  Stream<Map<String, dynamic>> get onMessage => _messageController.stream;
  String? get deviceToken => _deviceToken;

  /// Initialize push SDK and register for notifications.
  Future<void> initialize() async {
    try {
      // In production: call aliyun_push init with app key/secret
      // final result = await AliyunPush.initPush(appKey: '...', appSecret: '...');
      _deviceToken = 'emas-placeholder-token-${DateTime.now().millisecondsSinceEpoch}';
      debugPrint('PushService: initialized with token $_deviceToken');
    } catch (e) {
      debugPrint('PushService: initialization failed: $e');
    }
  }

  /// Register device token with backend for targeted push delivery.
  Future<void> registerToken() async {
    if (_deviceToken == null) return;
    try {
      await _apiClient.put('/v1/citizen/push-token', data: {'token': _deviceToken});
      debugPrint('PushService: token registered with backend');
    } catch (e) {
      debugPrint('PushService: token registration failed: $e');
    }
  }

  /// Handle foreground push message.
  void onForegroundMessage(Map<String, dynamic> message) {
    debugPrint('PushService: foreground message received');
    _messageController.add(message);
  }

  /// Handle background/terminated push message tap.
  void onMessageTap(Map<String, dynamic> message) {
    debugPrint('PushService: message tap received');
    _messageController.add({...message, '_tapped': true});
  }

  /// Dispose resources.
  void dispose() {
    _messageController.close();
  }
}
