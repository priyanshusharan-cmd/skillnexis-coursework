import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sn_week4/main.dart';
import 'package:sn_week4/store.dart';

Future<AttendanceStore> newStore([Map<String, Object> initial = const {}]) async {
  SharedPreferences.setMockInitialValues(initial);
  return AttendanceStore(await SharedPreferences.getInstance());
}

void main() {
  test('adds students, rejects blanks and duplicates, removes students', () async {
    final s = await newStore();
    expect(await s.addStudent('  Asha '), isTrue);
    expect(await s.addStudent('asha'), isFalse);
    expect(await s.addStudent('   '), isFalse);
    expect(await s.addStudent('Ravi'), isTrue);
    expect(s.students.map((x) => x.name), ['Asha', 'Ravi']);
    await s.removeStudent(s.students.first.id);
    expect(s.students.map((x) => x.name), ['Ravi']);
  });

  test('attendance is date-wise, summarised, and survives a restart', () async {
    final s = await newStore();
    await s.addStudent('Asha');
    await s.addStudent('Ravi');
    final asha = s.students[0].id, ravi = s.students[1].id;
    final d1 = DateTime(2026, 11, 2), d2 = DateTime(2026, 11, 3);
    await s.setPresent(d1, asha, true);
    await s.setPresent(d1, ravi, true);
    await s.setPresent(d2, asha, true);
    await s.setPresent(d2, ravi, false);
    expect(s.summary(asha), (present: 2, total: 2));
    expect(s.summary(ravi), (present: 1, total: 2));
    expect(s.recordedDates, ['2026-11-02', '2026-11-03']);

    final prefs = await SharedPreferences.getInstance();
    final reopened = AttendanceStore(prefs);
    expect(reopened.students.length, 2);
    expect(reopened.isPresent(d1, ravi), isTrue);
    expect(reopened.isPresent(d2, ravi), isFalse);
    await reopened.removeStudent(ravi);
    expect(reopened.summary(asha).total, 2);
  });

  test('corrupt stored data is ignored instead of crashing', () async {
    final s = await newStore({'attendance-v1': '{broken'});
    expect(s.students, isEmpty);
    expect(await s.addStudent('Meera'), isTrue);
  });

  testWidgets('admin adds a student, marks attendance, report updates, theme can switch to dark', (tester) async {
    SharedPreferences.setMockInitialValues({});
    await tester.pumpWidget(AttendanceApp(prefs: await SharedPreferences.getInstance()));
    expect(find.text('No students yet.'), findsOneWidget);

    await tester.enterText(find.byType(TextField), 'Kabir');
    await tester.tap(find.text('Add'));
    await tester.pumpAndSettle();
    expect(find.text('Kabir'), findsOneWidget);

    await tester.tap(find.text('Attendance'));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(Checkbox));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Report'));
    await tester.pumpAndSettle();
    expect(find.text('1/1 days (100%)'), findsOneWidget);

    await tester.tap(find.byTooltip('Theme'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Dark'));
    await tester.pumpAndSettle();
    expect(Theme.of(tester.element(find.byType(Scaffold).first)).brightness, Brightness.dark);
  });
}
