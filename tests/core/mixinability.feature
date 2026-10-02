Feature: Kind Mixinability

  As a developer extending the Kind class
  I want to dynamically add and manage functionality
  So that I can create flexible and modular symbolic systems

  Scenario: Freezing and unfreezing Kind class state
    Given the Kind class is initially not frozen
    When the Kind class is frozen
    Then the Kind class should be reported as frozen
    And subsequent attempts to freeze the Kind class should not change its frozen state

  Scenario: Registering and applying a basic mixin
    Given a simple mixin function defined
    When the mixin function is registered to the Kind class with a new method name
    Then the registration should be successful
    And instances of Kind should have the new method
    And calling the new method on a Kind instance should return the expected result

  Scenario: Overwriting an existing mixin
    Given an existing mixin registered to the Kind class
    And a new mixin function intended to overwrite the existing method
    When the new mixin function is registered with the same method name
    Then the registration should be successful
    And calling the method on a Kind instance should now return the result from the new mixin
