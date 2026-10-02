Feature: Kind Indexing Functionality

  As a developer managing indexed Kind data
  I want to efficiently insert Kinds and traverse the index
  So that I can perform quick lookups and ordered operations

  Scenario: KindIndex insertion
    Given an empty KindIndex
    When a Kind is inserted with a given weight
    Then the Kind should be present in the index
    And the index structure should remain valid

  Scenario: KindIndex traversal
    Given a KindIndex with a simple tree structure
    When the index is traversed in-order
    Then the Kinds should be yielded in the correct sorted order
