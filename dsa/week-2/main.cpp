#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace std;

// Assignment 1: singly linked list with insert and delete.
struct Node {
    int data;
    Node *next;
    explicit Node(int d, Node *n = nullptr) : data(d), next(n) {}
};

class LinkedList {
    Node *head_ = nullptr;

public:
    LinkedList() = default;
    LinkedList(const LinkedList &) = delete;
    LinkedList &operator=(const LinkedList &) = delete;
    ~LinkedList() {
        while (head_ != nullptr) {
            Node *n = head_;
            head_ = head_->next;
            delete n;
        }
    }
    void insertFront(int v) { head_ = new Node(v, head_); }
    void insertBack(int v) {
        Node **p = &head_;
        while (*p != nullptr) p = &(*p)->next;
        *p = new Node(v);
    }
    bool remove(int v) {
        for (Node **p = &head_; *p != nullptr; p = &(*p)->next) {
            if ((*p)->data == v) {
                Node *dead = *p;
                *p = dead->next;
                delete dead;
                return true;
            }
        }
        return false;
    }
    void print() const {
        for (Node *n = head_; n != nullptr; n = n->next) cout << n->data << (n->next ? " -> " : "");
        cout << (head_ ? "" : "(empty)") << '\n';
    }
    // Assignment 4: reverse using stack logic (push every value, pop back in reverse order).
    void reverseUsingStack();
    friend class LinkedStack;
    Node *head() const { return head_; }
};

// Assignment 2: stack using a linked list.
class LinkedStack {
    Node *top_ = nullptr;
    size_t size_ = 0;

public:
    LinkedStack() = default;
    LinkedStack(const LinkedStack &) = delete;
    LinkedStack &operator=(const LinkedStack &) = delete;
    ~LinkedStack() {
        while (!empty()) pop();
    }
    void push(int v) {
        top_ = new Node(v, top_);
        ++size_;
    }
    int pop() {
        if (empty()) throw underflow_error("stack underflow");
        Node *n = top_;
        int v = n->data;
        top_ = n->next;
        delete n;
        --size_;
        return v;
    }
    int peek() const {
        if (empty()) throw underflow_error("stack is empty");
        return top_->data;
    }
    bool empty() const { return top_ == nullptr; }
    size_t size() const { return size_; }
};

void LinkedList::reverseUsingStack() {
    LinkedStack s;
    for (Node *n = head_; n != nullptr; n = n->next) s.push(n->data);
    for (Node *n = head_; n != nullptr; n = n->next) n->data = s.pop();
}

// Assignment 3: queue using an array (circular, fixed capacity).
class ArrayQueue {
    vector<int> buf_;
    size_t head_ = 0, count_ = 0;

public:
    explicit ArrayQueue(size_t cap) : buf_(cap) {}
    bool full() const { return count_ == buf_.size(); }
    bool empty() const { return count_ == 0; }
    void enqueue(int v) {
        if (full()) throw overflow_error("queue overflow");
        buf_[(head_ + count_++) % buf_.size()] = v;
    }
    int dequeue() {
        if (empty()) throw underflow_error("queue underflow");
        int v = buf_[head_];
        head_ = (head_ + 1) % buf_.size();
        --count_;
        return v;
    }
};

// Mini project: undo/redo text editor simulation using two stacks.
class Editor {
    string text_;
    vector<string> undo_, redo_;

public:
    void type(const string &s) {
        undo_.push_back(text_);
        redo_.clear();
        text_ += s;
    }
    bool undo() {
        if (undo_.empty()) return false;
        redo_.push_back(text_);
        text_ = undo_.back();
        undo_.pop_back();
        return true;
    }
    bool redo() {
        if (redo_.empty()) return false;
        undo_.push_back(text_);
        text_ = redo_.back();
        redo_.pop_back();
        return true;
    }
    const string &text() const { return text_; }
};

int main() {
    cout << "1. Singly linked list\n  ";
    LinkedList list;
    for (int v : {10, 20, 30}) list.insertBack(v);
    list.insertFront(5);
    list.print();
    cout << "  delete 20: " << list.remove(20) << ", delete 99: " << list.remove(99) << "\n  ";
    list.print();

    cout << "2. Stack using a linked list\n";
    LinkedStack st;
    for (int v : {1, 2, 3}) st.push(v);
    cout << "  peek=" << st.peek() << " size=" << st.size() << " pops:";
    while (!st.empty()) cout << ' ' << st.pop();
    try {
        st.pop();
    } catch (const underflow_error &e) {
        cout << "\n  caught: " << e.what() << '\n';
    }

    cout << "3. Queue using an array (capacity 3)\n  ";
    ArrayQueue q(3);
    q.enqueue(1);
    q.enqueue(2);
    q.enqueue(3);
    try {
        q.enqueue(4);
    } catch (const overflow_error &e) {
        cout << "caught: " << e.what() << "; ";
    }
    cout << "dequeued " << q.dequeue() << ' ';
    q.enqueue(4);
    cout << "then wrap-around: " << q.dequeue() << ' ' << q.dequeue() << ' ' << q.dequeue() << '\n';

    cout << "4. Reverse a linked list using stack logic\n  before: ";
    list.print();
    list.reverseUsingStack();
    cout << "  after:  ";
    list.print();

    cout << "Undo/redo editor\n";
    Editor ed;
    ed.type("Hello");
    ed.type(", world");
    ed.type("!");
    cout << "  typed:  \"" << ed.text() << "\"\n";
    ed.undo();
    ed.undo();
    cout << "  undo x2: \"" << ed.text() << "\"\n";
    ed.redo();
    cout << "  redo:    \"" << ed.text() << "\"\n";
    ed.type(" there");
    cout << "  new edit clears redo: redo() -> " << (ed.redo() ? "applied" : "nothing to redo") << ", text \"" << ed.text() << "\"\n";
    return 0;
}
