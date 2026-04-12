import 'package:test/test.dart';
import 'package:shared_dart/shared_dart.dart';

void main() {
  group('CaseTypeDto', () {
    test('fromJson parses a full case type', () {
      final json = {
        'id': 'ct-001',
        'name': 'Đăng ký hộ kinh doanh',
        'code': 'HOUSEHOLD_BIZ_REG',
        'description': 'Test description',
        'is_active': true,
        'retention_years': 10,
        'retention_permanent': false,
        'requirement_groups': [
          {
            'id': 'grp-001',
            'group_order': 1,
            'label': 'Giấy tờ tùy thân',
            'is_mandatory': true,
            'is_fulfilled': false,
            'slots': [
              {
                'id': 'slot-001',
                'document_type_id': 'dt-001',
                'document_type_code': 'CCCD',
                'label': 'CMND/CCCD',
                'label_override': null,
                'fulfilled_by_document_id': null,
              },
            ],
          },
        ],
        'routing_steps': [
          {
            'id': 'rs-001',
            'step_order': 1,
            'department_id': 'dept-001',
            'department_name': 'Tiếp nhận',
            'expected_duration_hours': 48,
            'required_clearance_level': 0,
          },
        ],
      };

      final caseType = CaseTypeDto.fromJson(json);
      expect(caseType.id, 'ct-001');
      expect(caseType.name, 'Đăng ký hộ kinh doanh');
      expect(caseType.code, 'HOUSEHOLD_BIZ_REG');
      expect(caseType.isActive, true);
      expect(caseType.retentionYears, 10);
      expect(caseType.retentionPermanent, false);
      expect(caseType.requirementGroups, hasLength(1));
      expect(caseType.requirementGroups.first.label, 'Giấy tờ tùy thân');
      expect(caseType.requirementGroups.first.isMandatory, true);
      expect(caseType.requirementGroups.first.slots, hasLength(1));
      expect(caseType.requirementGroups.first.slots.first.label, 'CMND/CCCD');
      expect(caseType.routingSteps, hasLength(1));
      expect(caseType.routingSteps.first.departmentName, 'Tiếp nhận');
    });

    test('fromJson handles missing optional fields', () {
      final json = {
        'id': 'ct-002',
        'name': 'Test',
        'code': 'TEST',
        'requirement_groups': <dynamic>[],
        'routing_steps': <dynamic>[],
      };

      final caseType = CaseTypeDto.fromJson(json);
      expect(caseType.description, isNull);
      expect(caseType.isActive, true); // default
      expect(caseType.requirementGroups, isEmpty);
      expect(caseType.routingSteps, isEmpty);
    });
  });

  group('DossierDto', () {
    test('fromJson parses a full dossier with documents', () {
      final json = {
        'id': 'dos-001',
        'reference_number': 'HS-20260411-00001',
        'citizen_id': 'cit-001',
        'citizen_name': 'Nguyen Van A',
        'case_type_id': 'ct-001',
        'case_type_name': 'Đăng ký hộ kinh doanh',
        'status': 'in_progress',
        'priority': 'normal',
        'security_classification': 0,
        'created_at': '2026-04-11T10:00:00Z',
        'submitted_at': '2026-04-11T10:30:00Z',
        'requirement_groups': <dynamic>[],
        'documents': [
          {
            'id': 'doc-001',
            'dossier_id': 'dos-001',
            'requirement_slot_id': 'slot-001',
            'ai_match_result': {'match': true, 'confidence': 0.95, 'reason': 'Match'},
            'ai_match_overridden': false,
            'page_count': 2,
            'created_at': '2026-04-11T10:15:00Z',
          },
        ],
        'completeness': {'complete': true, 'missing_groups': <dynamic>[]},
      };

      final dossier = DossierDto.fromJson(json);
      expect(dossier.referenceNumber, 'HS-20260411-00001');
      expect(dossier.status, 'in_progress');
      expect(dossier.isSubmitted, true);
      expect(dossier.isDraft, false);
      expect(dossier.documents, hasLength(1));
      expect(dossier.documents.first.aiMatch, true);
      expect(dossier.documents.first.aiConfidence, 0.95);
      expect(dossier.completeness!.complete, true);
      expect(dossier.submittedAt, isNotNull);
    });

    test('status convenience getters', () {
      final draftJson = {
        'id': 'dos-002',
        'citizen_id': 'c',
        'case_type_id': 'ct',
        'status': 'draft',
        'security_classification': 0,
        'created_at': '2026-04-11T10:00:00Z',
        'requirement_groups': <dynamic>[],
        'documents': <dynamic>[],
      };

      final draft = DossierDto.fromJson(draftJson);
      expect(draft.isDraft, true);
      expect(draft.isSubmitted, false);
      expect(draft.isCompleted, false);
      expect(draft.isRejected, false);
    });
  });

  group('DossierDocumentDto', () {
    test('aiMatch helpers work correctly', () {
      final doc = DossierDocumentDto.fromJson({
        'id': 'doc-001',
        'dossier_id': 'dos-001',
        'ai_match_result': {'match': false, 'confidence': 0.12, 'reason': 'Not a CCCD'},
        'ai_match_overridden': false,
        'page_count': 1,
        'created_at': '2026-04-11T10:00:00Z',
      });

      expect(doc.aiMatch, false);
      expect(doc.aiConfidence, 0.12);
      expect(doc.aiReason, 'Not a CCCD');
    });

    test('null ai_match_result returns defaults', () {
      final doc = DossierDocumentDto.fromJson({
        'id': 'doc-002',
        'dossier_id': 'dos-001',
        'ai_match_result': null,
        'page_count': 0,
        'created_at': '2026-04-11T10:00:00Z',
      });

      expect(doc.aiMatch, false);
      expect(doc.aiConfidence, 0.0);
      expect(doc.aiReason, isNull);
    });
  });

  group('DossierTrackingDto', () {
    test('progress and status labels', () {
      final tracking = DossierTrackingDto.fromJson({
        'id': 'dos-001',
        'reference_number': 'HS-20260411-00001',
        'case_type_name': 'Đăng ký hộ kinh doanh',
        'status': 'in_progress',
        'submitted_at': '2026-04-11T10:00:00Z',
        'steps': [
          {'step_order': 1, 'department_name': 'Tiếp nhận', 'status': 'completed'},
          {'step_order': 2, 'department_name': 'Phòng TC', 'status': 'active'},
          {'step_order': 3, 'department_name': 'Lãnh đạo', 'status': 'pending'},
        ],
      });

      expect(tracking.statusLabelVi, 'Đang xử lý');
      expect(tracking.isInProgress, true);
      expect(tracking.totalSteps, 3);
      expect(tracking.completedSteps, 1);
      expect(tracking.progressFraction, closeTo(0.333, 0.01));
    });

    test('completed dossier tracking', () {
      final tracking = DossierTrackingDto.fromJson({
        'case_type_name': 'Test',
        'status': 'completed',
        'steps': <dynamic>[],
      });

      expect(tracking.statusLabelVi, 'Hoàn thành');
      expect(tracking.isCompleted, true);
      expect(tracking.progressFraction, 0.0);
    });
  });

  group('DossierListItemDto', () {
    test('fromJson parses list item', () {
      final item = DossierListItemDto.fromJson({
        'id': 'dos-001',
        'reference_number': 'HS-20260411-00001',
        'citizen_name': 'Nguyen Van A',
        'case_type_name': 'Test',
        'status': 'draft',
        'priority': 'urgent',
        'created_at': '2026-04-11T10:00:00Z',
      });

      expect(item.referenceNumber, 'HS-20260411-00001');
      expect(item.citizenName, 'Nguyen Van A');
      expect(item.priority, 'urgent');
    });
  });
}
