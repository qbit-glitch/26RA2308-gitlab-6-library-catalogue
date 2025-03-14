# Library Catalogue

A small command-line toolkit for keeping track of the books in a library.
It is written in three languages on purpose:

* `src/`   - a C core (book records) and a C++ search helper
* `tools/` - Python scripts that read the data and print reports
* `data/`  - plain-text sample data

## Data format

Books are stored one per line in `data/books.txt`, with fields separated
by a vertical bar:

    id|title|author|year|copies

Lines that start with `#` are comments and are ignored.

## Running the report

From the top-level directory run:

    python3 -m tools.report data/books.txt

The report prints the number of titles, the total number of copies and the
average number of copies per title.

## Project layout

    data/    sample data files
    src/     C and C++ sources
    tools/   Python scripts

## Contributing

Keep commits small and write the subject line in the form
`type(scope): summary`, for example `fix(search): ignore letter case`.
Run the tests before you commit.

## Licence

Released for teaching purposes. Do whatever you like with it.

## Lab assignment

This repository is also the starter for a Git lab. Open `ASSIGNMENT.md`
for the instructions.
