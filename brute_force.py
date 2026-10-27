"""
Brute Force Multi-Pattern String Search
========================================
Baseline algorithm for benchmarking against Aho-Corasick.

For each pattern, scans the entire text character by character.
Time complexity: O(k * n * m) where:
  k = number of patterns
  n = length of text
  m = average pattern length

This is what Aho-Corasick (1975) was designed to replace.
"""


def brute_force_search(text: str, patterns: list[str]) -> tuple[list[tuple], int]:
    """
    Search for all patterns in text using naive character-by-character comparison.

    Returns:
        matches  : list of (pattern, position) tuples for every match found
        comparisons: total character comparisons made (complexity metric)
    """
    matches = []
    comparisons = 0

    for pattern in patterns:
        pat_len = len(pattern)
        text_len = len(text)

        # Slide pattern over every possible starting position
        for i in range(text_len - pat_len + 1):
            match = True

            for j in range(pat_len):
                comparisons += 1
                if text[i + j] != pattern[j]:
                    match = False
                    break   # mismatch — stop checking this position

            if match:
                matches.append((pattern, i))

    return matches, comparisons
