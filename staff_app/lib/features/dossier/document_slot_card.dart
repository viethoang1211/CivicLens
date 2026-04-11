import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_dart/shared_dart.dart';

/// Card widget for a single document requirement group.
/// Shows which slots are in the group and lets staff upload / delete documents.
class DocumentSlotCard extends StatefulWidget {
  final DocumentRequirementGroupDto group;
  final List<DossierDocumentDto> uploadedDocuments;
  final String dossierId;
  final DossierApi dossierApi;
  final VoidCallback onDocumentUploaded;
  final VoidCallback onDocumentDeleted;

  const DocumentSlotCard({
    super.key,
    required this.group,
    required this.uploadedDocuments,
    required this.dossierId,
    required this.dossierApi,
    required this.onDocumentUploaded,
    required this.onDocumentDeleted,
  });

  @override
  State<DocumentSlotCard> createState() => _DocumentSlotCardState();
}

class _DocumentSlotCardState extends State<DocumentSlotCard> {
  final ImagePicker _picker = ImagePicker();
  bool _uploading = false;

  bool get _isFulfilled => widget.group.isFulfilled;

  Future<void> _pickAndUpload(DocumentRequirementSlotDto slot) async {
    final source = await showModalBottomSheet<ImageSource>(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Chụp ảnh'),
              onTap: () => Navigator.pop(ctx, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Chọn từ thư viện'),
              onTap: () => Navigator.pop(ctx, ImageSource.gallery),
            ),
          ],
        ),
      ),
    );
    if (source == null) return;

    final XFile? photo = await _picker.pickImage(
      source: source,
      imageQuality: 90,
    );
    if (photo == null) return;

    setState(() => _uploading = true);
    try {
      await widget.dossierApi.uploadDocument(
        dossierId: widget.dossierId,
        requirementSlotId: slot.id,
        pages: [File(photo.path)],
      );
      if (mounted) widget.onDocumentUploaded();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi tải lên: ${e.toString()}')),
        );
      }
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  Future<void> _deleteDocument(DossierDocumentDto doc) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Xoá tài liệu'),
        content: const Text('Bạn có chắc chắn muốn xoá tài liệu này?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Huỷ')),
          TextButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('Xoá'),
          ),
        ],
      ),
    );
    if (confirm != true) return;

    try {
      await widget.dossierApi.deleteDocument(
        dossierId: widget.dossierId,
        documentId: doc.id,
      );
      widget.onDocumentDeleted();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi xoá: ${e.toString()}')),
        );
      }
    }
  }

  Future<void> _overrideAi(DossierDocumentDto doc) async {
    final notesController = TextEditingController();
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Ghi đè kết quả AI'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Xác nhận tài liệu này đáp ứng yêu cầu, bỏ qua kết quả AI.'),
            const SizedBox(height: 12),
            TextField(
              controller: notesController,
              decoration: const InputDecoration(
                labelText: 'Ghi chú (tuỳ chọn)',
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Huỷ')),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Xác nhận'),
          ),
        ],
      ),
    );
    if (confirm != true) return;

    try {
      await widget.dossierApi.overrideAiDecision(
        dossierId: widget.dossierId,
        documentId: doc.id,
        staffNotes: notesController.text.trim().isEmpty ? null : notesController.text.trim(),
      );
      widget.onDocumentUploaded();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi: ${e.toString()}')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final borderColor = _isFulfilled
        ? Colors.green
        : widget.group.isMandatory
            ? Colors.red.shade200
            : Colors.grey.shade300;

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: borderColor, width: 1.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: _isFulfilled
                  ? Colors.green.shade50
                  : widget.group.isMandatory
                      ? Colors.red.shade50
                      : Colors.grey.shade50,
              borderRadius: const BorderRadius.vertical(top: Radius.circular(8)),
            ),
            child: Row(
              children: [
                Icon(
                  _isFulfilled ? Icons.check_circle : Icons.radio_button_unchecked,
                  color: _isFulfilled ? Colors.green : Colors.grey,
                  size: 20,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    widget.group.label,
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                ),
                if (!widget.group.isMandatory)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.grey.shade200,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: const Text('Tuỳ chọn', style: TextStyle(fontSize: 11)),
                  ),
              ],
            ),
          ),
          // Fulfilled doc (if any)
          if (widget.uploadedDocuments.isNotEmpty) ...[
            for (final doc in widget.uploadedDocuments)
              _buildUploadedDocTile(doc),
          ],
          // Slots available to upload
          if (!_isFulfilled)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    widget.group.slots.length > 1
                        ? 'Chọn một trong các loại tài liệu sau:'
                        : 'Tải lên:',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      for (final slot in widget.group.slots)
                        _uploading
                            ? const SizedBox(
                                width: 24,
                                height: 24,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : OutlinedButton.icon(
                                onPressed: () => _pickAndUpload(slot),
                                icon: const Icon(Icons.upload_file, size: 16),
                                label: Text(slot.labelOverride ?? slot.label),
                              ),
                    ],
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildUploadedDocTile(DossierDocumentDto doc) {
    final aiMatch = doc.aiMatchResult != null ? doc.aiMatch : null;
    final Color aiBadgeColor;
    final String aiBadgeText;
    final IconData aiBadgeIcon;

    if (doc.aiMatchOverridden) {
      aiBadgeColor = Colors.purple;
      aiBadgeText = 'Ghi đè';
      aiBadgeIcon = Icons.supervisor_account;
    } else if (aiMatch == null) {
      aiBadgeColor = Colors.grey;
      aiBadgeText = 'Đang xử lý...';
      aiBadgeIcon = Icons.hourglass_empty;
    } else if (aiMatch) {
      aiBadgeColor = Colors.green;
      aiBadgeText = '${(doc.aiConfidence * 100).toStringAsFixed(0)}%';
      aiBadgeIcon = Icons.verified;
    } else {
      aiBadgeColor = Colors.red;
      aiBadgeText = 'Không khớp';
      aiBadgeIcon = Icons.warning_amber;
    }

    return ListTile(
      leading: const Icon(Icons.description, color: Colors.blue),
      title: Text(doc.documentTypeName ?? 'Tài liệu'),
      subtitle: Text('${doc.pageCount} trang'),
      trailing: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          // AI badge
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
            decoration: BoxDecoration(
              color: aiBadgeColor.withOpacity(0.1),
              border: Border.all(color: aiBadgeColor),
              borderRadius: BorderRadius.circular(4),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(aiBadgeIcon, size: 12, color: aiBadgeColor),
                const SizedBox(width: 2),
                Text(aiBadgeText, style: TextStyle(fontSize: 11, color: aiBadgeColor)),
              ],
            ),
          ),
          // Overflow menu
          PopupMenuButton<String>(
            onSelected: (action) {
              if (action == 'delete') _deleteDocument(doc);
              if (action == 'override') _overrideAi(doc);
            },
            itemBuilder: (ctx) => [
              if (!doc.aiMatchOverridden && aiMatch == false)
                const PopupMenuItem(
                  value: 'override',
                  child: ListTile(
                    leading: Icon(Icons.supervisor_account),
                    title: Text('Ghi đè AI'),
                  ),
                ),
              const PopupMenuItem(
                value: 'delete',
                child: ListTile(
                  leading: Icon(Icons.delete, color: Colors.red),
                  title: Text('Xoá', style: TextStyle(color: Colors.red)),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
