import 'package:flutter/material.dart';

/// Screen 1: the list of tasks. Screen 2 (AddTaskScreen) returns the new task text.
class TodoListScreen extends StatefulWidget {
  const TodoListScreen({super.key});

  @override
  State<TodoListScreen> createState() => _TodoListScreenState();
}

class _Task {
  _Task(this.title);
  final String title;
  bool done = false;
}

class _TodoListScreenState extends State<TodoListScreen> {
  final List<_Task> _tasks = [];

  Future<void> _openAdd() async {
    final text = await Navigator.push<String>(context, MaterialPageRoute(builder: (_) => const AddTaskScreen()));
    if (text != null && text.trim().isNotEmpty) {
      setState(() => _tasks.add(_Task(text.trim())));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Tasks (${_tasks.where((t) => !t.done).length} left)')),
      body: _tasks.isEmpty
          ? const Center(child: Text('No tasks yet. Tap + to add one.'))
          : ListView.builder(
              itemCount: _tasks.length,
              itemBuilder: (context, i) {
                final task = _tasks[i];
                return Dismissible(
                  key: ObjectKey(task),
                  background: Container(color: Colors.red),
                  onDismissed: (_) => setState(() => _tasks.removeAt(i)),
                  child: CheckboxListTile(
                    value: task.done,
                    title: Text(task.title, style: TextStyle(decoration: task.done ? TextDecoration.lineThrough : null)),
                    onChanged: (v) => setState(() => task.done = v ?? false),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton(onPressed: _openAdd, tooltip: 'Add task', child: const Icon(Icons.add)),
    );
  }
}

class AddTaskScreen extends StatefulWidget {
  const AddTaskScreen({super.key});

  @override
  State<AddTaskScreen> createState() => _AddTaskScreenState();
}

class _AddTaskScreenState extends State<AddTaskScreen> {
  final _controller = TextEditingController();
  String? _error;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    if (_controller.text.trim().isEmpty) {
      setState(() => _error = 'Enter a task');
      return;
    }
    Navigator.pop(context, _controller.text);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Add task')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          TextField(
            controller: _controller,
            autofocus: true,
            decoration: InputDecoration(labelText: 'Task', errorText: _error, border: const OutlineInputBorder()),
            onSubmitted: (_) => _submit(),
          ),
          const SizedBox(height: 16),
          FilledButton(onPressed: _submit, child: const Text('Save')),
        ]),
      ),
    );
  }
}
