Feature: Kind Path Functionality

  As a developer navigating Kind graphs
  I want to find paths between Kinds and match Kinds based on predicates
  So that I can analyze relationships and extract relevant subgraphs

  Scenario: Finding a path between two Kinds
    Given a Kind graph with a defined path between a source and a target Kind
    When `path_to` is called from the source Kind to the target Kind
    Then a list of Kinds representing the path should be returned

  Scenario: Matching Kinds based on a predicate
    Given a Kind graph with various Kinds
    When `match` is called with a predicate that identifies specific Kinds
    And a traversal strategy (e.g., DFS or BFS)
    Then an iterator yielding only the Kinds that match the predicate should be returned in the specified traversal order
