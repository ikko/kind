Feature: Kind Time Dimension Functionality

  As a developer working with time-based data in Kind
  I want to parse, access, and manipulate time_dim information
  So that I can effectively manage temporal aspects of my symbolic systems

  Scenario: Parsing timestamps from Kind names
    Given a Kind with a valid ISO format time_dim name (e.g., "2023-01-15T10:30:00")
    When the timestamp is parsed
    Then it should correctly convert to a time_dim object with the specified date and time
    Given a Kind with a valid ISO format date-only name (e.g., "2023-03-20")
    When the timestamp is parsed
    Then it should correctly convert to a time_dim object with the specified date and time defaulting to midnight
    Given a Kind with an invalid format name (e.g., "invalid-date")
    When the timestamp is parsed
    Then it should default to today's date with time set to midnight

  Scenario: Accessing time_dim properties of a Kind
    Given a Kind named "2023-04-22T14:45:30"
    When its time_dim properties are accessed
    Then its `as_date` property should return the correct date
    And its `as_time` property should return the correct time
    And its `as_datetime` property should return the correct full time_dim
    And its `day` property should return the correct day
    And its `hour` property should return the correct hour
    And its `minute` property should return the correct minute
    And its `second` property should return the correct second
    Given a Kind named "2023-05-01" (date-only)
    When its time_dim properties are accessed
    Then its `as_date` property should return the correct date
    And its `as_time` property should return midnight
    And its `as_datetime` property should return the correct time_dim with midnight time

  Scenario: Retrieving chronological head and tail views of Kinds
    Given multiple Kinds with distinct chronological timestamps (early, middle, late)
    When the `head` property is accessed on any of these Kinds
    Then a `KindHeadTailView` instance should be returned
    And iterating over this view should yield Kinds in chronological order (early to late)
    When the `tail` property is accessed on any of these Kinds
    Then a `KindHeadTailView` instance should be returned
    And iterating over this view should yield Kinds in reverse chronological order (late to early)

  Scenario: Calculating time periods between Kinds
    Given two Kinds representing a start and an end time (e.g., "2023-01-01T10:00:00" and "2023-01-01T11:30:00")
    When the `period`, `as_period`, `duration`, `as_duration`, `delta`, or `as_delta` properties are accessed
    Then they should all return the correct `Duration` representing the duration between the start and end Kinds
    Given a single Kind
    When its period properties are accessed
    Then they should return a `Duration` of zero
