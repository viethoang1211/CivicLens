import 'package:shared_dart/src/api/api_client.dart';
import 'package:shared_dart/src/models/search_result.dart';
import 'package:shared_dart/src/models/sla_metrics.dart';

class SearchApiClient {
  final ApiClient _apiClient;

  SearchApiClient(this._apiClient);

  Future<SearchResponse> search(
    String query, {
    String? status,
    String? documentTypeCode,
    String? caseTypeCode,
    String? departmentId,
    String? dateFrom,
    String? dateTo,
    String sort = 'relevance',
    int page = 1,
    int perPage = 20,
  }) async {
    final params = <String, dynamic>{
      'q': query,
      if (status != null) 'status': status,
      if (documentTypeCode != null) 'document_type_code': documentTypeCode,
      if (caseTypeCode != null) 'case_type_code': caseTypeCode,
      if (departmentId != null) 'department_id': departmentId,
      if (dateFrom != null) 'date_from': dateFrom,
      if (dateTo != null) 'date_to': dateTo,
      'sort': sort,
      'page': page,
      'per_page': perPage,
    };

    final response = await _apiClient.get(
      '/v1/staff/search',
      queryParameters: params,
    );
    return SearchResponse.fromJson(response.data);
  }

  Future<SlaMetricsResponse> getSlaMetrics({
    String? dateFrom,
    String? dateTo,
    String? departmentId,
  }) async {
    final params = <String, dynamic>{
      if (dateFrom != null) 'date_from': dateFrom,
      if (dateTo != null) 'date_to': dateTo,
      if (departmentId != null) 'department_id': departmentId,
    };

    final response = await _apiClient.get(
      '/v1/staff/analytics/sla',
      queryParameters: params,
    );
    return SlaMetricsResponse.fromJson(response.data);
  }
}
