import 'package:flutter/material.dart';

void main() => runApp(const ProfileApp());

class ProfileApp extends StatelessWidget {
  const ProfileApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Week 1 Profile Card',
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF3867D6)), useMaterial3: true),
    home: const ProfilePage(),
  );
}

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Hello Flutter')),
    body: Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Card(
            clipBehavior: Clip.antiAlias,
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                const CircleAvatar(radius: 42, child: Icon(Icons.person, size: 48)),
                const SizedBox(height: 16),
                Text('Your Name', style: Theme.of(context).textTheme.headlineSmall),
                const Text('Flutter learner'),
                const SizedBox(height: 20),
                const _InfoRow(icon: Icons.code, label: 'Skills', value: 'Dart, Flutter basics'),
                const _InfoRow(icon: Icons.email_outlined, label: 'Contact', value: 'you@example.com'),
                const SizedBox(height: 16),
                FilledButton.icon(onPressed: () {}, icon: const Icon(Icons.waving_hand), label: const Text('Hello')),
              ]),
            ),
          ),
        ),
      ),
    ),
  );
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({required this.icon, required this.label, required this.value});
  final IconData icon;
  final String label;
  final String value;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 6),
    child: Row(children: [Icon(icon), const SizedBox(width: 12), Text('$label: '), Expanded(child: Text(value))]),
  );
}
