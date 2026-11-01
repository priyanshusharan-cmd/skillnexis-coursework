# Flutter — Week 4: Capstone (Option 3, Student Attendance App)

- **Admin:** add and remove students. Blank and duplicate names are rejected.
- **Attendance:** pick a date and tick who was present. Records are date-wise.
- **Report:** days present out of days recorded, per student, as a percentage.
- **Local database:** everything is saved as JSON in `SharedPreferences` and restored on start. Corrupt stored data is ignored.
- **Theming:** light, dark and system modes, remembered between launches.

Admin and student views are not separated by login; one person uses all three tabs. There is no sign-in, so this is not suitable for real access control.

Checked with `flutter analyze` (no issues), `flutter test` (4 tests including persistence across a restart) and `flutter build web` (release build succeeded). **Not done:** an Android APK build, Play Store steps, and Firebase push notifications (listed under the week's topics), because they need an Android SDK and your own accounts. Platform folders are generated and left out: run `flutter create --project-name sn_week4 .` first.
