# Flutter — Week 2: Layouts, Navigation & State Management

One app with three entries on a home screen:

1. **To-Do list**, two screens: the task list and an Add Task screen (`TextField`), with `setState`, tick to complete and swipe to delete.
2. **Login and navigation demo**: form validation, `Navigator.push`/`pushReplacement`, a Drawer on the home page. It is UI only: any well-formed email with a password of 6 or more characters is accepted, and nothing is stored or sent.
3. **Expense tracker UI** (mini project): Dashboard, Add Expense and History screens with a bottom `NavigationBar` and local state.

Checked with `flutter analyze` (no issues) and `flutter test` (3 widget tests passing). The `android/`, `ios/` and `web/` folders are generated and left out; to run it, create them in this folder with `flutter create --project-name sn_week2 .` and then `flutter run`.
