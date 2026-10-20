#include <ctype.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int read_line(char *buffer, size_t size) {
    if (fgets(buffer, (int)size, stdin) == NULL) {
        return 0;
    }
    size_t length = strlen(buffer);
    if (length > 0 && buffer[length - 1] == '\n') {
        buffer[length - 1] = '\0';
    } else {
        int character;
        while ((character = getchar()) != '\n' && character != EOF) {
        }
    }
    return 1;
}

static int read_int(const char *prompt, int *value) {
    char line[128];
    char *end = NULL;
    printf("%s", prompt);
    if (!read_line(line, sizeof line)) {
        return 0;
    }
    errno = 0;
    long parsed = strtol(line, &end, 10);
    while (end != NULL && isspace((unsigned char)*end)) {
        end++;
    }
    if (errno != 0 || end == line || *end != '\0' || parsed < -2147483647L - 1 || parsed > 2147483647L) {
        printf("Please enter a whole number.\n");
        return -1;
    }
    *value = (int)parsed;
    return 1;
}

static int read_double(const char *prompt, double *value) {
    char line[128];
    char *end = NULL;
    printf("%s", prompt);
    if (!read_line(line, sizeof line)) {
        return 0;
    }
    errno = 0;
    double parsed = strtod(line, &end);
    while (end != NULL && isspace((unsigned char)*end)) {
        end++;
    }
    if (errno != 0 || end == line || *end != '\0') {
        printf("Please enter a valid number.\n");
        return -1;
    }
    *value = parsed;
    return 1;
}

static void sum_two_numbers(void) {
    int first;
    int second;
    int status = read_int("First integer: ", &first);
    if (status <= 0) return;
    status = read_int("Second integer: ", &second);
    if (status <= 0) return;
    printf("Sum: %d\n", first + second);
}

static void check_even_or_odd(void) {
    int number;
    int status = read_int("Enter an integer: ", &number);
    if (status <= 0) return;
    printf("%d is %s.\n", number, number % 2 == 0 ? "even" : "odd");
}

static void print_fibonacci(void) {
    int terms;
    int status = read_int("Number of terms (0-46): ", &terms);
    if (status <= 0) return;
    if (terms < 0 || terms > 46) {
        printf("Choose a number from 0 to 46 so the values fit in a signed integer.\n");
        return;
    }

    int first = 0;
    int second = 1;
    for (int index = 0; index < terms; index++) {
        printf("%d%s", first, index + 1 == terms ? "\n" : " ");
        int next = first + second;
        first = second;
        second = next;
    }
    if (terms == 0) printf("(empty sequence)\n");
}

static void simple_calculator(void) {
    double first;
    double second;
    int status = read_double("First number: ", &first);
    if (status <= 0) return;
    status = read_double("Second number: ", &second);
    if (status <= 0) return;

    char line[32];
    printf("Operator (+, -, *, /): ");
    if (!read_line(line, sizeof line)) return;
    switch (line[0]) {
        case '+': printf("Result: %.2f\n", first + second); break;
        case '-': printf("Result: %.2f\n", first - second); break;
        case '*': printf("Result: %.2f\n", first * second); break;
        case '/':
            if (second == 0.0) printf("Cannot divide by zero.\n");
            else printf("Result: %.2f\n", first / second);
            break;
        default: printf("Choose +, -, *, or /.\n");
    }
}

int main(void) {
    for (;;) {
        int choice;
        printf("\nC Programming — Week 1\n");
        printf("1) Hello World\n");
        printf("2) Sum of two numbers\n");
        printf("3) Even or odd\n");
        printf("4) Fibonacci sequence\n");
        printf("5) Simple calculator\n");
        printf("6) Exit\n");

        int status = read_int("Choose an option: ", &choice);
        if (status == 0) return 0;
        if (status < 0) continue;
        switch (choice) {
            case 1: printf("Hello, World!\n"); break;
            case 2: sum_two_numbers(); break;
            case 3: check_even_or_odd(); break;
            case 4: print_fibonacci(); break;
            case 5: simple_calculator(); break;
            case 6: return 0;
            default: printf("Choose a number from 1 to 6.\n");
        }
    }
}
