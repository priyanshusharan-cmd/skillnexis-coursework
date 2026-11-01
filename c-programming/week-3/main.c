#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void reverse_string(char *s) {
    char *left = s;
    char *right = s + strlen(s);
    if (right == s) {
        return;
    }
    --right;
    while (left < right) {
        char tmp = *left;
        *left++ = *right;
        *right-- = tmp;
    }
}

static void count_vowels_consonants(const char *s, int *vowels, int *consonants) {
    *vowels = 0;
    *consonants = 0;
    for (; *s != '\0'; ++s) {
        if (isalpha((unsigned char)*s)) {
            if (strchr("aeiouAEIOU", *s) != NULL) {
                ++*vowels;
            } else {
                ++*consonants;
            }
        }
    }
}

static void swap(int *a, int *b) {
    int tmp = *a;
    *a = *b;
    *b = tmp;
}

static int *allocate_array(size_t n) {
    int *arr = malloc(n * sizeof *arr);
    if (arr == NULL) {
        return NULL;
    }
    for (size_t i = 0; i < n; ++i) {
        *(arr + i) = (int)((i + 1) * (i + 1));
    }
    return arr;
}

static int count_words(const char *s) {
    int words = 0;
    int in_word = 0;
    for (; *s != '\0'; ++s) {
        if (isspace((unsigned char)*s)) {
            in_word = 0;
        } else if (!in_word) {
            in_word = 1;
            ++words;
        }
    }
    return words;
}

int main(void) {
    char text[] = "Pointers and strings in C";
    printf("1. Original: \"%s\"\n", text);
    reverse_string(text);
    printf("   Reversed: \"%s\"\n", text);

    int v, c;
    count_vowels_consonants("Hello, World!", &v, &c);
    printf("2. \"Hello, World!\" -> vowels=%d consonants=%d\n", v, c);

    int x = 10, y = 25;
    printf("3. Before swap: x=%d y=%d\n", x, y);
    swap(&x, &y);
    printf("   After swap:  x=%d y=%d\n", x, y);

    size_t n = 5;
    int *arr = allocate_array(n);
    if (arr == NULL) {
        fprintf(stderr, "malloc failed\n");
        return EXIT_FAILURE;
    }
    printf("4. malloc'd array of %zu squares:", n);
    for (size_t i = 0; i < n; ++i) {
        printf(" %d", arr[i]);
    }
    printf("\n");
    free(arr);

    const char *sentence = "  the quick  brown fox\tjumps over the lazy dog  ";
    printf("Mini project: word count of \"%s\" = %d\n", sentence, count_words(sentence));
    printf("Word count of empty string = %d\n", count_words(""));
    return EXIT_SUCCESS;
}
