import 'dart:convert';

import 'package:http/http.dart' as http;

class Weather {
  const Weather({required this.city, required this.temperature, required this.humidity, required this.code, required this.windKmh});
  final String city;
  final double temperature;
  final int humidity;
  final int code;
  final double windKmh;

  String get description => describeCode(code);
}

class WeatherException implements Exception {
  WeatherException(this.message);
  final String message;
  @override
  String toString() => message;
}

String describeCode(int c) {
  if (c == 0) return 'Clear sky';
  if (c <= 3) return 'Partly cloudy';
  if (c == 45 || c == 48) return 'Fog';
  if (c >= 51 && c <= 57) return 'Drizzle';
  if (c >= 61 && c <= 67) return 'Rain';
  if (c >= 71 && c <= 77) return 'Snow';
  if (c >= 80 && c <= 82) return 'Rain showers';
  if (c >= 95) return 'Thunderstorm';
  return 'Unknown';
}

/// Uses Open-Meteo, which needs no API key. The client is injectable so tests can fake the network.
class WeatherService {
  WeatherService({http.Client? client}) : _client = client ?? http.Client();
  final http.Client _client;

  Future<Map<String, dynamic>> _getJson(Uri uri) async {
    final http.Response res;
    try {
      res = await _client.get(uri).timeout(const Duration(seconds: 10));
    } catch (_) {
      throw WeatherException('Could not reach the weather service. Check your connection.');
    }
    if (res.statusCode != 200) throw WeatherException('Weather service error (${res.statusCode}).');
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<Weather> forCity(String city) async {
    final name = city.trim();
    if (name.isEmpty) throw WeatherException('Enter a city name.');
    final geo = await _getJson(Uri.https('geocoding-api.open-meteo.com', '/v1/search', {'name': name, 'count': '1', 'format': 'json'}));
    final results = geo['results'] as List<dynamic>?;
    if (results == null || results.isEmpty) throw WeatherException('City not found: $name');
    final g = results.first as Map<String, dynamic>;
    final w = await _getJson(Uri.https('api.open-meteo.com', '/v1/forecast', {
      'latitude': '${g['latitude']}',
      'longitude': '${g['longitude']}',
      'current': 'temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m',
    }));
    final cur = w['current'] as Map<String, dynamic>;
    return Weather(
      city: '${g['name']}, ${g['country_code'] ?? ''}',
      temperature: (cur['temperature_2m'] as num).toDouble(),
      humidity: (cur['relative_humidity_2m'] as num).toInt(),
      code: (cur['weather_code'] as num).toInt(),
      windKmh: (cur['wind_speed_10m'] as num).toDouble(),
    );
  }
}
