#include <iostream>
#include <string>
#include <vector>

using namespace std;

struct TreeNode {
    int key;
    TreeNode *left = nullptr, *right = nullptr;
    explicit TreeNode(int k) : key(k) {}
};

class BST {
    TreeNode *root_ = nullptr;

    static TreeNode *insert(TreeNode *n, int k) {
        if (n == nullptr) return new TreeNode(k);
        if (k < n->key) n->left = insert(n->left, k);
        else if (k > n->key) n->right = insert(n->right, k);
        return n;
    }
    static bool contains(const TreeNode *n, int k) {
        while (n != nullptr) {
            if (k == n->key) return true;
            n = k < n->key ? n->left : n->right;
        }
        return false;
    }
    static void inorder(const TreeNode *n, vector<int> &out) {
        if (!n) return;
        inorder(n->left, out);
        out.push_back(n->key);
        inorder(n->right, out);
    }
    static void preorder(const TreeNode *n, vector<int> &out) {
        if (!n) return;
        out.push_back(n->key);
        preorder(n->left, out);
        preorder(n->right, out);
    }
    static void postorder(const TreeNode *n, vector<int> &out) {
        if (!n) return;
        postorder(n->left, out);
        postorder(n->right, out);
        out.push_back(n->key);
    }
    static void destroy(TreeNode *n) {
        if (!n) return;
        destroy(n->left);
        destroy(n->right);
        delete n;
    }

public:
    BST() = default;
    BST(const BST &) = delete;
    BST &operator=(const BST &) = delete;
    ~BST() { destroy(root_); }
    void insert(int k) { root_ = insert(root_, k); }
    bool contains(int k) const { return contains(root_, k); }
    vector<int> inorder() const { vector<int> v; inorder(root_, v); return v; }
    vector<int> preorder() const { vector<int> v; preorder(root_, v); return v; }
    vector<int> postorder() const { vector<int> v; postorder(root_, v); return v; }
};

void show(const string &label, const vector<int> &v) {
    cout << "  " << label << ':';
    for (int x : v) cout << ' ' << x;
    cout << '\n';
}

// Assignments 3 and 4: hash map using arrays, with linear probing.
class HashTable {
    enum State { EMPTY, USED, DELETED };
    struct Slot {
        State state = EMPTY;
        int key = 0;
        string value;
    };
    vector<Slot> slots_;
    size_t used_ = 0;

    size_t hash(int key) const { return static_cast<size_t>(key < 0 ? -key : key) % slots_.size(); }

public:
    explicit HashTable(size_t cap) : slots_(cap) {}
    bool put(int key, const string &value) {
        size_t i = hash(key);
        for (size_t probes = 0; probes < slots_.size(); ++probes, i = (i + 1) % slots_.size()) {
            if (slots_[i].state == USED && slots_[i].key == key) {
                slots_[i].value = value;
                return true;
            }
            if (slots_[i].state != USED) {
                slots_[i] = {USED, key, value};
                ++used_;
                return true;
            }
        }
        return false;
    }
    const string *get(int key) const {
        size_t i = hash(key);
        for (size_t probes = 0; probes < slots_.size(); ++probes, i = (i + 1) % slots_.size()) {
            if (slots_[i].state == EMPTY) return nullptr;
            if (slots_[i].state == USED && slots_[i].key == key) return &slots_[i].value;
        }
        return nullptr;
    }
    bool remove(int key) {
        size_t i = hash(key);
        for (size_t probes = 0; probes < slots_.size(); ++probes, i = (i + 1) % slots_.size()) {
            if (slots_[i].state == EMPTY) return false;
            if (slots_[i].state == USED && slots_[i].key == key) {
                slots_[i].state = DELETED;
                --used_;
                return true;
            }
        }
        return false;
    }
    void display() const {
        for (size_t i = 0; i < slots_.size(); ++i) {
            cout << "  [" << i << "] ";
            if (slots_[i].state == USED) cout << slots_[i].key << " => " << slots_[i].value << " (home " << hash(slots_[i].key) << ")";
            else cout << (slots_[i].state == DELETED ? "<deleted>" : "-");
            cout << '\n';
        }
    }
};

// Mini project: contact directory on a BST keyed by name.
struct Contact {
    string name, phone;
    Contact *left = nullptr, *right = nullptr;
};

class Directory {
    Contact *root_ = nullptr;

    static Contact *insert(Contact *n, const string &name, const string &phone) {
        if (!n) return new Contact{name, phone};
        if (name < n->name) n->left = insert(n->left, name, phone);
        else if (name > n->name) n->right = insert(n->right, name, phone);
        else n->phone = phone;
        return n;
    }
    static Contact *minNode(Contact *n) {
        while (n->left) n = n->left;
        return n;
    }
    static Contact *erase(Contact *n, const string &name, bool &removed) {
        if (!n) return nullptr;
        if (name < n->name) n->left = erase(n->left, name, removed);
        else if (name > n->name) n->right = erase(n->right, name, removed);
        else {
            removed = true;
            if (!n->left || !n->right) {
                Contact *child = n->left ? n->left : n->right;
                delete n;
                return child;
            }
            Contact *s = minNode(n->right);
            n->name = s->name;
            n->phone = s->phone;
            bool dummy = false;
            n->right = erase(n->right, s->name, dummy);
        }
        return n;
    }
    static void inorder(const Contact *n) {
        if (!n) return;
        inorder(n->left);
        cout << "  " << n->name << " : " << n->phone << '\n';
        inorder(n->right);
    }
    static void destroy(Contact *n) {
        if (!n) return;
        destroy(n->left);
        destroy(n->right);
        delete n;
    }

public:
    Directory() = default;
    Directory(const Directory &) = delete;
    Directory &operator=(const Directory &) = delete;
    ~Directory() { destroy(root_); }
    void add(const string &name, const string &phone) { root_ = insert(root_, name, phone); }
    const Contact *find(const string &name) const {
        const Contact *n = root_;
        while (n && n->name != name) n = name < n->name ? n->left : n->right;
        return n;
    }
    bool remove(const string &name) {
        bool removed = false;
        root_ = erase(root_, name, removed);
        return removed;
    }
    void list() const { inorder(root_); }
};

int main() {
    cout << "1. Binary search tree\n";
    BST t;
    for (int k : {50, 30, 70, 20, 40, 60, 80, 30}) t.insert(k);
    cout << "  search 60: " << (t.contains(60) ? "found" : "not found") << ", search 65: " << (t.contains(65) ? "found" : "not found") << '\n';

    cout << "2. Recursive traversals\n";
    show("inorder  ", t.inorder());
    show("preorder ", t.preorder());
    show("postorder", t.postorder());

    cout << "3-4. Hash table with linear probing (capacity 7)\n";
    HashTable h(7);
    h.put(10, "ten");
    h.put(17, "seventeen");   // collides with 10 (both hash to 3)
    h.put(24, "twenty-four"); // collides again
    h.put(5, "five");
    h.put(10, "TEN");          // update in place
    h.display();
    const string *v = h.get(24);
    cout << "  get(24) = " << (v ? *v : "missing") << ", get(99) = " << (h.get(99) ? "found" : "missing") << '\n';
    h.remove(17);
    cout << "  after removing 17, get(24) still = " << *h.get(24) << " (tombstone keeps the probe chain)\n";

    cout << "Contact directory (BST)\n";
    Directory d;
    d.add("Meera", "98100 00003");
    d.add("Asha", "98100 00001");
    d.add("Ravi", "98100 00002");
    d.add("Kabir", "98100 00004");
    d.list();
    const Contact *c = d.find("Ravi");
    cout << "  search Ravi: " << (c ? c->phone : "not found") << ", search Zed: " << (d.find("Zed") ? "found" : "not found") << '\n';
    cout << "  delete Meera (two children?): " << d.remove("Meera") << ", delete Zed: " << d.remove("Zed") << '\n';
    d.list();
    return 0;
}
