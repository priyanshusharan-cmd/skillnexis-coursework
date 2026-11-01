#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

// Assignment 1: write data into a file and read it back.
void writeAndRead(const string &path) {
    {
        ofstream out(path);
        if (!out) throw runtime_error("cannot open " + path + " for writing");
        out << "line one\nline two\nline three\n";
    }
    ifstream in(path);
    if (!in) throw runtime_error("cannot open " + path + " for reading");
    string line;
    int n = 0;
    while (getline(in, line)) {
        cout << "  " << ++n << ": " << line << '\n';
    }
}

// Assignment 2: store N elements in a vector and sort them.
vector<int> sortedCopy(vector<int> v) {
    sort(v.begin(), v.end());
    return v;
}

// Assignment 4: division with exception handling.
double divide(double a, double b) {
    if (b == 0) throw invalid_argument("division by zero");
    return a / b;
}

// Mini project: employee record saver using file handling and the STL.
struct Employee {
    int id;
    string name;
    string role;
    double salary;
};

void saveEmployees(const string &path, const map<int, Employee> &emps) {
    ofstream out(path);
    if (!out) throw runtime_error("cannot write " + path);
    for (const auto &kv : emps) {
        const Employee &e = kv.second;
        out << e.id << ',' << e.name << ',' << e.role << ',' << e.salary << '\n';
    }
}

map<int, Employee> loadEmployees(const string &path) {
    map<int, Employee> emps;
    ifstream in(path);
    if (!in) return emps;
    string line;
    while (getline(in, line)) {
        stringstream ss(line);
        string id, name, role, salary;
        if (getline(ss, id, ',') && getline(ss, name, ',') && getline(ss, role, ',') && getline(ss, salary)) {
            Employee e{stoi(id), name, role, stod(salary)};
            emps[e.id] = e;
        }
    }
    return emps;
}

int main() {
    const string base = "week4_";
    cout << "1. File write and read\n";
    writeAndRead(base + "demo.txt");

    cout << "2. Vector sort\n";
    vector<int> v = {42, 7, 19, 3, 88, 7};
    cout << "  input: ";
    for (int x : v) cout << x << ' ';
    cout << "\n  sorted: ";
    for (int x : sortedCopy(v)) cout << x << ' ';
    set<int> unique(v.begin(), v.end());
    cout << "\n  set of unique values: ";
    for (int x : unique) cout << x << ' ';
    cout << '\n';

    cout << "3. Map of roll number to name\n";
    map<int, string> students = {{102, "Ravi"}, {101, "Asha"}, {103, "Meera"}};
    for (const auto &kv : students) cout << "  " << kv.first << " -> " << kv.second << '\n';
    auto it = students.find(102);
    cout << "  lookup 102: " << (it != students.end() ? it->second : "not found") << '\n';
    cout << "  lookup 999: " << (students.count(999) ? students.at(999) : "not found") << '\n';

    cout << "4. Exception handling\n";
    for (double d : {4.0, 0.0}) {
        try {
            double q = divide(10, d);
            cout << "  10 / " << d << " = " << q << '\n';
        } catch (const invalid_argument &e) {
            cout << "  caught: " << e.what() << '\n';
        }
    }

    cout << "Employee record saver\n";
    const string db = base + "employees.csv";
    map<int, Employee> emps = loadEmployees(db);
    int next = emps.empty() ? 1 : emps.rbegin()->first + 1;
    emps[next] = Employee{next, "Asha", "Engineer", 85000};
    emps[next + 1] = Employee{next + 1, "Ravi", "Designer", 62000.5};
    saveEmployees(db, emps);
    for (const auto &kv : loadEmployees(db)) {
        const Employee &e = kv.second;
        cout << "  " << e.id << ' ' << e.name << ' ' << e.role << ' ' << e.salary << '\n';
    }
    return 0;
}
