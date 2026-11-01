#include <algorithm>
#include <climits>
#include <iostream>
#include <map>
#include <queue>
#include <string>
#include <vector>

using namespace std;

struct Graph {
    int n;
    vector<vector<pair<int, int>>> adj;  // (neighbour, weight)
    explicit Graph(int nodes) : n(nodes), adj(static_cast<size_t>(nodes)) {}
    void addEdge(int a, int b, int w = 1) {
        adj[static_cast<size_t>(a)].push_back({b, w});
        adj[static_cast<size_t>(b)].push_back({a, w});
    }
};

vector<int> bfs(const Graph &g, int start) {
    vector<int> order;
    vector<bool> seen(static_cast<size_t>(g.n), false);
    queue<int> q;
    q.push(start);
    seen[static_cast<size_t>(start)] = true;
    while (!q.empty()) {
        int u = q.front();
        q.pop();
        order.push_back(u);
        for (auto [v, w] : g.adj[static_cast<size_t>(u)]) {
            (void)w;
            if (!seen[static_cast<size_t>(v)]) {
                seen[static_cast<size_t>(v)] = true;
                q.push(v);
            }
        }
    }
    return order;
}

void dfsVisit(const Graph &g, int u, vector<bool> &seen, vector<int> &order) {
    seen[static_cast<size_t>(u)] = true;
    order.push_back(u);
    for (auto [v, w] : g.adj[static_cast<size_t>(u)]) {
        (void)w;
        if (!seen[static_cast<size_t>(v)]) dfsVisit(g, v, seen, order);
    }
}

vector<int> dfs(const Graph &g, int start) {
    vector<int> order;
    vector<bool> seen(static_cast<size_t>(g.n), false);
    dfsVisit(g, start, seen, order);
    return order;
}

// Dijkstra with a min-heap; returns distances and the predecessor array.
pair<vector<int>, vector<int>> dijkstra(const Graph &g, int src) {
    vector<int> dist(static_cast<size_t>(g.n), INT_MAX), prev(static_cast<size_t>(g.n), -1);
    priority_queue<pair<int, int>, vector<pair<int, int>>, greater<>> pq;
    dist[static_cast<size_t>(src)] = 0;
    pq.push({0, src});
    while (!pq.empty()) {
        auto [d, u] = pq.top();
        pq.pop();
        if (d > dist[static_cast<size_t>(u)]) continue;
        for (auto [v, w] : g.adj[static_cast<size_t>(u)]) {
            if (d + w < dist[static_cast<size_t>(v)]) {
                dist[static_cast<size_t>(v)] = d + w;
                prev[static_cast<size_t>(v)] = u;
                pq.push({dist[static_cast<size_t>(v)], v});
            }
        }
    }
    return {dist, prev};
}

// Fibonacci: memoization (top-down) and tabulation (bottom-up).
unsigned long long fibMemo(int n, vector<long long> &memo) {
    if (n < 2) return static_cast<unsigned long long>(n);
    if (memo[static_cast<size_t>(n)] != -1) return static_cast<unsigned long long>(memo[static_cast<size_t>(n)]);
    memo[static_cast<size_t>(n)] = static_cast<long long>(fibMemo(n - 1, memo) + fibMemo(n - 2, memo));
    return static_cast<unsigned long long>(memo[static_cast<size_t>(n)]);
}

unsigned long long fibTab(int n) {
    if (n < 2) return static_cast<unsigned long long>(n);
    vector<unsigned long long> t(static_cast<size_t>(n) + 1);
    t[0] = 0;
    t[1] = 1;
    for (size_t i = 2; i <= static_cast<size_t>(n); ++i) t[i] = t[i - 1] + t[i - 2];
    return t[static_cast<size_t>(n)];
}

// 0/1 knapsack, also reporting which items were taken.
pair<int, vector<int>> knapsack(const vector<int> &wt, const vector<int> &val, int cap) {
    size_t n = wt.size();
    vector<vector<int>> dp(n + 1, vector<int>(static_cast<size_t>(cap) + 1, 0));
    for (size_t i = 1; i <= n; ++i) {
        for (int c = 0; c <= cap; ++c) {
            dp[i][static_cast<size_t>(c)] = dp[i - 1][static_cast<size_t>(c)];
            if (wt[i - 1] <= c) {
                dp[i][static_cast<size_t>(c)] = max(dp[i][static_cast<size_t>(c)], dp[i - 1][static_cast<size_t>(c - wt[i - 1])] + val[i - 1]);
            }
        }
    }
    vector<int> taken;
    int c = cap;
    for (size_t i = n; i > 0; --i) {
        if (dp[i][static_cast<size_t>(c)] != dp[i - 1][static_cast<size_t>(c)]) {
            taken.push_back(static_cast<int>(i - 1));
            c -= wt[i - 1];
        }
    }
    reverse(taken.begin(), taken.end());
    return {dp[n][static_cast<size_t>(cap)], taken};
}

void print(const string &label, const vector<int> &v) {
    cout << "  " << label << ':';
    for (int x : v) cout << ' ' << x;
    cout << '\n';
}

int main() {
    cout << "1. BFS and DFS from node 0\n";
    Graph g(7);
    for (auto e : vector<pair<int, int>>{{0, 1}, {0, 2}, {1, 3}, {1, 4}, {2, 5}, {2, 6}}) g.addEdge(e.first, e.second);
    print("BFS", bfs(g, 0));
    print("DFS", dfs(g, 0));

    cout << "2. Dijkstra shortest paths from node 0\n";
    Graph w(5);
    w.addEdge(0, 1, 4);
    w.addEdge(0, 2, 1);
    w.addEdge(2, 1, 2);
    w.addEdge(1, 3, 1);
    w.addEdge(2, 3, 5);
    w.addEdge(3, 4, 3);
    auto [dist, prev] = dijkstra(w, 0);
    for (int i = 0; i < w.n; ++i) cout << "  0 -> " << i << " = " << dist[static_cast<size_t>(i)] << '\n';

    cout << "3. Fibonacci\n";
    vector<long long> memo(91, -1);
    cout << "  fib(10): memo=" << fibMemo(10, memo) << " tab=" << fibTab(10) << "; fib(90): memo=" << fibMemo(90, memo) << " tab=" << fibTab(90) << '\n';

    cout << "4. 0/1 knapsack\n";
    auto [best, items] = knapsack({1, 3, 4, 5}, {1, 4, 5, 7}, 7);
    cout << "  weights {1,3,4,5} values {1,4,5,7} capacity 7 -> best value " << best << ", items";
    for (int i : items) cout << ' ' << i;
    cout << '\n';

    cout << "City path finder\n";
    vector<string> cities = {"Bengaluru", "Mysuru", "Chennai", "Hyderabad", "Mumbai", "Pune"};
    map<string, int> id;
    for (size_t i = 0; i < cities.size(); ++i) id[cities[i]] = static_cast<int>(i);
    Graph roads(static_cast<int>(cities.size()));
    struct Road { const char *a, *b; int km; };
    for (Road r : {Road{"Bengaluru", "Mysuru", 150}, Road{"Bengaluru", "Chennai", 345}, Road{"Bengaluru", "Hyderabad", 570},
                   Road{"Chennai", "Hyderabad", 625}, Road{"Hyderabad", "Pune", 560}, Road{"Hyderabad", "Mumbai", 710}, Road{"Pune", "Mumbai", 150},
                   Road{"Bengaluru", "Pune", 840}}) {
        roads.addEdge(id[r.a], id[r.b], r.km);
    }
    for (auto [from, to] : vector<pair<string, string>>{{"Mysuru", "Mumbai"}, {"Chennai", "Pune"}}) {
        auto [d, p] = dijkstra(roads, id[from]);
        vector<string> path;
        for (int at = id[to]; at != -1; at = p[static_cast<size_t>(at)]) path.push_back(cities[static_cast<size_t>(at)]);
        reverse(path.begin(), path.end());
        cout << "  " << from << " -> " << to << ": " << d[static_cast<size_t>(id[to])] << " km via ";
        for (size_t i = 0; i < path.size(); ++i) cout << path[i] << (i + 1 < path.size() ? " > " : "");
        cout << '\n';
    }
    return 0;
}
