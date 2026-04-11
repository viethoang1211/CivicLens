import 'package:flutter/material.dart';
import 'package:shared_dart/shared_dart.dart';

/// State management service for dossier operations in the staff app.
/// Uses ChangeNotifier for simple reactive updates without external state management.
class DossierService extends ChangeNotifier {
  final DossierApi _api;

  DossierService(this._api);

  // ── State ──────────────────────────────────────────────────────────────

  List<DossierListItemDto> _dossiers = [];
  DossierDto? _currentDossier;
  List<CaseTypeDto> _caseTypes = [];
  bool _loading = false;
  String? _error;

  List<DossierListItemDto> get dossiers => _dossiers;
  DossierDto? get currentDossier => _currentDossier;
  List<CaseTypeDto> get caseTypes => _caseTypes;
  bool get loading => _loading;
  String? get error => _error;

  // ── Case Types ─────────────────────────────────────────────────────────

  Future<void> loadCaseTypes() async {
    _setLoading(true);
    try {
      _caseTypes = await _api.listCaseTypes(activeOnly: true);
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _setLoading(false);
    }
  }

  // ── Dossier List ───────────────────────────────────────────────────────

  Future<void> loadDossiers({
    String? status,
    String? caseTypeId,
    String? citizenId,
    int page = 1,
    int pageSize = 20,
  }) async {
    _setLoading(true);
    try {
      final result = await _api.listDossiers(
        status: status,
        caseTypeId: caseTypeId,
        citizenId: citizenId,
        page: page,
        pageSize: pageSize,
      );
      _dossiers = result['items'] as List<DossierListItemDto>;
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _setLoading(false);
    }
  }

  // ── Single Dossier ─────────────────────────────────────────────────────

  Future<void> loadDossier(String dossierId) async {
    _setLoading(true);
    try {
      _currentDossier = await _api.getDossier(dossierId);
      _error = null;
    } catch (e) {
      _error = e.toString();
    } finally {
      _setLoading(false);
    }
  }

  Future<DossierDto?> createDossier({
    required String citizenIdNumber,
    required String caseTypeId,
    int securityClassification = 0,
    String priority = 'normal',
  }) async {
    _setLoading(true);
    try {
      final dossier = await _api.createDossier(
        citizenIdNumber: citizenIdNumber,
        caseTypeId: caseTypeId,
        securityClassification: securityClassification,
        priority: priority,
      );
      _currentDossier = dossier;
      _error = null;
      notifyListeners();
      return dossier;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    } finally {
      _setLoading(false);
    }
  }

  Future<DossierDto?> submitDossier(String dossierId) async {
    _setLoading(true);
    try {
      final submitted = await _api.submitDossier(dossierId);
      _currentDossier = submitted;
      _error = null;
      notifyListeners();
      return submitted;
    } catch (e) {
      _error = e.toString();
      notifyListeners();
      return null;
    } finally {
      _setLoading(false);
    }
  }

  // ── Helpers ────────────────────────────────────────────────────────────

  void _setLoading(bool value) {
    _loading = value;
    notifyListeners();
  }

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
