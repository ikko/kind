Feature: Kind Visual Functionality

  As a developer visualizing Kind graphs
  I want to generate Mermaid diagrams from Kind structures
  So that I can easily represent and understand complex relationships

  Scenario: Generating a Mermaid diagram for a simple Kind graph
    Given a simple Kind graph structure
    When `to_mmd` is called on the root Kind
    Then a valid Mermaid diagram string representing the graph should be returned
