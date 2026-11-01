import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import 'auth.dart';
import 'posts_screen.dart';
import 'weather_screen.dart';
import 'weather_service.dart';

void main() => runApp(Week3App(client: http.Client(), auth: LocalAuthService()));

class Week3App extends StatelessWidget {
  const Week3App({super.key, required this.client, required this.auth});
  final http.Client client;
  final AuthService auth;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SkillNexis Flutter Week 3',
      theme: ThemeData(colorSchemeSeed: Colors.teal, useMaterial3: true),
      home: Builder(builder: (context) {
        void go(Widget page) => Navigator.push(context, MaterialPageRoute<void>(builder: (_) => page));
        return Scaffold(
          appBar: AppBar(title: const Text('Week 3 demos')),
          body: ListView(padding: const EdgeInsets.all(12), children: [
            Card(child: ListTile(leading: const Icon(Icons.list), title: const Text('Public API data'), onTap: () => go(PostsScreen(client: client)))),
            Card(child: ListTile(leading: const Icon(Icons.lock), title: const Text('Login page'), onTap: () => go(LoginScreen(auth: auth)))),
            Card(child: ListTile(leading: const Icon(Icons.cloud), title: const Text('Weather forecast'), onTap: () => go(WeatherScreen(service: WeatherService(client: client))))),
          ]),
        );
      }),
    );
  }
}
