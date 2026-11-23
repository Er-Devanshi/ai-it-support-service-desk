# Enterprise Account Security and Access Policy

## Password Complexity and Expiry Rules
- Minimum length: 12 characters.
- Must contain at least: one uppercase letter (A-Z), one lowercase letter (a-z), one numeric digit (0-9), and one approved symbol (`!@#$%^&*`).
- History: Users cannot reuse any of their previous 5 passwords.
- Expiration: Passwords expire every 90 days. Automated reminders are dispatched via email 14, 7, and 3 days prior to expiration.

## Password Reset Email Not Received

**Symptoms:**
- Password reset email does not arrive in inbox
- Self-service password reset email shows "Sent" but email never appears
- Email was sent but not received or is delayed

**Step-by-step resolution:**

1. **Check your email account is correct.** Verify the email address on file matches where you expect to receive the reset link. Check your user profile in the IT Self-Service Portal.
2. **Check the spam/junk folder.** The reset email may have been filtered. Search your Spam folder for emails from [contact IT Helpdesk] with subject containing "password" or "reset".
3. **Wait 5-10 minutes.** Email delivery can be delayed. If using a mobile device, manually refresh or check again after a short wait.
4. **Resend the reset request.** Go to the IT Self-Service Portal → Account Management → Reset Password and request a new email. Wait 2-3 minutes before escalating.
5. **Update your email address if it has changed.** If you no longer use the registered email, contact IT Support immediately with proof of identity to update your account contact details.
6. **Clear your email cache.** Close and reopen your email client to ensure new messages are synced.

**Escalation:** If the reset email still does not arrive after all steps above, or if your email address cannot be updated, contact IT Support with your employee ID. Provide the date and time you requested the reset and any error messages you received. IT can verify the email was sent and manually reset your password.

## Account Compromised or Unauthorized Access Suspected

**Symptoms:**
- You see login activity you did not perform
- Your password stopped working without being changed by you
- Account is locked but you have not attempted login
- Unexpected security alerts or access from unknown location

**Step-by-step response:**

1. **Change your password immediately.** If you can still log in, go to the IT Self-Service Portal → Change Password and create a new strong password (follow "Password Complexity and Expiry Rules" above). Do not reuse previous passwords.
2. **Review your recent login history.** In the IT Self-Service Portal → Account Security → View Login History, check for logins you do not recognize. Note the date, time, and location.
3. **Revoke active sessions.** In the IT Self-Service Portal → Account Security → Active Sessions, end all sessions except your current one.
4. **Enable or verify multi-factor authentication (MFA).** Go to the IT Self-Service Portal → Security → MFA Setup and ensure MFA is active on your account. If you see MFA methods you did not set up, remove them immediately.
5. **Check for forwarding rules.** In Outlook or your email client, go to Settings → Forwarding or Rules to ensure no unauthorized email forwarding is set up. Delete any unexpected rules.
6. **Report to IT Security immediately.** Contact IT Security team directly with details of the suspicious activity, including when you first noticed it and any error messages. Provide your login history report from the Self-Service Portal. Do not attempt further login if the compromise is active.

**Do not:**
- Share your new password with anyone, including IT staff. IT will never ask for your password.
- Reuse passwords from other accounts or previous passwords.
- Use a public or shared device until your account is verified clean.

**Escalation condition:** Always escalate suspected compromises to IT Security. They will audit your account for unauthorized access, review activity logs, and advise on additional protective measures.

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
