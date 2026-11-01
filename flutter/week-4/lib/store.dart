import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class Student {
  const Student(this.id, this.name);
  final int id;
  final String name;

  Map<String, dynamic> toJson() => {'id': id, 'name': name};
  static Student fromJson(Map<String, dynamic> j) => Student(j['id'] as int, j['name'] as String);
}

String dateKey(DateTime d) => '${d.year.toString().padLeft(4, '0')}-${d.month.toString().padLeft(2, '0')}-${d.day.toString().padLeft(2, '0')}';

/// Local database: students and date-wise attendance, saved as JSON in SharedPreferences.
class AttendanceStore extends ChangeNotifier {
  AttendanceStore(this._prefs) {
    _load();
  }

  static const _key = 'attendance-v1';
  final SharedPreferences _prefs;
  final List<Student> _students = [];
  final Map<String, Set<int>> _present = {}; // date -> ids marked present
  int _nextId = 1;

  List<Student> get students => List.unmodifiable(_students);
  List<String> get recordedDates => (_present.keys.toList()..sort());

  void _load() {
    final raw = _prefs.getString(_key);
    if (raw == null) return;
    try {
      final j = jsonDecode(raw) as Map<String, dynamic>;
      _students.addAll([for (final s in j['students'] as List<dynamic>) Student.fromJson(s as Map<String, dynamic>)]);
      (j['present'] as Map<String, dynamic>).forEach((k, v) => _present[k] = {for (final id in v as List<dynamic>) id as int});
      _nextId = j['nextId'] as int;
    } catch (_) {
      _students.clear();
      _present.clear();
      _nextId = 1;
    }
  }

  Future<void> _save() async {
    await _prefs.setString(
      _key,
      jsonEncode({
        'students': [for (final s in _students) s.toJson()],
        'present': _present.map((k, v) => MapEntry(k, v.toList()..sort())),
        'nextId': _nextId,
      }),
    );
    notifyListeners();
  }

  Future<bool> addStudent(String name) async {
    final clean = name.trim();
    if (clean.isEmpty || _students.any((s) => s.name.toLowerCase() == clean.toLowerCase())) return false;
    _students.add(Student(_nextId++, clean));
    await _save();
    return true;
  }

  Future<void> removeStudent(int id) async {
    _students.removeWhere((s) => s.id == id);
    for (final ids in _present.values) {
      ids.remove(id);
    }
    await _save();
  }

  bool isPresent(DateTime day, int id) => _present[dateKey(day)]?.contains(id) ?? false;

  Future<void> setPresent(DateTime day, int id, bool present) async {
    final ids = _present.putIfAbsent(dateKey(day), () => {});
    present ? ids.add(id) : ids.remove(id);
    await _save();
  }

  /// A day counts as recorded once anything has been saved for it.
  ({int present, int total}) summary(int id) => (present: _present.values.where((ids) => ids.contains(id)).length, total: _present.length);
}
