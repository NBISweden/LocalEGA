Feature: Authentication
  As a user I want to be able to authenticate against LocalEGA inbox

  Scenario: Authenticate against LocalEGA inbox
    Given I have username and password
    When I try to connect to the LocalEGA inbox via SFTP using these credentials
    Then the operation is successful