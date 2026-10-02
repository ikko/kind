Feature: Kind Creation and Core Properties

  As a developer using the Kind library
  I want to reliably create and manage Kind instances
  So that I can build consistent symbolic representations

  Scenario: Kind creation and interning
    Given a kind name "test_kind"
    When a Kind is created with "test_kind"
    Then an instance of Kind is returned
    And the kind's name is "test_kind"
    When another Kind is created with the same name "test_kind"
    Then the same Kind instance is returned (interning)
    When a Kind is created with a case-sensitive different name "Test_Kind"
    Then a new Kind instance is returned
    And the new kind's name is "Test_Kind"
    When Kinds are created with names like "123", "kind-with_dashes", and "another kind"
    Then they should retain their exact names

  Scenario: Kind equality and hashing
    Given two Kinds with the same name "apple"
    And one Kind with a different name "banana"
    When the two Kinds with the same name are compared for equality
    Then they should be equal
    When a Kind with a different name is compared for equality
    Then they should not be equal
    When the hash of the two Kinds with the same name is calculated
    Then their hashes should be equal
    When the hash of a Kind with a different name is calculated
    Then its hash should not be equal to the others
    When a Kind is compared with non-Kind types (e.g., string, integer)
    Then they should not be equal

  Scenario: Kind string representation
    Given a Kind named "test_repr"
    When the Kind is converted to a string
    Then the string representation should be "test_repr"
    When the Kind's repr is called
    Then the repr representation should be "Kind('test_repr')"

  Scenario: Basic graph operations (append, add, children, parents)
    Given a parent Kind and two child Kinds (child1, child2)
    And a grandchild Kind
    When child1 is appended to the parent
    Then child1 is in the parent's children
    And parent is in child1's parents
    And the parent has one child
    When child1 is appended again to the parent
    Then the parent still has one child (no duplicates)
    When child2 is added to the parent
    Then child2 is in the parent's children
    And parent is in child2's parents
    And the parent has two children
    When child2 is added again to the parent
    Then the parent still has two children (no duplicates)
    When grandchild is appended to the parent, and then child1 is appended (chaining)
    Then grandchild is in the parent's children
    And parent is in grandchild's parents
    And the parent has three children (child1, child2, grandchild)
    And the children and parents properties reflect the correct relationships
    When another parent and child are created, and the child is appended to the another parent
    And the another parent is appended to child1
    Then the relationships are correctly established in the graph

  Scenario: KindNamespace functionality
    Given a KindNamespace instance
    When a Kind is accessed via attribute (e.g., `s.my_attribute_kind`)
    Then an instance of Kind is returned
    And its name matches the attribute name
    When a Kind is accessed via item (e.g., `s["my_item_kind"]`)
    Then an instance of Kind is returned
    And its name matches the item name
    When Kinds are accessed via both attribute and item with the same name
    Then the same Kind instance is returned (interning through namespace)
    When an attempt is made to set an attribute or item on the KindNamespace
    Then a TypeError should be raised, indicating it is read-only
