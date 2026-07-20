# Authentication Flow

Register

↓

Validate input

↓

Hash password

↓

Store user

↓

Return JWT tokens

---------------------

Login

↓

Validate credentials

↓

Generate JWT

↓

Return access token

---------------------

Protected Routes

↓

Verify JWT

↓

Load current user

↓

Process request