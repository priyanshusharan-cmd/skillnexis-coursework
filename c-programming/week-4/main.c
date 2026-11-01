#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NAME_LEN 50

struct Student {
    char name[NAME_LEN];
    int age;
    float marks;
};

struct Date {
    int day, month, year;
};

struct Employee {
    int id;
    char name[NAME_LEN];
    char role[NAME_LEN];
    float salary;
    struct Date joined;
};

static const char *STUDENT_FILE = "students.dat";
static const char *LOG_FILE = "notes.txt";
static const char *EMP_FILE = "employees.dat";

static int write_students(const struct Student *s, size_t n) {
    FILE *fp = fopen(STUDENT_FILE, "wb");
    if (fp == NULL) {
        perror(STUDENT_FILE);
        return -1;
    }
    size_t written = fwrite(s, sizeof *s, n, fp);
    fclose(fp);
    return written == n ? 0 : -1;
}

static int read_students(void) {
    FILE *fp = fopen(STUDENT_FILE, "rb");
    if (fp == NULL) {
        perror(STUDENT_FILE);
        return -1;
    }
    struct Student s;
    printf("%-15s %-5s %s\n", "Name", "Age", "Marks");
    while (fread(&s, sizeof s, 1, fp) == 1) {
        printf("%-15s %-5d %.1f\n", s.name, s.age, s.marks);
    }
    fclose(fp);
    return 0;
}

static int count_lines(const char *path) {
    FILE *fp = fopen(path, "r");
    if (fp == NULL) {
        perror(path);
        return -1;
    }
    int lines = 0, ch, last = '\n';
    while ((ch = fgetc(fp)) != EOF) {
        if (ch == '\n') {
            ++lines;
        }
        last = ch;
    }
    if (last != '\n') {
        ++lines;
    }
    fclose(fp);
    return lines;
}

static int append_line(const char *path, const char *text) {
    FILE *fp = fopen(path, "a");
    if (fp == NULL) {
        perror(path);
        return -1;
    }
    fprintf(fp, "%s\n", text);
    fclose(fp);
    return 0;
}

static int run_demo(void) {
    struct Student students[] = {
        {"Asha", 20, 88.5f}, {"Ravi", 21, 74.0f}, {"Meera", 19, 91.25f},
    };
    size_t n = sizeof students / sizeof students[0];

    printf("1-2. Writing %zu students to %s and reading them back\n", n, STUDENT_FILE);
    if (write_students(students, n) != 0 || read_students() != 0) {
        return EXIT_FAILURE;
    }

    remove(LOG_FILE);
    append_line(LOG_FILE, "first line");
    append_line(LOG_FILE, "second line");
    printf("3. Lines in %s: %d\n", LOG_FILE, count_lines(LOG_FILE));
    append_line(LOG_FILE, "appended line");
    printf("4. After append, lines in %s: %d\n", LOG_FILE, count_lines(LOG_FILE));
    return EXIT_SUCCESS;
}

static int emp_next_id(void) {
    FILE *fp = fopen(EMP_FILE, "rb");
    int max = 0;
    struct Employee e;
    if (fp != NULL) {
        while (fread(&e, sizeof e, 1, fp) == 1) {
            if (e.id > max) {
                max = e.id;
            }
        }
        fclose(fp);
    }
    return max + 1;
}

static void print_emp(const struct Employee *e) {
    printf("%-4d %-15s %-15s %10.2f  %02d-%02d-%04d\n", e->id, e->name, e->role, e->salary,
           e->joined.day, e->joined.month, e->joined.year);
}

static int emp_add(char **argv) {
    struct Employee e = {0};
    e.id = emp_next_id();
    snprintf(e.name, sizeof e.name, "%s", argv[0]);
    snprintf(e.role, sizeof e.role, "%s", argv[1]);
    e.salary = (float)atof(argv[2]);
    if (sscanf(argv[3], "%d-%d-%d", &e.joined.day, &e.joined.month, &e.joined.year) != 3) {
        fprintf(stderr, "date must be DD-MM-YYYY\n");
        return EXIT_FAILURE;
    }
    FILE *fp = fopen(EMP_FILE, "ab");
    if (fp == NULL) {
        perror(EMP_FILE);
        return EXIT_FAILURE;
    }
    fwrite(&e, sizeof e, 1, fp);
    fclose(fp);
    printf("Added employee #%d\n", e.id);
    return EXIT_SUCCESS;
}

static int emp_list(const char *needle) {
    FILE *fp = fopen(EMP_FILE, "rb");
    if (fp == NULL) {
        printf("No employees stored yet.\n");
        return EXIT_SUCCESS;
    }
    struct Employee e;
    int shown = 0;
    printf("%-4s %-15s %-15s %10s  %s\n", "ID", "Name", "Role", "Salary", "Joined");
    while (fread(&e, sizeof e, 1, fp) == 1) {
        if (needle == NULL || strstr(e.name, needle) != NULL) {
            print_emp(&e);
            ++shown;
        }
    }
    fclose(fp);
    printf("(%d shown)\n", shown);
    return EXIT_SUCCESS;
}

static int emp_delete(int id) {
    FILE *in = fopen(EMP_FILE, "rb");
    if (in == NULL) {
        fprintf(stderr, "No employees stored yet.\n");
        return EXIT_FAILURE;
    }
    FILE *out = fopen("employees.tmp", "wb");
    if (out == NULL) {
        perror("employees.tmp");
        fclose(in);
        return EXIT_FAILURE;
    }
    struct Employee e;
    int removed = 0;
    while (fread(&e, sizeof e, 1, in) == 1) {
        if (e.id == id) {
            removed = 1;
        } else {
            fwrite(&e, sizeof e, 1, out);
        }
    }
    fclose(in);
    fclose(out);
    if (removed) {
        remove(EMP_FILE);
        rename("employees.tmp", EMP_FILE);
        printf("Deleted employee #%d\n", id);
        return EXIT_SUCCESS;
    }
    remove("employees.tmp");
    fprintf(stderr, "Employee #%d not found\n", id);
    return EXIT_FAILURE;
}

static void usage(const char *prog) {
    fprintf(stderr,
            "Usage:\n"
            "  %s demo                              run assignments 1-4\n"
            "  %s add <name> <role> <salary> <DD-MM-YYYY>\n"
            "  %s list [name-fragment]\n"
            "  %s delete <id>\n",
            prog, prog, prog, prog);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        usage(argv[0]);
        return EXIT_FAILURE;
    }
    if (strcmp(argv[1], "demo") == 0) {
        return run_demo();
    }
    if (strcmp(argv[1], "add") == 0 && argc == 6) {
        return emp_add(argv + 2);
    }
    if (strcmp(argv[1], "list") == 0 && argc <= 3) {
        return emp_list(argc == 3 ? argv[2] : NULL);
    }
    if (strcmp(argv[1], "delete") == 0 && argc == 3) {
        return emp_delete(atoi(argv[2]));
    }
    usage(argv[0]);
    return EXIT_FAILURE;
}
