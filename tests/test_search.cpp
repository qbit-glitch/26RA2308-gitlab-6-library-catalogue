// C++ tests for the title search (run with: make test-cpp).
#include <iostream>
#include <string>
#include <vector>

#include "search.hpp"

static int failures = 0;

static void check(const std::string &name, bool condition)
{
    std::cout << (condition ? "PASS " : "FAIL ") << name << "\n";
    if (!condition) {
        failures++;
    }
}

int main()
{
    const std::vector<std::string> titles = {
        "Clean Code", "Python Crash Course", "Effective C++", "Design Patterns"};

    check("finds an exact word", search_titles(titles, "Clean").size() == 1);
    check("search ignores letter case", search_titles(titles, "python").size() == 1);
    check("finds a substring", search_titles(titles, "ern").size() == 1);
    check("no match gives an empty list", search_titles(titles, "zzz").empty());

    return failures == 0 ? 0 : 1;
}
