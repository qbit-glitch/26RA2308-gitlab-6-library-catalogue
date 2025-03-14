# Library Catalogue - build and test targets
CC       := gcc
CXX      := g++
CFLAGS   := -Wall -Wextra -std=c99 -Isrc
CXXFLAGS := -Wall -Wextra -std=c++11 -Isrc
BUILD    := build

.PHONY: test test-py test-c test-cpp grade clean

test: test-py test-c test-cpp
	@echo "ALL TESTS PASSED"

test-py:
	python3 -m unittest discover -s tests -v

test-c:
	@mkdir -p $(BUILD)
	$(CC) $(CFLAGS) -o $(BUILD)/test_catalog tests/test_catalog.c src/catalog.c
	./$(BUILD)/test_catalog

test-cpp:
	@mkdir -p $(BUILD)
	$(CXX) $(CXXFLAGS) -o $(BUILD)/test_search tests/test_search.cpp src/search.cpp
	./$(BUILD)/test_search

grade:
	python3 tests/grade.py

clean:
	rm -rf $(BUILD)
