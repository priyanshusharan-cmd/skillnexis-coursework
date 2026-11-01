import 'package:flutter/material.dart';

class Expense {
  Expense(this.title, this.amount, this.category, this.date);
  final String title;
  final double amount;
  final String category;
  final DateTime date;
}

const categories = ['Food', 'Travel', 'Bills', 'Fun', 'Other'];

/// Mini project: expense tracker with Dashboard, Add Expense and History, using local state.
class ExpenseTrackerApp extends StatefulWidget {
  const ExpenseTrackerApp({super.key});

  @override
  State<ExpenseTrackerApp> createState() => _ExpenseTrackerAppState();
}

class _ExpenseTrackerAppState extends State<ExpenseTrackerApp> {
  final List<Expense> _expenses = [];
  int _tab = 0;

  void _add(Expense e) => setState(() {
        _expenses.insert(0, e);
        _tab = 0;
      });

  @override
  Widget build(BuildContext context) {
    final pages = [
      Dashboard(expenses: _expenses),
      AddExpense(onAdd: _add),
      History(expenses: _expenses, onDelete: (e) => setState(() => _expenses.remove(e))),
    ];
    return Scaffold(
      appBar: AppBar(title: const Text('Expense tracker')),
      body: pages[_tab],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.add_circle), label: 'Add'),
          NavigationDestination(icon: Icon(Icons.history), label: 'History'),
        ],
      ),
    );
  }
}

class Dashboard extends StatelessWidget {
  const Dashboard({super.key, required this.expenses});
  final List<Expense> expenses;

  @override
  Widget build(BuildContext context) {
    final total = expenses.fold<double>(0, (s, e) => s + e.amount);
    final byCategory = <String, double>{};
    for (final e in expenses) {
      byCategory[e.category] = (byCategory[e.category] ?? 0) + e.amount;
    }
    return ListView(padding: const EdgeInsets.all(16), children: [
      Card(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(children: [
            const Text('Total spent'),
            Text('₹${total.toStringAsFixed(2)}', style: Theme.of(context).textTheme.headlineLarge),
          ]),
        ),
      ),
      const SizedBox(height: 8),
      if (byCategory.isEmpty) const Padding(padding: EdgeInsets.all(24), child: Center(child: Text('No expenses yet.'))),
      for (final entry in byCategory.entries)
        ListTile(
          title: Text(entry.key),
          subtitle: LinearProgressIndicator(value: total == 0 ? 0 : entry.value / total),
          trailing: Text('₹${entry.value.toStringAsFixed(2)}'),
        ),
    ]);
  }
}

class AddExpense extends StatefulWidget {
  const AddExpense({super.key, required this.onAdd});
  final void Function(Expense) onAdd;

  @override
  State<AddExpense> createState() => _AddExpenseState();
}

class _AddExpenseState extends State<AddExpense> {
  final _form = GlobalKey<FormState>();
  final _title = TextEditingController();
  final _amount = TextEditingController();
  String _category = categories.first;

  @override
  void dispose() {
    _title.dispose();
    _amount.dispose();
    super.dispose();
  }

  void _save() {
    if (!_form.currentState!.validate()) return;
    widget.onAdd(Expense(_title.text.trim(), double.parse(_amount.text), _category, DateTime.now()));
    _title.clear();
    _amount.clear();
  }

  @override
  Widget build(BuildContext context) {
    return Form(
      key: _form,
      child: ListView(padding: const EdgeInsets.all(16), children: [
        TextFormField(
          controller: _title,
          decoration: const InputDecoration(labelText: 'Title', border: OutlineInputBorder()),
          validator: (v) => (v ?? '').trim().isEmpty ? 'Enter a title' : null,
        ),
        const SizedBox(height: 12),
        TextFormField(
          controller: _amount,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: const InputDecoration(labelText: 'Amount', border: OutlineInputBorder()),
          validator: (v) {
            final n = double.tryParse(v ?? '');
            return n == null || n <= 0 ? 'Enter an amount above 0' : null;
          },
        ),
        const SizedBox(height: 12),
        DropdownButtonFormField<String>(
          initialValue: _category,
          decoration: const InputDecoration(labelText: 'Category', border: OutlineInputBorder()),
          items: [for (final c in categories) DropdownMenuItem(value: c, child: Text(c))],
          onChanged: (v) => setState(() => _category = v ?? _category),
        ),
        const SizedBox(height: 16),
        FilledButton(onPressed: _save, child: const Text('Add expense')),
      ]),
    );
  }
}

class History extends StatelessWidget {
  const History({super.key, required this.expenses, required this.onDelete});
  final List<Expense> expenses;
  final void Function(Expense) onDelete;

  @override
  Widget build(BuildContext context) {
    if (expenses.isEmpty) return const Center(child: Text('Nothing here yet.'));
    return ListView(children: [
      for (final e in expenses)
        ListTile(
          title: Text(e.title),
          subtitle: Text('${e.category} • ${e.date.day}/${e.date.month}/${e.date.year}'),
          trailing: Row(mainAxisSize: MainAxisSize.min, children: [
            Text('₹${e.amount.toStringAsFixed(2)}'),
            IconButton(icon: const Icon(Icons.delete_outline), tooltip: 'Delete', onPressed: () => onDelete(e)),
          ]),
        ),
    ]);
  }
}
