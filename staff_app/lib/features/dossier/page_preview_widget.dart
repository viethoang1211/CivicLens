import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

/// Horizontal scrollable row of page thumbnails for a captured document.
/// Supports tap-to-enlarge and delete actions per page.
class PagePreviewWidget extends StatelessWidget {
  final DossierDocumentDto document;
  final VoidCallback? onDelete;

  const PagePreviewWidget({
    super.key,
    required this.document,
    this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    if (document.pageCount == 0) return const SizedBox.shrink();

    return SizedBox(
      height: 80,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: document.pageCount,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          return _PageThumbnail(
            pageNumber: index + 1,
            onDelete: index == 0 && document.pageCount == 1 ? onDelete : null,
          );
        },
      ),
    );
  }
}

class _PageThumbnail extends StatelessWidget {
  final int pageNumber;
  final VoidCallback? onDelete;

  const _PageThumbnail({required this.pageNumber, this.onDelete});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 60,
      decoration: BoxDecoration(
        border: Border.all(color: Colors.grey.shade300),
        borderRadius: BorderRadius.circular(6),
        color: Colors.grey.shade100,
      ),
      child: Stack(
        children: [
          Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.description, size: 24, color: Colors.grey.shade500),
                Text(
                  'Tr. $pageNumber',
                  style: TextStyle(fontSize: 10, color: Colors.grey.shade600),
                ),
              ],
            ),
          ),
          if (onDelete != null)
            Positioned(
              top: 0,
              right: 0,
              child: GestureDetector(
                onTap: onDelete,
                child: Container(
                  padding: const EdgeInsets.all(2),
                  decoration: const BoxDecoration(
                    color: Colors.red,
                    borderRadius: BorderRadius.only(
                      topRight: Radius.circular(6),
                      bottomLeft: Radius.circular(6),
                    ),
                  ),
                  child: const Icon(Icons.close, size: 12, color: Colors.white),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
