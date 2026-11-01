# Flutter — Week 3: Backend Integration & Database

- **Public API data:** fetches and lists posts from JSONPlaceholder with loading and retry states.
- **Login page:** a sign-up/log-in/log-out screen written against an `AuthService` interface. The shipped implementation, `LocalAuthService`, is in-memory and is used for development and tests. **Firebase Auth was not connected**, because that needs your own Firebase project. To use it, run `flutterfire configure`, add `firebase_core` and `firebase_auth`, implement `AuthService` with `createUserWithEmailAndPassword`, `signInWithEmailAndPassword` and `signOut`, and pass it to `Week3App`.
- **Weather forecast app** (mini project): temperature, humidity, wind and a weather icon for any city, with a loading indicator and error handling. It uses Open-Meteo, which needs no API key, instead of OpenWeather, so there is no key in the repository.

Checked with `flutter analyze` (no issues) and `flutter test` (6 tests: service parsing and error paths with a mocked HTTP client, auth, and the three screens). `dart run tool/live_check.dart` calls the real Open-Meteo API. Platform folders are generated and left out: run `flutter create --project-name sn_week3 .` first.
