Feature: OrderedKindSet Functionality

  As a developer using Kind collections
  I want to manage unique Kind objects while preserving insertion order
  So that I can maintain predictable data structures

  Scenario: OrderedKindSet creation and adding Kinds
    Given an empty OrderedKindSet is created
    Then its size should be 0
    When a single Kind is added to the set
    Then its size should be 1
    And the Kind should be present in the set
    When multiple Kinds are added to the set
    Then its size should reflect the number of unique Kinds added
    And all added Kinds should be present in the set
    When an existing Kind is added again to the set
    Then the size of the set should not change
    Given an OrderedKindSet is created with initial Kinds
    Then its size should reflect the number of initial Kinds
    And all initial Kinds should be present in the set

  Scenario: OrderedKindSet iteration, length, and containment
    Given an OrderedKindSet containing Kinds "alpha", "beta", and "gamma" in that order
    When the length of the set is checked
    Then it should be 3
    When the set is iterated over
    Then the Kinds should be yielded in their insertion order
    When checking for containment of an existing Kind
    Then it should be found in the set
    When checking for containment of a Kind with the same name (due to interning)
    Then it should also be found in the set
    When checking for containment of a non-existent Kind
    Then it should not be found in the set
    When a new Kind "delta" is added to the set
    Then iterating over the set should include "delta" at the end, maintaining insertion order
