#include "search.hpp"

std::vector<std::string> search_titles(const std::vector<std::string> &titles,
                                       const std::string &query)
{
    std::vector<std::string> matches;
    for (const std::string &title : titles) {
        if (title.find(query) != std::string::npos) {
            matches.push_back(title);
        }
    }
    return matches;
}
