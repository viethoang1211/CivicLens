import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_dart/shared_dart.dart';
import '../../core/widgets/ai_validation_badge.dart';

/// Expandable card per requirement group in the guided capture flow.
///
/// Shows: group label, mandatory/optional badge, slot alternatives,
/// captured page thumbnails, AI validation badge, and capture button.
class CaptureStepWidget extends StatefulWidget {
  final Map<String, dynamic> group;
  final List<DossierDocumentDto> uploadedDocuments;
  final String dossierId;
  final DossierApi dossierApi;
  final VoidCallback onDocumentChanged;
  final bool initiallyExpanded;

  const CaptureStepWidget({
    super.key,
    required this.group,
    required this.uploadedDocuments,
    required this.dossierId,
    required this.dossierApi,
    required this.onDocumentChanged,
    this.initiallyExpanded = false,
  });

  @override
  State<CaptureStepWidget> createState() => _CaptureStepWidgetState();
}

class _CaptureStepWidgetState extends State<CaptureStepWidget> {
  final ImagePicker _picker = ImagePicker();
  bool _uploading = false;

  bool get _isFulfilled => widget.uploadedDocuments.isNotEmpty;
  bool get _isMandatory => widget.group['is_mandatory'] as bool? ?? true;
  List<Map<String, dynamic>> get _slots =>
      (widget.group['slots'] as List<dynamic>? ?? []).cast<Map<String, dynamic>>();

  Future<void> _captureForSlot(Map<String, dynamic> slot) async {
    final photo = await _picker.pickImage(
      source: ImageSource.camera,
      imageQuality: 90,
      preferredCameraDevice: CameraDevice.rear,
    );
    if (photo == null) return;

    setState(() => _uploading = true);
    try {
      await widget.dossierApi.uploadDocument(
        dossierId: widget.dossierId,
        requirementSlotId: slot['id'] as String,
        pages: [File(photo.path)],
      );
      widget.onDocumentChanged();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi tải lên: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  void _onCaptureTap() {
    if (_slots.length == 1) {
      _captureForSlot(_slots.first);
    } else {
      _showSlotSelector();
    }
  }

  void _showSlotSelector() {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Padding(
              padding: EdgeInsets.all(16),
              child: Text(
                'Chọn loại tài liệu',
                style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
            ),
            ..._slots.map((slot) => ListTile(
                  leading: const Icon(Icons.description),
                  title: Text(
                    (slot['label_override'] as String?) ??
                        (slot['document_type_name'] as String?) ??
                        'Tài liệu',
                  ),
                  subtitle: slot['description'] != null
                      ? Text(
                          slot['description'] as String,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        )
                      : null,
                  onTap: () {
                    Navigator.pop(ctx);
                    _captureForSlot(slot);
                  },
                )),
            const SizedBox(height: 8),
          ],
        ),
      ),
    );
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
      widget.onDocumentChanged();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi xoá: $e')),
        );
      }
    }
  }

  Future<void> _overrideAi(DossierDocumentDto doc) async {
    try {
      await widget.dossierApi.overrideAiDecision(
        dossierId: widget.dossierId,
        documentId: doc.id,
      );
      widget.onDocumentChanged();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final groupLabel = widget.group['label'] as String? ?? '';
    final groupOrder = widget.group['group_order'] as int? ?? 0;
    final borderColor = _isFulfilled
        ? Colors.green
        : _isMandatory
            ? Colors.red.shade200
            : Colors.grey.shade300;

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(color: borderColor, width: 1.5),
      ),
      child: ExpansionTile(
        initiallyExpanded: widget.initiallyExpanded || !_isFulfilled,
        leading: _buildStepIndicator(groupOrder),
        title: Row(
          children: [
            Expanded(
              child: Text(
                groupLabel,
                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
              ),
            ),
            if (!_isMandatory)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(4),
                ),
                child: const Text('Tuỳ chọn', style: TextStyle(fontSize: 10, color: Colors.grey)),
              ),
          ],
        ),
        subtitle: _isFulfilled && widget.uploadedDocuments.isNotEmpty
            ? AiValidationBadge(
                aiMatchResult: widget.uploadedDocuments.first.aiMatchResult,
                aiMatchOverridden: widget.uploadedDocuments.first.aiMatchOverridden,
              )
            : null,
        children: [
          // Document guidance
          if (_slots.isNotEmpty) _buildGuidanceSection(),
          // Uploaded documents
          if (widget.uploadedDocuments.isNotEmpty) _buildUploadedDocuments(),
          // Capture button
          if (!_isFulfilled) _buildCaptureButton(),
          const SizedBox(height: 8),
        ],
      ),
    );
  }

  Widget _buildStepIndicator(int order) {
    if (_isFulfilled) {
      return const CircleAvatar(
        radius: 14,
        backgroundColor: Colors.green,
        child: Icon(Icons.check, size: 16, color: Colors.white),
      );
    }
    return CircleAvatar(
      radius: 14,
      backgroundColor: _isMandatory ? Colors.blue : Colors.grey,
      child: Text(
        '$order',
        style: const TextStyle(fontSize: 12, color: Colors.white, fontWeight: FontWeight.bold),
      ),
    );
  }

  Widget _buildGuidanceSection() {
    final slot = _slots.first;
    final docName = (slot['label_override'] as String?) ??
        (slot['document_type_name'] as String?) ??
        '';
    final description = slot['description'] as String?;
    final classificationPrompt = slot['classification_prompt'] as String?;

    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (docName.isNotEmpty)
            Text(docName, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
          if (description != null) ...[
            const SizedBox(height: 2),
            Text(description, style: TextStyle(fontSize: 12, color: Colors.grey.shade700)),
          ],
          if (classificationPrompt != null) ...[
            const SizedBox(height: 4),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(6),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Đặc điểm nhận dạng',
                    style: TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: Colors.blue.shade800,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    classificationPrompt,
                    style: TextStyle(fontSize: 11, color: Colors.blue.shade700),
                    maxLines: 4,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
          ],
          if (_slots.length > 1) ...[
            const SizedBox(height: 4),
            Text(
              'Chấp nhận ${_slots.length} loại tài liệu (chọn 1)',
              style: TextStyle(fontSize: 11, color: Colors.blue.shade700, fontStyle: FontStyle.italic),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildUploadedDocuments() {
    return Column(
      children: widget.uploadedDocuments.map((doc) {
        return Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
          child: Row(
            children: [
              const Icon(Icons.insert_drive_file, size: 20, color: Colors.blue),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('${doc.pageCount} trang', style: const TextStyle(fontSize: 12)),
                    AiValidationBadge(
                      aiMatchResult: doc.aiMatchResult,
                      aiMatchOverridden: doc.aiMatchOverridden,
                    ),
                  ],
                ),
              ),
              if (!doc.aiMatchOverridden &&
                  doc.aiMatchResult != null &&
                  ((doc.aiMatchResult!['confidence'] as num?)?.toDouble() ?? 1.0) < 0.7)
                TextButton(
                  onPressed: () => _overrideAi(doc),
                  child: const Text('Bỏ qua', style: TextStyle(fontSize: 11)),
                ),
              IconButton(
                icon: const Icon(Icons.delete_outline, size: 20, color: Colors.red),
                onPressed: () => _deleteDocument(doc),
              ),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildCaptureButton() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: SizedBox(
        width: double.infinity,
        child: OutlinedButton.icon(
          onPressed: _uploading ? null : _onCaptureTap,
          icon: _uploading
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.camera_alt),
          label: Text(_uploading ? 'Đang tải...' : 'Chụp ảnh'),
        ),
      ),
    );
  }
}
