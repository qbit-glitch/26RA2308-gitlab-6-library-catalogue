#ifndef SEARCH_HPP
#define SEARCH_HPP

#include <string>
#include <vector>

// Return every title that contains the query text.
std::vector<std::string> search_titles(const std::vector<std::string> &titles,
                                       const std::string &query);

#endif
