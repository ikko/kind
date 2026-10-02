Feature: Kind Happy Path Functionality

  As a developer using the Kind library
  I want to ensure core Kind functionalities work as expected
  So that I can build reliable symbolic systems

  Scenario: Kind creation and interning
    Given a kind name "test_kind_1"
    When a Kind is created with "test_kind_1"
    Then an instance of Kind is returned
    And the kind's name is "test_kind_1"
    When another Kind is created with the same name "test_kind_1"
    Then the same Kind instance is returned (interning)
    When a Kind is created with a different name "test_kind_2"
    Then a new Kind instance is returned
    And the new kind's name is "test_kind_2"

  Scenario: Kind equality and hashing
    Given two Kinds with the same name "equal_kind"
    And one Kind with a different name "another_kind"
    When the two Kinds with the same name are compared for equality
    Then they should be equal
    When a Kind with a different name is compared for equality
    Then they should not be equal
    When the hash of the two Kinds with the same name is calculated
    Then their hashes should be equal
    When the hash of a Kind with a different name is calculated
    Then its hash should not be equal to the others

  Scenario: Kind string representation
    Given a Kind named "repr_kind"
    When the Kind is converted to a string
    Then the string representation should be "repr_kind"
    When the Kind's repr is called
    Then the repr representation should be ":repr_kind"

  Scenario: Basic graph operations (append, add)
    Given a parent Kind and two child Kinds
    When a child Kind is appended to the parent
    Then the child is in the parent's children list
    And the parent is in the child's parents list
    When the same child Kind is added again to the parent
    Then the number of children remains the same (no duplicates)
    When a different child Kind is added to the parent
    Then the new child is in the parent's children list
    And the parent is in the new child's parents list
    And the parent has two children

  Scenario: KindNamespace functionality
    Given a KindNamespace instance
    When a Kind is accessed via attribute (e.g., "my_attribute_kind")
    Then an instance of Kind is returned
    And the kind's name matches the attribute name
    When a Kind is accessed via item (e.g., "my_item_kind")
    Then an instance of Kind is returned
    And the kind's name matches the item name
    When Kinds are accessed via both attribute and item with the same name
    Then the same Kind instance is returned (interning through namespace)
