import '../api/api_client.dart';
import '../models/dossier_tracking.dart';

/// Citizen-facing dossier tracking API client.
class CitizenDossierApi {
  final ApiClient _client;

  CitizenDossierApi(this._client);

  /// List the authenticated citizen's dossiers (requires auth token).
  Future<List<DossierTrackingListItemDto>> listMyDossiers({
    String? status,
    int page = 1,
    int pageSize = 20,
  }) async {
    final params = <String, dynamic>{'page': page, 'page_size': pageSize};
    if (status != null) params['status'] = status;

    final response = await _client.get<Map<String, dynamic>>(
      '/v1/citizen/dossiers',
      queryParameters: params,
    );
    final data = response.data as Map<String, dynamic>;
    final items = data['items'] as List<dynamic>? ?? [];
    return items
        .map((e) => DossierTrackingListItemDto.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Get full tracking detail for a specific dossier (requires auth token).
  Future<DossierTrackingDto> getDossier(String dossierId) async {
    final response = await _client.get<Map<String, dynamic>>(
      '/v1/citizen/dossiers/$dossierId',
    );
    return DossierTrackingDto.fromJson(response.data as Map<String, dynamic>);
  }

  /// Public lookup by reference number — no auth required.
  /// The returned [DossierTrackingDto] will have [id] == null to prevent enumeration.
  Future<DossierTrackingDto> lookupByReference(String referenceNumber) async {
    final response = await _client.get<Map<String, dynamic>>(
      '/v1/citizen/dossiers/lookup',
      queryParameters: {'reference_number': referenceNumber},
    );
    return DossierTrackingDto.fromJson(response.data as Map<String, dynamic>);
  }
}
