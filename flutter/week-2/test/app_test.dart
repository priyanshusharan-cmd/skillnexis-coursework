import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sn_week2/main.dart';

void main() {
  testWidgets('to-do: add a task on screen 2, see it on screen 1, tick it', (tester) async {
    await tester.pumpWidget(const Week2App());
    await tester.tap(find.text('To-Do list'));
    await tester.pumpAndSettle();
    expect(find.text('No tasks yet. Tap + to add one.'), findsOneWidget);

    await tester.tap(find.byIcon(Icons.add));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Save'));
    await tester.pump();
    expect(find.text('Enter a task'), findsOneWidget, reason: 'empty task is rejected');

    await tester.enterText(find.byType(TextField), 'Buy milk');
    await tester.tap(find.text('Save'));
    await tester.pumpAndSettle();
    expect(find.text('Buy milk'), findsOneWidget);
    expect(find.text('Tasks (1 left)'), findsOneWidget);

    await tester.tap(find.byType(Checkbox));
    await tester.pump();
    expect(find.text('Tasks (0 left)'), findsOneWidget);
  });

  testWidgets('login validates input then navigates to home', (tester) async {
    await tester.pumpWidget(const Week2App());
    await tester.tap(find.text('Login and navigation'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Log in'));
    await tester.pump();
    expect(find.text('Enter a valid email'), findsOneWidget);
    expect(find.text('At least 6 characters'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField).first, 'asha@example.com');
    await tester.enterText(find.byType(TextFormField).last, 'secret1');
    await tester.tap(find.text('Log in'));
    await tester.pumpAndSettle();
    expect(find.text('Welcome, asha@example.com'), findsOneWidget);
  });

  testWidgets('expense tracker: add, total on dashboard, history, delete', (tester) async {
    await tester.pumpWidget(const Week2App());
    await tester.tap(find.text('Expense tracker'));
    await tester.pumpAndSettle();
    expect(find.text('No expenses yet.'), findsOneWidget);

    await tester.tap(find.text('Add'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextFormField).first, 'Lunch');
    await tester.enterText(find.byType(TextFormField).at(1), '-5');
    await tester.tap(find.text('Add expense'));
    await tester.pump();
    expect(find.text('Enter an amount above 0'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField).at(1), '120.5');
    await tester.tap(find.text('Add expense'));
    await tester.pumpAndSettle();
    expect(find.text('₹120.50'), findsWidgets);

    await tester.tap(find.text('History'));
    await tester.pumpAndSettle();
    expect(find.text('Lunch'), findsOneWidget);
    await tester.tap(find.byTooltip('Delete'));
    await tester.pumpAndSettle();
    expect(find.text('Nothing here yet.'), findsOneWidget);
  });
}
