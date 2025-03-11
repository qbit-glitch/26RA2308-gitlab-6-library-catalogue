#include <algorithm>
#include <cctype>

#include "search.hpp"

static std::string to_lower(std::string text)
{
    std::transform(text.begin(), text.end(), text.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return text;
}

std::vector<std::string> search_titles(const std::vector<std::string> &titles,
                                       const std::string &query)
{
    const std::string needle = to_lower(query);
    std::vector<std::string> matches;
    for (const std::string &title : titles) {
        if (to_lower(title).find(needle) != std::string::npos) {
            matches.push_back(title);
        }
    }
    return matches;
}
