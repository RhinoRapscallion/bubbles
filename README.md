# bubbles
A small flask forum

Testing only, not tested nor ready for public use.

Main page shows cronologincal posts and random posts, post page allows comments

Login system uses Argon2 for password Hashing, serverSecrets should be populated with a crypto-secure random string, will work with an empty string, but nothing will be secure.

Sessions are stored via JWT token cookies, cookies are also used for returning to pages after failed logins, and to return the contents of the posts page after one logs in.
