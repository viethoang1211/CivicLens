class SearchResult {
  final String type;
  final String id;
  final String status;
  final DateTime? submittedAt;
  final String? citizenName;
  final String? documentTypeName;
  final String? documentTypeCode;
  final String? caseTypeName;
  final String? caseTypeCode;
  final String? referenceNumber;
  final String? aiSummary;
  final bool aiSummaryIsAiGenerated;
  final double relevanceScore;
  final String highlight;

  SearchResult({
    required this.type,
    required this.id,
    required this.status,
    this.submittedAt,
    this.citizenName,
    this.documentTypeName,
    this.documentTypeCode,
    this.caseTypeName,
    this.caseTypeCode,
    this.referenceNumber,
    this.aiSummary,
    this.aiSummaryIsAiGenerated = false,
    this.relevanceScore = 0.0,
    this.highlight = '',
  });

  factory SearchResult.fromJson(Map<String, dynamic> json) {
    return SearchResult(
      type: json['type'],
      id: json['id'],
      status: json['status'],
      submittedAt: json['submitted_at'] != null
          ? DateTime.parse(json['submitted_at'])
          : null,
      citizenName: json['citizen_name'],
      documentTypeName: json['document_type_name'],
      documentTypeCode: json['document_type_code'],
      caseTypeName: json['case_type_name'],
      caseTypeCode: json['case_type_code'],
      referenceNumber: json['reference_number'],
      aiSummary: json['ai_summary'],
      aiSummaryIsAiGenerated: json['ai_summary_is_ai_generated'] ?? false,
      relevanceScore: (json['relevance_score'] ?? 0.0).toDouble(),
      highlight: json['highlight'] ?? '',
    );
  }
}

class SearchPagination {
  final int page;
  final int perPage;
  final int total;
  final int totalPages;

  SearchPagination({
    required this.page,
    required this.perPage,
    required this.total,
    required this.totalPages,
  });

  factory SearchPagination.fromJson(Map<String, dynamic> json) {
    return SearchPagination(
      page: json['page'],
      perPage: json['per_page'],
      total: json['total'],
      totalPages: json['total_pages'],
    );
  }
}

class SearchResponse {
  final List<SearchResult> results;
  final SearchPagination pagination;
  final String query;

  SearchResponse({
    required this.results,
    required this.pagination,
    required this.query,
  });

  factory SearchResponse.fromJson(Map<String, dynamic> json) {
    return SearchResponse(
      results: (json['results'] as List)
          .map((r) => SearchResult.fromJson(r))
          .toList(),
      pagination: SearchPagination.fromJson(json['pagination']),
      query: json['query'],
    );
  }
}
