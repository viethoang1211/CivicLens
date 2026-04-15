import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

class SearchScreen extends StatefulWidget {
  final SearchApiClient searchApiClient;

  const SearchScreen({super.key, required this.searchApiClient});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _searchController = TextEditingController();
  SearchResponse? _response;
  bool _loading = false;
  String? _error;

  // Filters
  String? _statusFilter;
  String? _documentTypeFilter;

  Future<void> _performSearch({int page = 1}) async {
    final query = _searchController.text.trim();
    if (query.length < 2) return;

    setState(() {
      _loading = true;
      _error = null;
    });

    try {
      final response = await widget.searchApiClient.search(
        query,
        status: _statusFilter,
        documentTypeCode: _documentTypeFilter,
        page: page,
      );
      setState(() {
        _response = response;
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Lỗi tìm kiếm: $e';
        _loading = false;
      });
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Tìm kiếm'),
      ),
      body: Column(
        children: [
          // Search bar
          Padding(
            padding: const EdgeInsets.all(16.0),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Nhập từ khóa tìm kiếm (tối thiểu 2 ký tự)...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () {
                    _searchController.clear();
                    setState(() {
                      _response = null;
                    });
                  },
                ),
                border: const OutlineInputBorder(),
              ),
              onSubmitted: (_) => _performSearch(),
            ),
          ),

          // Filter chips
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16.0),
            child: Wrap(
              spacing: 8.0,
              children: [
                FilterChip(
                  label: const Text('Hoàn thành'),
                  selected: _statusFilter == 'completed',
                  onSelected: (selected) {
                    setState(() {
                      _statusFilter = selected ? 'completed' : null;
                    });
                    if (_searchController.text.trim().length >= 2) {
                      _performSearch();
                    }
                  },
                ),
                FilterChip(
                  label: const Text('Đang xử lý'),
                  selected: _statusFilter == 'in_progress',
                  onSelected: (selected) {
                    setState(() {
                      _statusFilter = selected ? 'in_progress' : null;
                    });
                    if (_searchController.text.trim().length >= 2) {
                      _performSearch();
                    }
                  },
                ),
                FilterChip(
                  label: const Text('Chờ xử lý'),
                  selected: _statusFilter == 'pending',
                  onSelected: (selected) {
                    setState(() {
                      _statusFilter = selected ? 'pending' : null;
                    });
                    if (_searchController.text.trim().length >= 2) {
                      _performSearch();
                    }
                  },
                ),
              ],
            ),
          ),

          const SizedBox(height: 8),

          // Results
          Expanded(
            child: _buildResultsList(),
          ),
        ],
      ),
    );
  }

  Widget _buildResultsList() {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    if (_error != null) {
      return Center(child: Text(_error!, style: const TextStyle(color: Colors.red)));
    }

    if (_response == null) {
      return const Center(
        child: Text('Nhập từ khóa để bắt đầu tìm kiếm', style: TextStyle(color: Colors.grey)),
      );
    }

    if (_response!.results.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.search_off, size: 48, color: Colors.grey),
            SizedBox(height: 16),
            Text('Không tìm thấy kết quả', style: TextStyle(fontSize: 16, color: Colors.grey)),
            SizedBox(height: 8),
            Text('Thử mở rộng từ khóa tìm kiếm', style: TextStyle(color: Colors.grey)),
          ],
        ),
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16.0),
          child: Text(
            'Tìm thấy ${_response!.pagination.total} kết quả',
            style: const TextStyle(color: Colors.grey),
          ),
        ),
        Expanded(
          child: ListView.builder(
            itemCount: _response!.results.length,
            itemBuilder: (context, index) {
              final result = _response!.results[index];
              return _SearchResultCard(result: result);
            },
          ),
        ),
        if (_response!.pagination.totalPages > 1)
          _buildPagination(),
      ],
    );
  }

  Widget _buildPagination() {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(
            icon: const Icon(Icons.chevron_left),
            onPressed: _response!.pagination.page > 1
                ? () => _performSearch(page: _response!.pagination.page - 1)
                : null,
          ),
          Text('Trang ${_response!.pagination.page}/${_response!.pagination.totalPages}'),
          IconButton(
            icon: const Icon(Icons.chevron_right),
            onPressed: _response!.pagination.page < _response!.pagination.totalPages
                ? () => _performSearch(page: _response!.pagination.page + 1)
                : null,
          ),
        ],
      ),
    );
  }
}

class _SearchResultCard extends StatelessWidget {
  final SearchResult result;

  const _SearchResultCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final isSubmission = result.type == 'submission';

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16.0, vertical: 4.0),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: isSubmission ? Colors.blue.shade100 : Colors.green.shade100,
          child: Icon(
            isSubmission ? Icons.description : Icons.folder,
            color: isSubmission ? Colors.blue : Colors.green,
          ),
        ),
        title: Row(
          children: [
            Expanded(
              child: Text(
                result.citizenName ?? '',
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: isSubmission ? Colors.blue.shade50 : Colors.green.shade50,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                isSubmission ? 'Hồ sơ đơn' : 'Hồ sơ vụ',
                style: TextStyle(
                  fontSize: 12,
                  color: isSubmission ? Colors.blue : Colors.green,
                ),
              ),
            ),
          ],
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              isSubmission
                  ? (result.documentTypeName ?? '')
                  : (result.caseTypeName ?? ''),
              style: const TextStyle(fontSize: 13),
            ),
            if (result.aiSummary != null) ...[
              const SizedBox(height: 4),
              Row(
                children: [
                  if (result.aiSummaryIsAiGenerated)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                      margin: const EdgeInsets.only(right: 4),
                      decoration: BoxDecoration(
                        color: Colors.purple.shade50,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text(
                        'AI tạo',
                        style: TextStyle(fontSize: 10, color: Colors.purple),
                      ),
                    ),
                  Expanded(
                    child: Text(
                      result.aiSummary!,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontSize: 12, color: Colors.black54),
                    ),
                  ),
                ],
              ),
            ],
          ],
        ),
        isThreeLine: result.aiSummary != null,
      ),
    );
  }
}
