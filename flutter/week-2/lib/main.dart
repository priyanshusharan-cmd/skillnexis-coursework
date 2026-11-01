import 'package:flutter/material.dart';

import 'expenses.dart';
import 'login_demo.dart';
import 'todo.dart';

void main() => runApp(const Week2App());

class Week2App extends StatelessWidget {
  const Week2App({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SkillNexis Flutter Week 2',
      theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
      home: const HomeMenu(),
    );
  }
}

class HomeMenu extends StatelessWidget {
  const HomeMenu({super.key});

  @override
  Widget build(BuildContext context) {
    Widget tile(String title, String subtitle, IconData icon, Widget page) => Card(
          child: ListTile(
            leading: Icon(icon),
            title: Text(title),
            subtitle: Text(subtitle),
            trailing: const Icon(Icons.chevron_right),
            onTap: () => Navigator.push(context, MaterialPageRoute<void>(builder: (_) => page)),
          ),
        );
    return Scaffold(
      appBar: AppBar(title: const Text('Week 2 demos')),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          tile('To-Do list', 'Two screens, TextField and setState', Icons.checklist, const TodoListScreen()),
          tile('Login and navigation', 'Form validation, push and pop', Icons.login, const LoginScreen()),
          tile('Expense tracker', 'Dashboard, add expense and history', Icons.account_balance_wallet, const ExpenseTrackerApp()),
        ],
      ),
    );
  }
}
