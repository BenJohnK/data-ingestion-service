# data-ingestion-service

Data Ingestion Service – Approach

1. High-Level Design

I will build a backend API using FastAPI to handle CSV uploads for three data types: stores, users, and store-user mappings. Each file will be processed independently through a structured pipeline:

Upload → Stream Read (chunked) → Row Validation → Data Normalization → Lookup Resolution (get-or-create) → Batch Insert → Error Reporting

The system will expose separate endpoints for each file type and enforce processing order (stores/users before mappings).

2. Validation Strategy

Each row will undergo strict validation before ingestion:

Required fields: Ensuring mandatory columns are present
Data types: Integers, floats, booleans, and dates validated
Format checks: Email and phone number validation
Length constraints: Enforcing column limits
Uniqueness: Within file (e.g., duplicate usernames/store_ids) and database-level constraints

Validation errors will be collected per row with details: row number, column, and reason.

3. Data Normalization & Lookup Handling

Lookup tables (store_brands, store_types, cities, states, countries, regions) will be populated dynamically using a get-or-create approach.

Before lookup:

Trim whitespace (strip())
Convert to lowercase for consistency

To optimize performance:

Maintain an in-memory cache (dictionary) for each lookup table
Avoid repeated database queries for the same values

This ensures consistent and deduplicated reference data.

4. Failure Handling Strategy

I will skip invalid rows and ingest valid ones.

Reasoning:

Prevents blocking large uploads due to a few bad rows
Aligns with real-world ingestion systems
Provides better usability for clients

All failed rows will be returned in a structured error report (JSON or downloadable file), enabling correction and re-upload.

5. Performance Strategy (500K Rows)

To handle large files efficiently:

Streaming CSV reading to avoid loading entire file into memory
Chunk processing (e.g., 1000–5000 rows per batch)
Bulk insert operations using ORM batch methods or raw SQL
Lookup caching to reduce database round trips

This ensures scalability and efficient memory usage.

6. Mapping File Handling

The store-user mapping file will only be processed after stores and users are ingested.

Validate existence of referenced store_id and user_id
Enforce uniqueness constraint (user_id, store_id, date)
Invalid references will be reported as errors

7. Tradeoffs Considered
Skip vs Reject entire file: Skipping improves usability and throughput but requires detailed error tracking
Bulk insert vs row-by-row: Bulk insert significantly improves performance at the cost of slightly more complex logic
Normalization strictness: Lowercasing ensures consistency but may lose original casing; chosen for data integrity


This design focuses on correctness, scalability, and clarity of failure reporting. In my previous project, I have implemented similar asynchronous and batch-processing workflows using FastAPI, Celery, and Redis for handling large-scale operations reliably, which influenced my approach to designing this ingestion pipeline.