#include <cmath>
#include <iomanip>
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <utility>
#include <vector>

using namespace std;

// Assignment 1: Employee with salary calculation.
class Employee {
    string name_;
    double basic_;
    double hra_percent_;
    double da_percent_;

public:
    Employee(string name, double basic, double hra = 20, double da = 10)
        : name_(std::move(name)), basic_(basic), hra_percent_(hra), da_percent_(da) {}
    double salary() const { return basic_ + basic_ * hra_percent_ / 100 + basic_ * da_percent_ / 100; }
    const string &name() const { return name_; }
};

// Assignment 2: constructor overloading (+ destructor).
class Box {
    double l_, w_, h_;

public:
    Box() : l_(1), w_(1), h_(1) { cout << "  Box() default\n"; }
    explicit Box(double side) : l_(side), w_(side), h_(side) { cout << "  Box(side)\n"; }
    Box(double l, double w, double h) : l_(l), w_(w), h_(h) { cout << "  Box(l, w, h)\n"; }
    Box(const Box &o) : l_(o.l_), w_(o.w_), h_(o.h_) { cout << "  Box(copy)\n"; }
    ~Box() { cout << "  ~Box volume " << volume() << '\n'; }
    double volume() const { return l_ * w_ * h_; }
};

// Assignments 3 and 4: abstract base class with virtual functions, Rectangle and Circle.
class Shape {
public:
    virtual ~Shape() = default;
    virtual double area() const = 0;
    virtual double perimeter() const = 0;
    virtual string name() const = 0;
};

class Rectangle : public Shape {
    double w_, h_;

public:
    Rectangle(double w, double h) : w_(w), h_(h) {}
    double area() const override { return w_ * h_; }
    double perimeter() const override { return 2 * (w_ + h_); }
    string name() const override { return "Rectangle"; }
};

class Circle : public Shape {
    double r_;

public:
    explicit Circle(double r) : r_(r) {}
    double area() const override { return M_PI * r_ * r_; }
    double perimeter() const override { return 2 * M_PI * r_; }
    string name() const override { return "Circle"; }
};

// Mini project: library management system.
class Book {
    int id_;
    string title_;
    string author_;
    bool issued_ = false;

public:
    Book(int id, string title, string author) : id_(id), title_(std::move(title)), author_(std::move(author)) {}
    int id() const { return id_; }
    bool issued() const { return issued_; }
    void setIssued(bool v) { issued_ = v; }
    string describe() const {
        return "#" + to_string(id_) + " " + title_ + " by " + author_ + (issued_ ? " [issued]" : " [available]");
    }
};

class Library {
    vector<Book> books_;
    map<string, vector<int>> loans_;

    Book *find(int id) {
        for (auto &b : books_) {
            if (b.id() == id) return &b;
        }
        return nullptr;
    }

public:
    void add(const Book &b) { books_.push_back(b); }
    bool issue(int id, const string &member) {
        Book *b = find(id);
        if (b == nullptr || b->issued()) return false;
        b->setIssued(true);
        loans_[member].push_back(id);
        return true;
    }
    bool giveBack(int id, const string &member) {
        Book *b = find(id);
        auto it = loans_.find(member);
        if (b == nullptr || !b->issued() || it == loans_.end()) return false;
        auto &v = it->second;
        for (size_t i = 0; i < v.size(); ++i) {
            if (v[i] == id) {
                v.erase(v.begin() + static_cast<long>(i));
                b->setIssued(false);
                return true;
            }
        }
        return false;
    }
    void list() const {
        for (const auto &b : books_) cout << "  " << b.describe() << '\n';
    }
};

int main() {
    cout << fixed << setprecision(2);

    Employee e("Asha", 50000);
    Employee e2("Ravi", 40000, 25, 12);
    cout << "1. " << e.name() << " salary = " << e.salary() << ", " << e2.name() << " salary = " << e2.salary() << '\n';

    cout << "2. Constructor overloading\n";
    {
        Box a;
        Box b(2);
        Box c(2, 3, 4);
        Box d = c;
        cout << "  volumes: " << a.volume() << ' ' << b.volume() << ' ' << c.volume() << ' ' << d.volume() << '\n';
    }

    cout << "3-4. Polymorphism through an abstract Shape\n";
    vector<unique_ptr<Shape>> shapes;
    shapes.push_back(make_unique<Rectangle>(3, 4));
    shapes.push_back(make_unique<Circle>(2));
    for (const auto &s : shapes) {
        cout << "  " << s->name() << " area=" << s->area() << " perimeter=" << s->perimeter() << '\n';
    }

    cout << "Library management\n";
    Library lib;
    lib.add(Book(1, "The C++ Programming Language", "Stroustrup"));
    lib.add(Book(2, "Effective Modern C++", "Meyers"));
    lib.add(Book(3, "Clean Code", "Martin"));
    cout << "issue 2 to asha: " << (lib.issue(2, "asha") ? "ok" : "failed") << '\n';
    cout << "issue 2 to ravi: " << (lib.issue(2, "ravi") ? "ok" : "failed") << '\n';
    cout << "issue 9 to ravi: " << (lib.issue(9, "ravi") ? "ok" : "failed") << '\n';
    lib.list();
    cout << "return 2 by ravi: " << (lib.giveBack(2, "ravi") ? "ok" : "failed") << '\n';
    cout << "return 2 by asha: " << (lib.giveBack(2, "asha") ? "ok" : "failed") << '\n';
    lib.list();
    return 0;
}
