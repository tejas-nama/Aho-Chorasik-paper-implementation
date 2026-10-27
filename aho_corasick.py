"""
Aho-Corasick Multi-Pattern String Search
==========================================
Implementation of the algorithm described in:

  Aho, A. V., and Corasick, M. J. (1975).
  Efficient String Matching: An Aid to Bibliographic Search.
  Communications of the ACM, 18(6), 333-340.

The algorithm has two phases:
  Phase 1 (Offline): Build a finite state machine from the pattern set.
                     - goto()   function: Trie construction
                     - failure() function: Suffix/failure links via BFS
                     - output() function: Merge outputs through failure links

  Phase 2 (Online):  Scan text in a single forward pass using the machine.
                     O(n + m + z) where n=text length, m=total pattern length,
                     z=number of matches.

This module tracks character comparisons to allow fair benchmarking
against the brute force baseline.
"""

from collections import deque


class AhoCorasick:
    """
    A finite state pattern-matching machine (Aho-Corasick automaton).

    Attributes:
        goto_fn   : dict[state -> dict[char -> state]]  (the trie transitions)
        failure_fn: dict[state -> state]                (failure/suffix links)
        output_fn : dict[state -> set[str]]             (patterns completing at state)
        num_states: int                                  (total states built)
    """

    def __init__(self):
        # State 0 is the root (start state)
        self.goto_fn    = {0: {}}      # goto_fn[state][char] = next_state
        self.failure_fn = {}           # failure_fn[state] = fallback_state
        self.output_fn  = {0: set()}   # output_fn[state] = set of matching patterns
        self.num_states = 0            # next available state ID

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1A: GOTO FUNCTION — Build the Trie
    # (Section 3, Algorithm 2 of Aho & Corasick 1975)
    # ─────────────────────────────────────────────────────────────────────────
    def _build_goto(self, patterns: list[str]):
        """
        Insert all patterns into the trie.
        Each character in a pattern creates (or reuses) a state.
        The state reached at the end of a pattern is marked in output_fn.
        """
        for pattern in patterns:
            current_state = 0

            for char in pattern:
                # If this character already has a transition, follow it
                if char in self.goto_fn[current_state]:
                    current_state = self.goto_fn[current_state][char]
                else:
                    # Create a new state for this character
                    self.num_states += 1
                    new_state = self.num_states
                    self.goto_fn[current_state][char] = new_state
                    self.goto_fn[new_state] = {}       # initialise empty transitions
                    self.output_fn[new_state] = set()  # no outputs yet
                    current_state = new_state

            # Mark this final state as producing the full pattern
            self.output_fn[current_state].add(pattern)

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 1B: FAILURE FUNCTION — Build Suffix Links via BFS
    # (Section 3, Algorithm 3 of Aho & Corasick 1975)
    # ─────────────────────────────────────────────────────────────────────────
    def _build_failure(self):
        """
        Compute failure links for all states using BFS.

        The failure link for state s points to the state representing the
        longest proper suffix of the string represented by s that is also
        a prefix of some pattern in the trie.

        This is what allows the automaton to avoid backtracking in the text.
        """
        queue = deque()

        # Initialise depth-1 states: their failure link always points to root (0)
        for char, next_state in self.goto_fn[0].items():
            self.failure_fn[next_state] = 0
            queue.append(next_state)

        # BFS over remaining states
        while queue:
            current_state = queue.popleft()

            for char, next_state in self.goto_fn[current_state].items():
                queue.append(next_state)

                # Follow failure links up until we find a match or reach root
                fallback = self.failure_fn[current_state]
                while fallback != 0 and char not in self.goto_fn[fallback]:
                    fallback = self.failure_fn[fallback]

                # Set failure link for next_state
                if char in self.goto_fn[fallback] and self.goto_fn[fallback][char] != next_state:
                    self.failure_fn[next_state] = self.goto_fn[fallback][char]
                else:
                    self.failure_fn[next_state] = 0

                # MERGE outputs: if the failure state has outputs, inherit them
                # This handles the case where one pattern is a suffix of another
                # (e.g. "he" is a suffix of "she" in the classic example)
                self.output_fn[next_state] |= self.output_fn[self.failure_fn[next_state]]

    # ─────────────────────────────────────────────────────────────────────────
    # Build the complete machine
    # ─────────────────────────────────────────────────────────────────────────
    def build(self, patterns: list[str]):
        """Build the full pattern-matching machine from a list of patterns."""
        self._build_goto(patterns)
        self._build_failure()

    # ─────────────────────────────────────────────────────────────────────────
    # PHASE 2: SEARCH — Single-pass text scan
    # (Section 3, Algorithm 1 of Aho & Corasick 1975)
    # ─────────────────────────────────────────────────────────────────────────
    def search(self, text: str) -> tuple[list[tuple], int]:
        """
        Scan text in a single forward pass using the pre-built automaton.

        Returns:
            matches    : list of (pattern, end_position) tuples
            comparisons: number of state-transition lookups (complexity metric)
        """
        matches     = []
        comparisons = 0
        state       = 0   # start at root

        for i, char in enumerate(text):
            comparisons += 1  # one lookup per character — O(n) regardless of k

            # Follow failure links until we find a valid transition or hit root
            while state != 0 and char not in self.goto_fn[state]:
                state = self.failure_fn[state]

            # Take the transition if it exists
            if char in self.goto_fn[state]:
                state = self.goto_fn[state][char]
            # else: state stays at 0 (root)

            # Check if this state produces any output
            if self.output_fn[state]:
                for pattern in self.output_fn[state]:
                    start_pos = i - len(pattern) + 1
                    matches.append((pattern, start_pos))

        return matches, comparisons


# ─────────────────────────────────────────────────────────────────────────────
# Convenience wrapper: build + search in one call
# ─────────────────────────────────────────────────────────────────────────────
def aho_corasick_search(text: str, patterns: list[str]) -> tuple[list[tuple], int]:
    """
    Build the Aho-Corasick automaton and search text.
    Returns (matches, comparisons) — same interface as brute_force_search().
    """
    ac = AhoCorasick()
    ac.build(patterns)
    return ac.search(text)
