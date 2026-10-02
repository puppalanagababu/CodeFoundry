# CodeFoundry Database Schema & Architecture Guide

This document outlines the **production database architecture, relational schema, entity relationships, constraints, data flow, and database design** used by the CodeFoundry platform.

The database layer supports user management, coding challenges, test cases, challenge files, code submissions, automated evaluations, and achievement tracking.

---

## 1. Database Architecture Overview

CodeFoundry uses **PostgreSQL** as its primary relational database.

The database is accessed through the application's database/ORM layer and schema changes are managed through **Alembic migrations**.

```text
                         [ CodeFoundry Application ]
                                    │
                                    │
                                    ▼
                         [ Database / ORM Layer ]
                                    │
                                    │
                                    ▼
                         [ PostgreSQL Database ]
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
        [ User Data ]       [ Challenge Data ]     [ Evaluation Data ]
              │                     │                     │
              │              ┌──────┴──────┐              │
              │              ▼             ▼              │
              │        [ Test Cases ] [ Challenge Files ] │
              │                                            │
              └──────────────────┐       ┌─────────────────┘
                                 ▼       ▼
                            [ Submissions ]
                                  │
                                  ▼
                            [ Evaluations ]
                                  │
                                  ▼
                            [ Achievements ]
                                  │
                                  ▼
                         [ User Achievements ]
```

---

## 2. Database Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| Database Engine | PostgreSQL | Primary relational database |
| ORM / Database Layer | SQLAlchemy | Application-to-database interaction |
| Migration Framework | Alembic | Database schema versioning and migrations |
| Database Model | Relational | Structured entity and relationship storage |
| Flexible Data Type | JSONB | Structured variable-format data |
| Primary Key Type | BIGINT | Unique record identification |
| Relationship Mechanism | Foreign Keys | Referential integrity |

PostgreSQL provides the persistent storage layer for the CodeFoundry application.

The relational design separates independent business entities into dedicated tables and connects them using primary and foreign keys.

---

## 3. Database Entity Overview

The CodeFoundry database contains the following major application entities:

1. `users_user`
2. `challenges_challenge`
3. `challenges_testcase`
4. `challenges_challengefile`
5. `submissions_submission`
6. `evaluations_evaluation`
7. `evaluations_achievement`
8. `evaluations_userachievement`

The entities can be grouped into four major functional areas:

```text
USER MANAGEMENT
    └── users_user

CHALLENGE MANAGEMENT
    ├── challenges_challenge
    ├── challenges_testcase
    └── challenges_challengefile

SUBMISSION & EVALUATION
    ├── submissions_submission
    └── evaluations_evaluation

ACHIEVEMENT SYSTEM
    ├── evaluations_achievement
    └── evaluations_userachievement
```

---

## 4. Complete Entity Relationship Diagram

The following diagram represents the primary relationships between the application tables:

```text
                              ┌─────────────────────────┐
                              │       users_user        │
                              │─────────────────────────│
                              │ PK  id                  │
                              │     username            │
                              │     email               │
                              │     password            │
                              │     role                │
                              └────────────┬────────────┘
                                           │
                                      1    │    M
                                           ▼
                              ┌─────────────────────────┐
                              │ submissions_submission  │
                              │─────────────────────────│
                              │ PK  id                  │
                              │ FK  user_id             │
                              │ FK  challenge_id        │
                              │     code                │
                              │     files               │
                              │     language            │
                              │     status              │
                              │     score               │
                              └───────────┬───────┬─────┘
                                          │       │
                                       1  │       │  M
                                          │       │
                                          ▼       │
                              ┌──────────────────┐ │
                              │ evaluations_     │ │
                              │ evaluation       │ │
                              │──────────────────│ │
                              │ PK id            │ │
                              │ FK submission_id │ │
                              │ score            │ │
                              │ tests_passed     │ │
                              │ tests_failed     │ │
                              │ test_results     │ │
                              │ skill_breakdown  │ │
                              └──────────────────┘ │
                                                  │
                                             M    │    1
                                                  ▼
                              ┌─────────────────────────┐
                              │ challenges_challenge   │
                              │─────────────────────────│
                              │ PK  id                 │
                              │     title              │
                              │     slug               │
                              │     description        │
                              │     difficulty         │
                              │     challenge_type     │
                              │     programming_language│
                              │     points             │
                              └────────────┬────────────┘
                                           │
                                ┌──────────┴──────────┐
                                │                     │
                             1  │                     │  1
                                │                     │
                                ▼                     ▼
                    ┌─────────────────────┐   ┌──────────────────────┐
                    │ challenges_testcase │   │ challenges_challenge │
                    │─────────────────────│   │ file                 │
                    │ PK id               │   │──────────────────────│
                    │ FK challenge_id     │   │ PK id                │
                    │ name                │   │ FK challenge_id      │
                    │ input_data          │   │ path                 │
                    │ expected_output     │   │ content              │
                    │ is_hidden           │   │ is_test              │
                    │ points              │   │ is_readonly          │
                    └─────────────────────┘   └──────────────────────┘


                              ┌─────────────────────────┐
                              │ evaluations_achievement │
                              │─────────────────────────│
                              │ PK id                  │
                              │     code               │
                              │     name               │
                              │     description        │
                              │     requirement_type   │
                              │     requirement_value  │
                              └────────────┬────────────┘
                                           │
                                      1    │    M
                                           ▼
                              ┌─────────────────────────┐
                              │ evaluations_            │
                              │ userachievement         │
                              │─────────────────────────│
                              │ PK id                  │
                              │ FK user_id             │
                              │ FK achievement_id      │
                              │     earned_at          │
                              └────────────┬────────────┘
                                           │
                                           │ M
                                           ▼
                                      [ users_user ]
```

---

## 5. Table: `users_user`

### 5.1 Purpose

The `users_user` table stores registered CodeFoundry users and their account-related information.

The table also contains role and account-status fields used to distinguish different types of users.

### 5.2 Schema

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGINT | **PRIMARY KEY** | Unique user identifier |
| `username` | VARCHAR(150) | **UNIQUE** | User's unique username |
| `password` | VARCHAR(128) | | Stored password value |
| `first_name` | VARCHAR(150) | | User first name |
| `last_name` | VARCHAR(150) | | User last name |
| `email` | VARCHAR(254) | | User email address |
| `role` | VARCHAR(20) | | User role |
| `is_superuser` | BOOLEAN | | Superuser permission flag |
| `is_staff` | BOOLEAN | | Staff permission flag |
| `is_active` | BOOLEAN | | Account activation status |
| `last_login` | DATETIME | | Last login timestamp |
| `date_joined` | DATETIME | | Account creation timestamp |

### 5.3 Supported User Roles

```text
STUDENT
TRAINER
ADMIN
RECRUITER
```

### 5.4 Relationships

```text
users_user
     │
     ├──────────────< submissions_submission
     │
     └──────────────< evaluations_userachievement
```

One user can create multiple submissions and can earn multiple achievements.

---

## 6. Table: `challenges_challenge`

### 6.1 Purpose

The `challenges_challenge` table stores the coding challenges available on the platform.

It contains challenge metadata, programming language information, execution limits, scoring information, and activation status.

### 6.2 Schema

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGINT | **PRIMARY KEY** | Unique challenge identifier |
| `title` | VARCHAR(200) | | Challenge title |
| `slug` | VARCHAR(50) | **UNIQUE** | Unique URL-friendly challenge identifier |
| `description` | TEXT | | Challenge description |
| `difficulty` | VARCHAR(20) | | Challenge difficulty |
| `challenge_type` | VARCHAR(20) | | Challenge category/type |
| `programming_language` | VARCHAR(50) | | Required programming language |
| `starter_code` | TEXT | | Initial code provided to users |
| `entrypoint` | VARCHAR(255) | | Code execution entry point |
| `time_limit` | INT | | Maximum execution time |
| `memory_limit` | INT | | Maximum memory allowed |
| `points` | INT | | Challenge score |
| `is_active` | BOOLEAN | | Challenge availability status |
| `created_at` | DATETIME | | Creation timestamp |
| `updated_at` | DATETIME | | Last modification timestamp |

### 6.3 Relationships

```text
challenges_challenge
       │
       ├──────────────< challenges_testcase
       │
       ├──────────────< challenges_challengefile
       │
       └──────────────< submissions_submission
```

One challenge can have multiple test cases, multiple files, and multiple submissions.

---

## 7. Table: `challenges_testcase`

### 7.1 Purpose

The `challenges_testcase` table stores the individual test cases used to validate submitted solutions.

### 7.2 Schema

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGINT | **PRIMARY KEY** | Unique test case identifier |
| `challenge_id` | BIGINT | **FOREIGN KEY** | Parent challenge |
| `name` | VARCHAR(100) | | Test case name |
| `input_data` | TEXT | | Input provided to the program |
| `expected_output` | TEXT | | Expected program output |
| `is_hidden` | BOOLEAN | | Whether the test case is hidden |
| `points` | INT | | Test case score |
| `is_active` | BOOLEAN | | Test case activation status |
| `created_at` | DATETIME | | Creation timestamp |
| `updated_at` | DATETIME | | Modification timestamp |

### 7.3 Foreign Key

```text
challenge_id
      │
      ▼
challenges_challenge.id
```

### 7.4 Relationship

```text
Challenge 1 ───────── M TestCase
```

---

## 8. Table: `challenges_challengefile`

### 8.1 Purpose

The `challenges_challengefile` table stores files required by multi-file coding challenges.

These files can contain source code, supporting code, or test-related files.

### 8.2 Schema

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGINT | **PRIMARY KEY** | Unique file identifier |
| `challenge_id` | BIGINT | **FOREIGN KEY** | Parent challenge |
| `path` | VARCHAR(255) | **UNIQUE WITH challenge_id** | File path |
| `content` | TEXT | | File contents |
| `is_test` | BOOLEAN | | Indicates test file |
| `is_readonly` | BOOLEAN | | Indicates whether file is read-only |
| `created_at` | DATETIME | | Creation timestamp |
| `updated_at` | DATETIME | | Modification timestamp |

### 8.3 Composite Unique Constraint

```text
UNIQUE (
    challenge_id,
    path
)
```

This ensures that a single challenge cannot contain two files with the same path.

### 8.4 Relationship

```text
Challenge 1 ───────── M ChallengeFile
```

---

## 9. Table: `submissions_submission`

### 9.1 Purpose

The `submissions_submission` table stores code submitted by users for coding challenges.

This table connects the submitting user with the selected challenge.

### 9.2 Schema

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGINT | **PRIMARY KEY** | Unique submission identifier |
| `user_id` | BIGINT | **FOREIGN KEY** | User who submitted the code |
| `challenge_id` | BIGINT | **FOREIGN KEY** | Challenge being attempted |
| `code` | TEXT | | Submitted source code |
| `files` | JSONB | | Submitted file information |
| `language` | VARCHAR(50) | | Programming language |
| `status` | VARCHAR(20) | | Submission status |
| `score` | INT | | Obtained score |
| `execution_time` | FLOAT | | Code execution time |
| `memory_used` | FLOAT | | Memory consumed |
| `test_results` | JSONB | | Test execution results |
| `submitted_at` | DATETIME | | Submission timestamp |
| `updated_at` | DATETIME | | Last modification timestamp |

### 9.3 Foreign Keys

```text
user_id
   │
   ▼
users_user.id
```

```text
challenge_id
      │
      ▼
challenges_challenge.id
```

### 9.4 Relationships

```text
User       1 ───────── M Submission

Challenge  1 ───────── M Submission
```

---

## 10. Table: `evaluations_evaluation`

### 10.1 Purpose

The `evaluations_evaluation` table stores the result generated after evaluating a submission.

It separates submission data from evaluation data.

### 10.2 Schema

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGINT | **PRIMARY KEY** | Unique evaluation identifier |
| `submission_id` | BIGINT | **FOREIGN KEY + UNIQUE** | Evaluated submission |
| `status` | VARCHAR(20) | | Evaluation status |
| `score` | INT | | Evaluation score |
| `tests_total` | INT | | Total tests executed |
| `tests_passed` | INT | | Tests passed |
| `tests_failed` | INT | | Tests failed |
| `execution_time` | FLOAT | | Execution duration |
| `memory_used` | FLOAT | | Memory consumption |
| `stdout` | TEXT | | Standard output |
| `stderr` | TEXT | | Standard error |
| `test_results` | JSONB | | Detailed test results |
| `skill_breakdown` | JSONB | | Skill-level evaluation data |
| `evaluated_at` | DATETIME | | Evaluation timestamp |
| `created_at` | DATETIME | | Record creation timestamp |

### 10.3 Relationship

```text
Submission 1 ───────── 1 Evaluation
```

The `submission_id` uniqueness constraint ensures that one submission can have at most one evaluation record.

---

## 11. Table: `evaluations_achievement`

### 11.1 Purpose

The `evaluations_achievement` table stores achievements or badges available to users.

Each achievement contains a requirement definition.

### 11.2 Schema

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGINT | **PRIMARY KEY** | Unique achievement identifier |
| `code` | VARCHAR(50) | **UNIQUE** | Unique achievement code |
| `name` | VARCHAR(100) | | Achievement name |
| `description` | TEXT | | Achievement description |
| `icon` | VARCHAR(50) | | Achievement icon identifier |
| `requirement_type` | VARCHAR(50) | | Requirement category |
| `requirement_value` | INT | | Required threshold/value |
| `is_active` | BOOLEAN | | Achievement activation status |
| `created_at` | DATETIME | | Creation timestamp |

### 11.3 Requirement Types

The project defines achievement requirement categories such as:

```text
BUG_FIX_COUNT
SECURITY_COUNT
PERFORMANCE_COUNT
TESTING_COUNT
PERFECT_SCORE_COUNT
TOTAL_COMPLETED_COUNT
```

---

## 12. Table: `evaluations_userachievement`

### 12.1 Purpose

The `evaluations_userachievement` table records achievements earned by individual users.

It functions as the association table between `users_user` and `evaluations_achievement`.

### 12.2 Schema

| Column | Data Type | Constraint | Description |
| :--- | :--- | :--- | :--- |
| `id` | BIGINT | **PRIMARY KEY** | Unique association identifier |
| `user_id` | BIGINT | **FOREIGN KEY** | User who earned the achievement |
| `achievement_id` | BIGINT | **FOREIGN KEY** | Achievement earned |
| `earned_at` | DATETIME | | Achievement earning timestamp |

### 12.3 Composite Unique Constraint

```text
UNIQUE (
    user_id,
    achievement_id
)
```

This prevents the same achievement from being recorded more than once for the same user.

### 12.4 Relationship

```text
User M ───────── M Achievement
       │
       │
       ▼
UserAchievement
```

---

## 13. Primary Key Reference

Every application table has an `id` field that acts as its primary key.

| Table | Primary Key | Data Type |
| :--- | :--- | :--- |
| `users_user` | `id` | BIGINT |
| `challenges_challenge` | `id` | BIGINT |
| `challenges_testcase` | `id` | BIGINT |
| `challenges_challengefile` | `id` | BIGINT |
| `submissions_submission` | `id` | BIGINT |
| `evaluations_evaluation` | `id` | BIGINT |
| `evaluations_achievement` | `id` | BIGINT |
| `evaluations_userachievement` | `id` | BIGINT |

---

## 14. Foreign Key Reference

| Child Table | Foreign Key | Parent Table | Parent Key |
| :--- | :--- | :--- | :--- |
| `challenges_testcase` | `challenge_id` | `challenges_challenge` | `id` |
| `challenges_challengefile` | `challenge_id` | `challenges_challenge` | `id` |
| `submissions_submission` | `user_id` | `users_user` | `id` |
| `submissions_submission` | `challenge_id` | `challenges_challenge` | `id` |
| `evaluations_evaluation` | `submission_id` | `submissions_submission` | `id` |
| `evaluations_userachievement` | `user_id` | `users_user` | `id` |
| `evaluations_userachievement` | `achievement_id` | `evaluations_achievement` | `id` |

---

## 15. Relationship Cardinality

| Relationship | Cardinality |
| :--- | :--- |
| User → Submission | 1 : M |
| Challenge → Submission | 1 : M |
| Challenge → TestCase | 1 : M |
| Challenge → ChallengeFile | 1 : M |
| Submission → Evaluation | 1 : 1 |
| User → UserAchievement | 1 : M |
| Achievement → UserAchievement | 1 : M |
| User ↔ Achievement | M : M through UserAchievement |

---

## 16. Unique Constraints

The database uses unique constraints to maintain data consistency.

| Table | Constraint | Purpose |
| :--- | :--- | :--- |
| `users_user` | `username` | Prevent duplicate usernames |
| `challenges_challenge` | `slug` | Prevent duplicate challenge slugs |
| `challenges_challengefile` | `challenge_id + path` | Prevent duplicate file paths within a challenge |
| `evaluations_evaluation` | `submission_id` | Limit a submission to one evaluation |
| `evaluations_achievement` | `code` | Prevent duplicate achievement codes |
| `evaluations_userachievement` | `user_id + achievement_id` | Prevent duplicate user-achievement assignments |

---

## 17. JSONB Data Storage

The database uses PostgreSQL's `JSONB` data type for flexible structured information.

The important JSONB fields are:

| Table | Column | Purpose |
| :--- | :--- | :--- |
| `submissions_submission` | `files` | Stores submission file information |
| `submissions_submission` | `test_results` | Stores submission test results |
| `evaluations_evaluation` | `test_results` | Stores detailed evaluation results |
| `evaluations_evaluation` | `skill_breakdown` | Stores skill-level evaluation information |

JSONB allows structured data to be stored without creating a separate relational column for every possible property.

---

## 18. Timestamp & Audit Fields

Timestamp fields are used to track important lifecycle events.

| Table | Field | Purpose |
| :--- | :--- | :--- |
| `users_user` | `last_login` | Last user login |
| `users_user` | `date_joined` | User registration time |
| `challenges_challenge` | `created_at` | Challenge creation |
| `challenges_challenge` | `updated_at` | Challenge modification |
| `challenges_testcase` | `created_at` | Test case creation |
| `challenges_testcase` | `updated_at` | Test case modification |
| `challenges_challengefile` | `created_at` | File creation |
| `challenges_challengefile` | `updated_at` | File modification |
| `submissions_submission` | `submitted_at` | Code submission time |
| `submissions_submission` | `updated_at` | Submission modification |
| `evaluations_evaluation` | `evaluated_at` | Evaluation completion time |
| `evaluations_evaluation` | `created_at` | Evaluation record creation |
| `evaluations_achievement` | `created_at` | Achievement creation |
| `evaluations_userachievement` | `earned_at` | Achievement earning time |

---

## 19. Database Data Flow

The primary database data flow is:

```text
                         [ User ]
                            │
                            │
                            ▼
                    [ Select Challenge ]
                            │
                            ▼
                       [ Challenge ]
                            │
                 ┌──────────┴──────────┐
                 │                     │
                 ▼                     ▼
           [ Test Cases ]      [ Challenge Files ]
                 │                     │
                 └──────────┬──────────┘
                            │
                            ▼
                      [ Submission ]
                            │
                            ▼
                      [ Evaluation ]
                            │
                 ┌──────────┼──────────┐
                 │          │          │
                 ▼          ▼          ▼
              [Score]   [Tests]   [Skills]
                            │
                            ▼
                       [ Achievement ]
                            │
                            ▼
                    [UserAchievement]
```

---

## 20. Submission & Evaluation Flow

A typical code-submission database flow is:

```text
1. User selects a challenge
             │
             ▼
2. Challenge information is retrieved
             │
             ▼
3. User submits source code
             │
             ▼
4. Submission record is created
             │
             ▼
5. Submission is evaluated
             │
             ▼
6. Evaluation record stores:
      ├── Score
      ├── Tests Passed
      ├── Tests Failed
      ├── Execution Time
      ├── Memory Usage
      ├── Standard Output
      ├── Standard Error
      ├── Test Results
      └── Skill Breakdown
             │
             ▼
7. Achievement conditions can be evaluated
             │
             ▼
8. UserAchievement records earned achievements
```

---

## 21. Challenge Data Flow

Challenge-related data is organized as:

```text
                   [ Challenge ]
                        │
             ┌──────────┴──────────┐
             │                     │
             ▼                     ▼
        [ Test Cases ]       [ Challenge Files ]
             │                     │
             └──────────┬──────────┘
                        │
                        ▼
                   [ Submission ]
```

A single challenge can therefore contain multiple test cases and multiple files while receiving submissions from multiple users.

---

## 22. Achievement Data Flow

The achievement system is represented by:

```text
                     [ User ]
                        │
                        │ completes activity
                        ▼
                [ Achievement Rule ]
                        │
                        ▼
                  [ Achievement ]
                        │
                        ▼
                [ UserAchievement ]
                        │
                        ▼
                  [ User Earned ]
```

The association table stores the user-achievement relationship and the timestamp at which the achievement was earned.

---

## 23. Database Normalization

The CodeFoundry database separates different business entities into independent tables.

For example:

```text
User Information
       │
       ▼
users_user

Challenge Information
       │
       ▼
challenges_challenge

Test Case Information
       │
       ▼
challenges_testcase

Submission Information
       │
       ▼
submissions_submission

Evaluation Information
       │
       ▼
evaluations_evaluation

Achievement Information
       │
       ▼
evaluations_achievement
```

This separation avoids storing unrelated information repeatedly in the same table.

The many-to-many relationship between users and achievements is handled through:

```text
users_user
     │
     ▼
evaluations_userachievement
     │
     ▼
evaluations_achievement
```

This is a standard relational approach for representing an association between two entities.

---

## 24. Referential Integrity

Foreign keys maintain valid relationships between related records.

For example:

```text
submissions_submission.user_id
              │
              ▼
        users_user.id
```

and:

```text
submissions_submission.challenge_id
              │
              ▼
      challenges_challenge.id
```

and:

```text
evaluations_evaluation.submission_id
              │
              ▼
      submissions_submission.id
```

These relationships allow the database to connect submissions with their users, challenges, and evaluations.

---

## 25. ORM Architecture

The application uses an ORM/database abstraction layer.

The conceptual flow is:

```text
Application Code
       │
       ▼
ORM / Database Models
       │
       ▼
Database Session
       │
       ▼
PostgreSQL
```

ORM provides a programmatic way to create, retrieve, update, and delete database records.

This also helps maintain consistent database access patterns throughout the backend.

---

## 26. Database Migration Architecture

Alembic is used to manage database schema changes.

The migration lifecycle is:

```text
Database Model Change
        │
        ▼
Migration Generation
        │
        ▼
Alembic Migration File
        │
        ▼
Migration Execution
        │
        ▼
PostgreSQL Schema Update
```

Migration files provide a history of database structure changes and allow the database schema to be updated in a controlled manner.

---

## 27. Database CRUD Operations

The database layer supports standard CRUD operations.

### CREATE

Used to create records such as:

```text
User
Challenge
TestCase
ChallengeFile
Submission
Evaluation
Achievement
UserAchievement
```

### READ

Used to retrieve:

```text
User information
Challenge information
Test cases
Challenge files
Submission history
Evaluation results
Achievements
```

### UPDATE

Used to modify records such as:

```text
User information
Challenge information
Test cases
Challenge files
Submission status
Evaluation information
```

### DELETE

Used where deletion functionality is implemented for the corresponding entity.

---

## 28. Database Security Considerations

The database layer should ensure that:

- Database credentials are not hard-coded in source files.
- Connection information is provided through secure configuration.
- Sensitive configuration values are stored using environment variables.
- ORM/database parameterization is used for database operations.
- User access is controlled through application-level authentication and authorization.
- Production database credentials should never be committed to source control.

The exact security controls should always match the implementation present in the deployment environment.

---

## 29. Complete Database Relationship Map

```text
                         ┌─────────────────┐
                         │      USER       │
                         └────────┬────────┘
                                  │
                       ┌──────────┴──────────┐
                       │                     │
                       ▼                     ▼
                ┌─────────────┐      ┌────────────────┐
                │ SUBMISSION  │      │ USERACHIEVEMENT│
                └──────┬──────┘      └───────┬────────┘
                       │                     │
                       │                     ▼
                       │              ┌──────────────┐
                       │              │ ACHIEVEMENT   │
                       │              └──────────────┘
                       │
                       ▼
                ┌─────────────┐
                │ EVALUATION  │
                └─────────────┘


                         ┌────────────────┐
                         │   CHALLENGE    │
                         └───────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
             ┌─────────────┐          ┌───────────────┐
             │  TESTCASE   │          │ CHALLENGEFILE │
             └─────────────┘          └───────────────┘
                    │
                    │
                    └──────────────┐
                                   ▼
                              SUBMISSION
```

---

## 30. Database Schema Quick Reference

| Entity | Purpose | Main Relationship |
| :--- | :--- | :--- |
| `users_user` | User accounts and roles | User → Submissions |
| `challenges_challenge` | Coding challenges | Challenge → TestCases |
| `challenges_testcase` | Challenge validation cases | TestCase → Challenge |
| `challenges_challengefile` | Challenge files | File → Challenge |
| `submissions_submission` | User code submissions | Submission → User/Challenge |
| `evaluations_evaluation` | Evaluation results | Evaluation → Submission |
| `evaluations_achievement` | Achievement definitions | Achievement → Users |
| `evaluations_userachievement` | Earned achievements | User ↔ Achievement |

---

## 31. Database Design Summary

```text
Database Engine
    PostgreSQL

ORM / Database Layer
    SQLAlchemy

Migration Tool
    Alembic

Main Application Tables
    8

Primary Key
    id

Primary Key Type
    BIGINT

Flexible Data Storage
    JSONB

Major Relationships
    User → Submission
    Challenge → Submission
    Challenge → TestCase
    Challenge → ChallengeFile
    Submission → Evaluation
    User ↔ Achievement
```

---

## 32. Database Architecture Summary

The CodeFoundry database is organized around the complete coding-platform lifecycle:

```text
                    USER
                      │
                      ▼
                  CHALLENGE
                      │
              ┌───────┴───────┐
              ▼               ▼
          TEST CASES      CHALLENGE FILES
              │               │
              └───────┬───────┘
                      ▼
                  SUBMISSION
                      │
                      ▼
                  EVALUATION
                      │
                      ▼
                 ACHIEVEMENT
                      │
                      ▼
              USER ACHIEVEMENT
```

The relational schema uses **primary keys, foreign keys, unique constraints, association tables, timestamps, and JSONB fields** to support the platform's core database requirements.

---

## 33. Database Viva — Quick Questions

### Q1. Which database is used in CodeFoundry?

PostgreSQL is used as the primary relational database.

### Q2. Which ORM is used?

SQLAlchemy is used for ORM/database interaction.

### Q3. Which migration tool is used?

Alembic is used for database schema migrations.

### Q4. What is the primary key?

A primary key uniquely identifies each record in a table. The main tables use the `id` column as the primary key.

### Q5. What is a foreign key?

A foreign key connects a record in one table with a record in another table.

### Q6. How is User related to Submission?

One user can have many submissions, so it is a one-to-many relationship.

### Q7. How is Challenge related to TestCase?

One challenge can have many test cases.

### Q8. How is Submission related to Evaluation?

One submission can have one evaluation because `submission_id` is unique in the Evaluation table.

### Q9. Why is UserAchievement required?

It connects users with the achievements they have earned and implements the user-achievement many-to-many relationship.

### Q10. Why is JSONB used?

JSONB is used for flexible structured information such as test results, submitted files, and skill breakdown data.

### Q11. What is a migration?

A migration is a controlled database schema change, such as creating a table or adding a column.

### Q12. What is referential integrity?

It ensures that foreign-key relationships between related database records remain valid.

---

## 34. 30-Second Database Explanation

> CodeFoundry uses PostgreSQL as its relational database, with SQLAlchemy for database interaction and Alembic for migrations. The main tables manage users, coding challenges, test cases, challenge files, submissions, evaluations, and achievements. Users can submit solutions for challenges, and each submission is connected to an evaluation containing scores and test results. Challenges can contain multiple test cases and files. Foreign keys maintain relationships between tables, while the UserAchievement table manages the many-to-many relationship between users and achievements.

---

## 35. Final Database Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                     CODEFOUNDRY DATABASE                     │
│                         PostgreSQL                           │
└──────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼──────────────────────┐
        │                     │                      │
        ▼                     ▼                      ▼
     USERS               CHALLENGES             ACHIEVEMENTS
        │                     │                      │
        │              ┌──────┴──────┐               │
        │              │             │               │
        │              ▼             ▼               │
        │          TESTCASES   CHALLENGEFILES        │
        │              │             │               │
        └──────────────┼─────────────┘               │
                       ▼                             │
                  SUBMISSIONS                        │
                       │                             │
                       ▼                             │
                  EVALUATIONS                        │
                       │                             │
                       └──────────────┬──────────────┘
                                      ▼
                              USERACHIEVEMENTS
```

This schema provides the persistent data layer required to support CodeFoundry's **user management, coding challenges, code submission, automated evaluation, and achievement tracking functionality**.