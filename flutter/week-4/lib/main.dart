import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'store.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(AttendanceApp(prefs: await SharedPreferences.getInstance()));
}

class AttendanceApp extends StatefulWidget {
  const AttendanceApp({super.key, required this.prefs});
  final SharedPreferences prefs;

  @override
  State<AttendanceApp> createState() => _AttendanceAppState();
}

class _AttendanceAppState extends State<AttendanceApp> {
  late final AttendanceStore store = AttendanceStore(widget.prefs);
  late ThemeMode mode = ThemeMode.values.firstWhere((m) => m.name == widget.prefs.getString('theme'), orElse: () => ThemeMode.system);

  void _setMode(ThemeMode m) {
    setState(() => mode = m);
    widget.prefs.setString('theme', m.name);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Student Attendance',
      themeMode: mode,
      theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
      darkTheme: ThemeData(colorSchemeSeed: Colors.indigo, brightness: Brightness.dark, useMaterial3: true),
      home: HomeShell(store: store, mode: mode, onMode: _setMode),
    );
  }
}

class HomeShell extends StatefulWidget {
  const HomeShell({super.key, required this.store, required this.mode, required this.onMode});
  final AttendanceStore store;
  final ThemeMode mode;
  final ValueChanged<ThemeMode> onMode;

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _tab = 0;

  @override
  Widget build(BuildContext context) {
    final titles = ['Students (admin)', 'Mark attendance', 'Report'];
    return Scaffold(
      appBar: AppBar(
        title: Text(titles[_tab]),
        actions: [
          PopupMenuButton<ThemeMode>(
            tooltip: 'Theme',
            icon: const Icon(Icons.brightness_6),
            initialValue: widget.mode,
            onSelected: widget.onMode,
            itemBuilder: (_) => const [
              PopupMenuItem(value: ThemeMode.system, child: Text('System')),
              PopupMenuItem(value: ThemeMode.light, child: Text('Light')),
              PopupMenuItem(value: ThemeMode.dark, child: Text('Dark')),
            ],
          ),
        ],
      ),
      body: ListenableBuilder(
        listenable: widget.store,
        builder: (context, _) => [AdminPage(store: widget.store), MarkPage(store: widget.store), ReportPage(store: widget.store)][_tab],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.people), label: 'Students'),
          NavigationDestination(icon: Icon(Icons.fact_check), label: 'Attendance'),
          NavigationDestination(icon: Icon(Icons.bar_chart), label: 'Report'),
        ],
      ),
    );
  }
}

class AdminPage extends StatefulWidget {
  const AdminPage({super.key, required this.store});
  final AttendanceStore store;

  @override
  State<AdminPage> createState() => _AdminPageState();
}

class _AdminPageState extends State<AdminPage> {
  final _name = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  Future<void> _add() async {
    final ok = await widget.store.addStudent(_name.text);
    setState(() => _error = ok ? null : 'Enter a new, non-empty name');
    if (ok) _name.clear();
  }

  @override
  Widget build(BuildContext context) {
    final students = widget.store.students;
    return Column(children: [
      Padding(
        padding: const EdgeInsets.all(12),
        child: Row(children: [
          Expanded(child: TextField(controller: _name, onSubmitted: (_) => _add(), decoration: InputDecoration(labelText: 'Student name', errorText: _error, border: const OutlineInputBorder()))),
          const SizedBox(width: 8),
          FilledButton(onPressed: _add, child: const Text('Add')),
        ]),
      ),
      Expanded(
        child: students.isEmpty
            ? const Center(child: Text('No students yet.'))
            : ListView(children: [
                for (final s in students)
                  ListTile(title: Text(s.name), trailing: IconButton(icon: const Icon(Icons.delete_outline), tooltip: 'Remove ${s.name}', onPressed: () => widget.store.removeStudent(s.id))),
              ]),
      ),
    ]);
  }
}

class MarkPage extends StatefulWidget {
  const MarkPage({super.key, required this.store});
  final AttendanceStore store;

  @override
  State<MarkPage> createState() => _MarkPageState();
}

class _MarkPageState extends State<MarkPage> {
  DateTime _day = DateTime.now();

  Future<void> _pick() async {
    final d = await showDatePicker(context: context, initialDate: _day, firstDate: DateTime(2020), lastDate: DateTime.now());
    if (d != null) setState(() => _day = d);
  }

  @override
  Widget build(BuildContext context) {
    final students = widget.store.students;
    return Column(children: [
      ListTile(leading: const Icon(Icons.calendar_today), title: Text('Date: ${dateKey(_day)}'), trailing: TextButton(onPressed: _pick, child: const Text('Change')), ),
      const Divider(height: 1),
      Expanded(
        child: students.isEmpty
            ? const Center(child: Text('Add students first.'))
            : ListView(children: [
                for (final s in students)
                  CheckboxListTile(title: Text(s.name), value: widget.store.isPresent(_day, s.id), onChanged: (v) => widget.store.setPresent(_day, s.id, v ?? false)),
              ]),
      ),
    ]);
  }
}

class ReportPage extends StatelessWidget {
  const ReportPage({super.key, required this.store});
  final AttendanceStore store;

  @override
  Widget build(BuildContext context) {
    if (store.students.isEmpty) return const Center(child: Text('No students yet.'));
    return ListView(children: [
      for (final s in store.students)
        Builder(builder: (context) {
          final r = store.summary(s.id);
          final pct = r.total == 0 ? 0.0 : r.present / r.total;
          return ListTile(
            title: Text(s.name),
            subtitle: LinearProgressIndicator(value: pct),
            trailing: Text('${r.present}/${r.total} days (${(pct * 100).round()}%)'),
          );
        }),
    ]);
  }
}
