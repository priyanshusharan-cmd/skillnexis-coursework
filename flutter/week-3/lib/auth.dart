import 'package:flutter/material.dart';

class AuthException implements Exception {
  AuthException(this.message);
  final String message;
  @override
  String toString() => message;
}

/// The app talks to this interface only. To use Firebase, implement it with `firebase_auth`
/// (`createUserWithEmailAndPassword`, `signInWithEmailAndPassword`, `signOut`) after running
/// `flutterfire configure` for your own Firebase project, then pass that implementation to the app.
abstract class AuthService {
  String? get currentUser;
  Future<void> signUp(String email, String password);
  Future<void> signIn(String email, String password);
  Future<void> signOut();
}

/// In-memory implementation used for development and tests. Nothing is stored or sent anywhere.
class LocalAuthService implements AuthService {
  final Map<String, String> _accounts = {};
  String? _user;

  @override
  String? get currentUser => _user;

  @override
  Future<void> signUp(String email, String password) async {
    if (_accounts.containsKey(email)) throw AuthException('An account already exists for $email');
    _accounts[email] = password;
    _user = email;
  }

  @override
  Future<void> signIn(String email, String password) async {
    if (_accounts[email] != password) throw AuthException('Wrong email or password');
    _user = email;
  }

  @override
  Future<void> signOut() async => _user = null;
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key, required this.auth});
  final AuthService auth;

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _form = GlobalKey<FormState>();
  final _email = TextEditingController();
  final _password = TextEditingController();
  bool _creating = false;
  bool _busy = false;
  String? _error;

  @override
  void dispose() {
    _email.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final email = _email.text.trim();
      if (_creating) {
        await widget.auth.signUp(email, _password.text);
      } else {
        await widget.auth.signIn(email, _password.text);
      }
    } on AuthException catch (e) {
      _error = e.message;
    }
    if (mounted) setState(() => _busy = false);
  }

  @override
  Widget build(BuildContext context) {
    final user = widget.auth.currentUser;
    if (user != null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Account')),
        body: Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            Text('Signed in as $user'),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: () async {
                await widget.auth.signOut();
                if (mounted) setState(() {});
              },
              child: const Text('Log out'),
            ),
          ]),
        ),
      );
    }
    return Scaffold(
      appBar: AppBar(title: Text(_creating ? 'Create account' : 'Log in')),
      body: Form(
        key: _form,
        child: ListView(padding: const EdgeInsets.all(20), children: [
          TextFormField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            decoration: const InputDecoration(labelText: 'Email', border: OutlineInputBorder()),
            validator: (v) => RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(v?.trim() ?? '') ? null : 'Enter a valid email',
          ),
          const SizedBox(height: 14),
          TextFormField(
            controller: _password,
            obscureText: true,
            decoration: const InputDecoration(labelText: 'Password', border: OutlineInputBorder()),
            validator: (v) => (v ?? '').length >= 6 ? null : 'At least 6 characters',
          ),
          if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error))),
          const SizedBox(height: 16),
          FilledButton(onPressed: _busy ? null : _submit, child: Text(_busy ? 'Please wait...' : (_creating ? 'Sign up' : 'Log in'))),
          TextButton(onPressed: () => setState(() => _creating = !_creating), child: Text(_creating ? 'I already have an account' : 'Create an account')),
        ]),
      ),
    );
  }
}
