import 'package:flutter/material.dart';

/// Displays AI validation status as a colored badge with text.
///
/// States based on `ai_match_result` JSONB:
/// - null → grey spinner "Đang xác minh..."
/// - match with confidence ≥ 0.7 → green "Đã xác minh"
/// - match with confidence 0.4–0.7 → orange "Cần kiểm tra"
/// - match with confidence < 0.4 → red "Không khớp"
/// - overridden → blue "Đã ghi đè"
class AiValidationBadge extends StatelessWidget {
  final Map<String, dynamic>? aiMatchResult;
  final bool aiMatchOverridden;

  const AiValidationBadge({
    super.key,
    required this.aiMatchResult,
    this.aiMatchOverridden = false,
  });

  @override
  Widget build(BuildContext context) {
    if (aiMatchOverridden) {
      return _badge(
        icon: Icons.verified_user,
        color: Colors.blue,
        label: 'Đã ghi đè',
      );
    }

    if (aiMatchResult == null) {
      return Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          SizedBox(
            width: 14,
            height: 14,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: Colors.grey.shade400,
            ),
          ),
          const SizedBox(width: 6),
          Text(
            'Đang xác minh...',
            style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
          ),
        ],
      );
    }

    final confidence = (aiMatchResult!['confidence'] as num?)?.toDouble() ?? 0.0;
    final reason = aiMatchResult!['reason'] as String?;

    if (confidence >= 0.7) {
      return _badge(
        icon: Icons.check_circle,
        color: Colors.green,
        label: 'Đã xác minh',
      );
    } else if (confidence >= 0.4) {
      return _badge(
        icon: Icons.warning_amber,
        color: Colors.orange,
        label: 'Cần kiểm tra',
        subtitle: reason,
      );
    } else {
      return _badge(
        icon: Icons.cancel,
        color: Colors.red,
        label: 'Không khớp',
        subtitle: reason,
      );
    }
  }

  Widget _badge({
    required IconData icon,
    required Color color,
    required String label,
    String? subtitle,
  }) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 16, color: color),
        const SizedBox(width: 4),
        Flexible(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(label, style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600)),
              if (subtitle != null)
                Text(
                  subtitle,
                  style: TextStyle(fontSize: 10, color: color.withOpacity(0.7)),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
            ],
          ),
        ),
      ],
    );
  }
}
