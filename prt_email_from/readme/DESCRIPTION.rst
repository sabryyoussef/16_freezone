This module allows to customise **From** and **Reply-to**
email address for outgoing email messages.

* Add company name to sender's name in **From** field:

  :Before: `Some User mycompany@example.com`
  :After: `Some User via My Company mycompany@example.com`

* Add sender's name to company name in **Reply-to** field:

  :Before: `My Company mycompany@example.com`
  :After: `Some User via My Company mycompany@example.com`

* Set names joint for **From** and **Reply-to** fields:

  :Before: `Some User My Company mycompany@example.com`
  :After: `Some User via My Company mycompany@example.com`


:Remember: your mail server must support sending emails using 'from' addresses you have defined!
:Notice: when sending email using template 'From' address configured in template will be used by default!
