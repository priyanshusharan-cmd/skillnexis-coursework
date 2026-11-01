#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>

using namespace std;

unsigned long long factorial(unsigned n) {
    return n <= 1 ? 1ULL : n * factorial(n - 1);
}

void reverseArray(vector<int> &a) {
    for (size_t i = 0, j = a.size(); i + 1 < j; ++i, --j) {
        swap(a[i], a[j - 1]);
    }
}

int countVowels(const string &s) {
    int n = 0;
    for (unsigned char c : s) {
        c = static_cast<unsigned char>(tolower(c));
        if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u') {
            ++n;
        }
    }
    return n;
}

void bubbleSort(vector<int> &a) {
    for (size_t pass = 0; pass + 1 < a.size(); ++pass) {
        bool swapped = false;
        for (size_t i = 0; i + 1 < a.size() - pass; ++i) {
            if (a[i] > a[i + 1]) {
                swap(a[i], a[i + 1]);
                swapped = true;
            }
        }
        if (!swapped) {
            break;
        }
    }
}

void print(const string &label, const vector<int> &a) {
    cout << label;
    for (int x : a) {
        cout << ' ' << x;
    }
    cout << '\n';
}

// Mini project: student report generator using functions and arrays.
const int SUBJECTS = 3;

double average(const int marks[], int n) {
    int total = 0;
    for (int i = 0; i < n; ++i) {
        total += marks[i];
    }
    return static_cast<double>(total) / n;
}

char grade(double avg) {
    if (avg >= 90) return 'A';
    if (avg >= 75) return 'B';
    if (avg >= 60) return 'C';
    if (avg >= 40) return 'D';
    return 'F';
}

void report(const string names[], const int marks[][SUBJECTS], int students) {
    cout << left << setw(10) << "Name" << setw(7) << "Maths" << setw(9) << "Science"
         << setw(9) << "English" << setw(9) << "Average" << "Grade\n";
    for (int i = 0; i < students; ++i) {
        double avg = average(marks[i], SUBJECTS);
        cout << left << setw(10) << names[i];
        for (int j = 0; j < SUBJECTS; ++j) {
            cout << setw(j == 0 ? 7 : 9) << marks[i][j];
        }
        cout << setw(9) << fixed << setprecision(2) << avg << grade(avg) << '\n';
    }
}

int main() {
    cout << "1. factorial(5) = " << factorial(5) << ", factorial(0) = " << factorial(0)
         << ", factorial(20) = " << factorial(20) << '\n';

    vector<int> a = {1, 2, 3, 4, 5};
    print("2. Before reverse:", a);
    reverseArray(a);
    print("   After reverse: ", a);

    string text = "Functions and Arrays in C++";
    cout << "3. Vowels in \"" << text << "\" = " << countVowels(text) << '\n';

    vector<int> b = {64, 34, 25, 12, 22, 11, 90};
    print("4. Before bubble sort:", b);
    bubbleSort(b);
    print("   After bubble sort: ", b);

    cout << "\nStudent report\n";
    const string names[] = {"Asha", "Ravi", "Meera", "Kabir"};
    const int marks[][SUBJECTS] = {{95, 92, 91}, {70, 65, 80}, {55, 62, 58}, {30, 35, 28}};
    report(names, marks, 4);
    return 0;
}
