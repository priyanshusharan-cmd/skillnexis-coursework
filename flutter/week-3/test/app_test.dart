import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:sn_week3/auth.dart';
import 'package:sn_week3/main.dart';
import 'package:sn_week3/weather_service.dart';

http.Client fakeClient({bool cityFound = true, int status = 200, bool offline = false}) => MockClient((req) async {
      await Future<void>.delayed(const Duration(milliseconds: 20));
      if (offline) throw Exception('no network');
      if (status != 200) return http.Response('boom', status);
      if (req.url.host == 'geocoding-api.open-meteo.com') {
        return http.Response(jsonEncode(cityFound ? {'results': [{'name': 'Pune', 'country_code': 'IN', 'latitude': 18.5, 'longitude': 73.8}]} : {}), 200);
      }
      if (req.url.host == 'api.open-meteo.com') {
        return http.Response(jsonEncode({'current': {'temperature_2m': 27.6, 'relative_humidity_2m': 61, 'weather_code': 61, 'wind_speed_10m': 9.4}}), 200);
      }
      if (req.url.host == 'jsonplaceholder.typicode.com') {
        return http.Response(jsonEncode([{'id': 1, 'title': 'First post', 'body': 'hello'}, {'id': 2, 'title': 'Second post', 'body': 'world'}]), 200);
      }
      return http.Response('not found', 404);
    });

void main() {
  test('weather service parses a result and reports errors', () async {
    final ok = await WeatherService(client: fakeClient()).forCity(' Pune ');
    expect(ok.city, 'Pune, IN');
    expect(ok.temperature, 27.6);
    expect(ok.humidity, 61);
    expect(ok.description, 'Rain');
    await expectLater(WeatherService(client: fakeClient(cityFound: false)).forCity('Nowhere'), throwsA(isA<WeatherException>().having((e) => e.message, 'message', 'City not found: Nowhere')));
    await expectLater(WeatherService(client: fakeClient()).forCity('  '), throwsA(isA<WeatherException>()));
    await expectLater(WeatherService(client: fakeClient(status: 500)).forCity('x'), throwsA(isA<WeatherException>().having((e) => e.message, 'message', contains('500'))));
    await expectLater(WeatherService(client: fakeClient(offline: true)).forCity('x'), throwsA(isA<WeatherException>().having((e) => e.message, 'message', contains('connection'))));
  });

  test('local auth service signs up, rejects bad credentials and signs out', () async {
    final auth = LocalAuthService();
    await auth.signUp('a@b.co', 'secret1');
    expect(auth.currentUser, 'a@b.co');
    await auth.signOut();
    expect(auth.currentUser, isNull);
    await expectLater(auth.signIn('a@b.co', 'wrong'), throwsA(isA<AuthException>()));
    await expectLater(auth.signUp('a@b.co', 'x'), throwsA(isA<AuthException>()));
    await auth.signIn('a@b.co', 'secret1');
    expect(auth.currentUser, 'a@b.co');
  });

  testWidgets('public API screen shows fetched posts', (tester) async {
    await tester.pumpWidget(Week3App(client: fakeClient(), auth: LocalAuthService()));
    await tester.tap(find.text('Public API data'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 5));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    await tester.pumpAndSettle();
    expect(find.text('First post'), findsOneWidget);
    expect(find.text('Second post'), findsOneWidget);
  });

  testWidgets('weather screen: loading indicator then result', (tester) async {
    await tester.pumpWidget(Week3App(client: fakeClient(), auth: LocalAuthService()));
    await tester.tap(find.text('Weather forecast'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Pune');
    await tester.tap(find.byTooltip('Search'));
    await tester.pump(const Duration(milliseconds: 5));
    expect(find.byType(CircularProgressIndicator), findsOneWidget);
    await tester.pumpAndSettle();
    expect(find.text('Pune, IN'), findsOneWidget);
    expect(find.text('28°C'), findsOneWidget);
    expect(find.text('Humidity 61%   Wind 9 km/h'), findsOneWidget);
  });

  testWidgets('weather screen shows an error for a missing city', (tester) async {
    await tester.pumpWidget(Week3App(client: fakeClient(cityFound: false), auth: LocalAuthService()));
    await tester.tap(find.text('Weather forecast'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byType(TextField), 'Nowhere');
    await tester.tap(find.byTooltip('Search'));
    await tester.pump();
    await tester.pumpAndSettle();
    expect(find.text('City not found: Nowhere'), findsOneWidget);
  });

  testWidgets('login page: validation, sign up, log out', (tester) async {
    await tester.pumpWidget(Week3App(client: fakeClient(), auth: LocalAuthService()));
    await tester.tap(find.text('Login page'));
    await tester.pumpAndSettle();
    await tester.tap(find.widgetWithText(FilledButton, 'Log in'));
    await tester.pump();
    expect(find.text('Enter a valid email'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField).first, 'asha@example.com');
    await tester.enterText(find.byType(TextFormField).last, 'secret1');
    await tester.tap(find.widgetWithText(FilledButton, 'Log in'));
    await tester.pumpAndSettle();
    expect(find.text('Wrong email or password'), findsOneWidget);

    await tester.tap(find.text('Create an account'));
    await tester.pump();
    await tester.tap(find.widgetWithText(FilledButton, 'Sign up'));
    await tester.pumpAndSettle();
    expect(find.text('Signed in as asha@example.com'), findsOneWidget);
    await tester.tap(find.text('Log out'));
    await tester.pumpAndSettle();
    expect(find.text('Create account'), findsOneWidget);
  });
}
