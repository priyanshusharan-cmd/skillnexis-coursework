// Run with: dart run tool/live_check.dart   (needs internet access)
import 'dart:io';

import 'package:sn_week3/weather_service.dart';

Future<void> main() async {
  final service = WeatherService();
  final w = await service.forCity('Bengaluru');
  stdout.writeln('${w.city}: ${w.temperature}C, humidity ${w.humidity}%, ${w.description}');
  try {
    await service.forCity('zzzzqqqxxnotacity');
  } on WeatherException catch (e) {
    stdout.writeln('unknown city -> ${e.message}');
  }
}
