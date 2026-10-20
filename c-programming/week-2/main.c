#include <ctype.h>
#include <errno.h>
#include <limits.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_ITEMS 100
#define MAX_DIM 10

static int read_line(char *s, size_t size) {
    if (fgets(s, (int)size, stdin) == NULL) return 0;
    size_t n = strlen(s);
    if (n && s[n - 1] == '\n') s[n - 1] = '\0';
    else { int c; while ((c = getchar()) != '\n' && c != EOF) {} }
    return 1;
}

static int read_int(const char *prompt, int *value) {
    char line[128], *end;
    for (;;) {
        printf("%s", prompt);
        if (!read_line(line, sizeof line)) return 0;
        errno = 0;
        long n = strtol(line, &end, 10);
        while (isspace((unsigned char)*end)) end++;
        if (!errno && end != line && *end == '\0' && n >= INT_MIN && n <= INT_MAX) {
            *value = (int)n; return 1;
        }
        puts("Please enter a whole number.");
    }
}

static int read_range(const char *prompt, int low, int high, int *value) {
    for (;;) {
        if (!read_int(prompt, value)) return 0;
        if (*value >= low && *value <= high) return 1;
        printf("Enter a value from %d to %d.\n", low, high);
    }
}

static int read_array(int a[], int *n) {
    if (!read_range("Number of elements (1-100): ", 1, MAX_ITEMS, n)) return 0;
    for (int i = 0; i < *n; i++) {
        char prompt[48];
        snprintf(prompt, sizeof prompt, "Element %d: ", i + 1);
        if (!read_int(prompt, &a[i])) return 0;
    }
    return 1;
}

static void largest_element(void) {
    int a[MAX_ITEMS], n;
    if (!read_array(a, &n)) return;
    int largest = a[0];
    for (int i = 1; i < n; i++) if (a[i] > largest) largest = a[i];
    printf("Largest element: %d\n", largest);
}

static void count_signs(void) {
    int a[MAX_ITEMS], n, positive = 0, negative = 0, zero = 0;
    if (!read_array(a, &n)) return;
    for (int i = 0; i < n; i++) {
        if (a[i] > 0) positive++;
        else if (a[i] < 0) negative++;
        else zero++;
    }
    printf("Positive: %d\nNegative: %d\nZero: %d\n", positive, negative, zero);
}

static unsigned long long factorial(unsigned int n) {
    return n < 2 ? 1ULL : n * factorial(n - 1);
}

static void show_factorial(void) {
    int n;
    if (read_range("Enter a whole number (0-20): ", 0, 20, &n))
        printf("%d! = %llu\n", n, factorial((unsigned int)n));
}

static void add_matrices(void) {
    int a[MAX_DIM][MAX_DIM], b[MAX_DIM][MAX_DIM], rows, cols;
    if (!read_range("Rows (1-10): ", 1, MAX_DIM, &rows) ||
        !read_range("Columns (1-10): ", 1, MAX_DIM, &cols)) return;
    puts("Enter the first matrix:");
    for (int r = 0; r < rows; r++) for (int c = 0; c < cols; c++) {
        char p[48]; snprintf(p, sizeof p, "A[%d][%d]: ", r + 1, c + 1);
        if (!read_int(p, &a[r][c])) return;
    }
    puts("Enter the second matrix:");
    for (int r = 0; r < rows; r++) for (int c = 0; c < cols; c++) {
        char p[48]; snprintf(p, sizeof p, "B[%d][%d]: ", r + 1, c + 1);
        if (!read_int(p, &b[r][c])) return;
    }
    puts("Sum matrix:");
    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++)
            printf("%lld%s", (long long)a[r][c] + b[r][c], c + 1 == cols ? "\n" : "\t");
    }
}

static double average(const int marks[], int count) {
    int total = 0;
    for (int i = 0; i < count; i++) total += marks[i];
    return (double)total / count;
}

static void student_average(void) {
    int marks[MAX_ITEMS], count;
    if (!read_range("Number of subjects (1-100): ", 1, MAX_ITEMS, &count)) return;
    for (int i = 0; i < count; i++) {
        char p[64]; snprintf(p, sizeof p, "Mark for subject %d (0-100): ", i + 1);
        if (!read_range(p, 0, 100, &marks[i])) return;
    }
    printf("Student average: %.2f%%\n", average(marks, count));
}

int main(void) {
    for (;;) {
        int choice;
        puts("\nC Programming — Week 2: Arrays & Functions");
        puts("1) Largest element in an array");
        puts("2) Count positive and negative numbers");
        puts("3) Factorial using a function");
        puts("4) Add two matrices");
        puts("5) Student average calculator");
        puts("6) Exit");
        if (!read_range("Choose an option (1-6): ", 1, 6, &choice)) return 0;
        switch (choice) {
            case 1: largest_element(); break;
            case 2: count_signs(); break;
            case 3: show_factorial(); break;
            case 4: add_matrices(); break;
            case 5: student_average(); break;
            case 6: return 0;
        }
    }
}
