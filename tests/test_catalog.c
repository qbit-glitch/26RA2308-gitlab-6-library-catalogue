/* C tests for the catalogue core (run with: make test-c). */
#include <stdio.h>
#include <stddef.h>
#include "catalog.h"

static int failures = 0;

#define CHECK(name, cond)                      \
    do {                                       \
        if (cond) {                            \
            printf("PASS %s\n", name);         \
        } else {                               \
            printf("FAIL %s\n", name);         \
            failures++;                        \
        }                                      \
    } while (0)

int main(void)
{
    Book list[MAX_BOOKS];
    int count = 0;
    Book a = {101, "The C Programming Language", "Kernighan and Ritchie", 1978, 4};
    Book b = {102, "Introduction to Algorithms", "Cormen", 2009, 6};

    count = catalog_add(list, count, a);
    count = catalog_add(list, count, b);

    CHECK("add increases the count", count == 2);
    CHECK("total copies is the sum of all copies", catalog_total_copies(list, count) == 10);
    CHECK("find an existing id", catalog_find_by_id(list, count, 102) != NULL);
    CHECK("find a missing id returns NULL", catalog_find_by_id(list, count, 999) == NULL);
    CHECK("add rejects a full catalogue", catalog_add(list, MAX_BOOKS, a) == -1);

    return failures == 0 ? 0 : 1;
}
