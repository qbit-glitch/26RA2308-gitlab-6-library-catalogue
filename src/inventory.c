#include <stddef.h>
#include "inventory.h"

int catalog_add(Book *list, int count, Book b)
{
    if (count >= MAX_BOOKS) {
        return -1;
    }
    list[count] = b;
    return count + 1;
}

int catalog_total_copies(const Book *list, int count)
{
    int total = 0;
    for (int i = 0; i < count; i++) {
        total += list[i].copies;
    }
    return total;
}

const Book *catalog_find_by_id(const Book *list, int count, int id)
{
    for (int i = 0; i < count; i++) {
        if (list[i].id == id) {
            return &list[i];
        }
    }
    return NULL;
}
