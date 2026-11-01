import 'package:flutter/material.dart';

/// Login page and home page navigation demo. This is UI only, so any well-formed email and a
/// password of at least 6 characters are accepted. No account or credential is checked or stored.
class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _hidden = true;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  void _login() {
    if (_form.currentState!.validate()) {
      Navigator.pushReplacement(context, MaterialPageRoute<void>(builder: (_) => DemoHomePage(email: _email.text.trim())));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Login')),
      body: Form(
        key: _form,
        child: ListView(padding: const EdgeInsets.all(20), children: [
          TextFormField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email', border: OutlineInputBorder()),
            validator: (v) => RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v?.trim() ?? '') ? null : 'Enter a valid email',
          ),
          const SizedBox(height: 16),
          TextFormField(
            controller: _password,
            obscureText: _hidden,
            decoration: InputDecoration(
              labelText: 'Password',
              border: const OutlineInputBorder(),
              suffixIcon: IconButton(icon: Icon(_hidden ? Icons.visibility : Icons.visibility_off), onPressed: () => setState(() => _hidden = !_hidden)),
            ),
            validator: (v) => (v ?? '').length >= 6 ? null : 'At least 6 characters',
          ),
          const SizedBox(height: 20),
          FilledButton(onPressed: _login, child: const Text('Log in')),
        ]),
      ),
    );
  }
}

class DemoHomePage extends StatelessWidget {
  const DemoHomePage({super.key, required this.email});
  final String email;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Home'), automaticallyImplyLeading: false),
      drawer: Drawer(
        child: ListView(children: [
          DrawerHeader(child: Text('Signed in as\n$email')),
          ListTile(leading: const Icon(Icons.logout), title: const Text('Log out'), onTap: () => Navigator.popUntil(context, (r) => r.isFirst)),
        ]),
      ),
      body: Center(child: Text('Welcome, $email', style: Theme.of(context).textTheme.titleLarge)),
    );
  }
}
