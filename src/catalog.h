#ifndef CATALOG_H
#define CATALOG_H

#define MAX_BOOKS 100

typedef struct {
    int id;
    char title[64];
    char author[48];
    int year;
    int copies;
} Book;

int catalog_add(Book *list, int count, Book b);
int catalog_total_copies(const Book *list, int count);
const Book *catalog_find_by_id(const Book *list, int count, int id);

#endif
