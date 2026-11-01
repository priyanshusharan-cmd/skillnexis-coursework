import 'package:flutter/material.dart';

import 'weather_service.dart';

IconData iconForCode(int c) {
  if (c == 0) return Icons.wb_sunny;
  if (c <= 3) return Icons.cloud;
  if (c == 45 || c == 48) return Icons.foggy;
  if (c >= 51 && c <= 67 || c >= 80 && c <= 82) return Icons.water_drop;
  if (c >= 71 && c <= 77) return Icons.ac_unit;
  if (c >= 95) return Icons.thunderstorm;
  return Icons.help_outline;
}

/// Mini project: weather forecast app with a loading indicator and error handling.
class WeatherScreen extends StatefulWidget {
  const WeatherScreen({super.key, required this.service});
  final WeatherService service;

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  final _controller = TextEditingController();
  Future<Weather>? _future;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _search() {
    final future = widget.service.forCity(_controller.text);
    setState(() {
      _future = future;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Weather forecast')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          TextField(
            controller: _controller,
            textInputAction: TextInputAction.search,
            onSubmitted: (_) => _search(),
            decoration: InputDecoration(
              labelText: 'City',
              border: const OutlineInputBorder(),
              suffixIcon: IconButton(icon: const Icon(Icons.search), tooltip: 'Search', onPressed: _search),
            ),
          ),
          const SizedBox(height: 24),
          if (_future == null)
            const Text('Search for a city to see its weather.')
          else
            FutureBuilder<Weather>(
              future: _future,
              builder: (context, snap) {
                if (snap.connectionState != ConnectionState.done) return const CircularProgressIndicator();
                if (snap.hasError) {
                  return Text('${snap.error}', style: TextStyle(color: Theme.of(context).colorScheme.error));
                }
                final w = snap.data!;
                return Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(children: [
                      Text(w.city, style: Theme.of(context).textTheme.headlineSmall),
                      const SizedBox(height: 8),
                      Icon(iconForCode(w.code), size: 72),
                      Text('${w.temperature.round()}°C', style: Theme.of(context).textTheme.displayMedium),
                      Text(w.description),
                      const SizedBox(height: 8),
                      Text('Humidity ${w.humidity}%   Wind ${w.windKmh.round()} km/h'),
                    ]),
                  ),
                );
              },
            ),
        ]),
      ),
    );
  }
}
