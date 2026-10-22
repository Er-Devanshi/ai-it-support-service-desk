# Enterprise Account Security and Access Policy

## Password Complexity and Expiry Rules
- Minimum length: 12 characters.
- Must contain at least: one uppercase letter (A-Z), one lowercase letter (a-z), one numeric digit (0-9), and one approved symbol (`!@#$%^&*`).
- History: Users cannot reuse any of their previous 5 passwords.
- Expiration: Passwords expire every 90 days. Automated reminders are dispatched via email 14, 7, and 3 days prior to expiration.

## Account Lockout Standard Operating Procedure
- Accounts lock automatically after 5 consecutive incorrect password attempts within a 15-minute window.
- Automatic lockout duration: 15 minutes.
- Immediate unlock: Employees can utilize the self-service portal or request an authorized ServiceDesk agent to trigger the `unlock_account` administrative workflow.
- High-risk flag: If lockouts occur repeatedly from foreign IP addresses or outside regular business hours, SecOps is automatically alerted.

## Privileged Resource Access Requests
- Access to production databases, financial ledgers, and Restricted-DB repositories requires explicit human approval.
- Workflows for access requests:
  1. The user or bot creates a pending authorization request (`grant_resource_access`).
  2. Support Lead or System Administrator reviews business justification.
  3. Once approved, temporary access tokens are provisioned with an automatic 8-hour time-to-live (TTL).
