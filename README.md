# data-ingestion-service

## Data Ingestion Service – Approach

---

## 1. High-Level Design

I will build a backend API using **FastAPI** to handle CSV uploads for three data types:
- Stores  
- Users  
- Store-User Mappings  

Each file will be processed through a structured pipeline:

Upload → Stream Read (Chunked) → Row Validation → Data Normalization → Lookup Resolution (Get-or-Create) → Batch Insert → Error Reporting

The system exposes separate endpoints for each file type and enforces processing order:
- Stores and Users → first  
- Store-User Mappings → after dependencies are available  

---

## 2. Validation Strategy

Each row undergoes strict validation before ingestion:

- **Required fields**: Ensuring mandatory columns are present  
- **Data types**: Integers, floats, booleans, and dates validated  
- **Format checks**: Email and phone number validation  
- **Length constraints**: Enforcing column limits  
- **Uniqueness**:  
  - Within file (e.g., duplicate usernames, store_ids)  
  - At database level (unique constraints)  

Validation errors are collected per row with:
- Row number  
- Column name  
- Reason  

---

## 3. Data Normalization & Lookup Handling

Lookup tables:
- `store_brands`
- `store_types`
- `cities`
- `states`
- `countries`
- `regions`

These are populated dynamically using a **get-or-create** approach.

### Normalization steps:
- Trim whitespace (`strip()`)  
- Convert to lowercase for consistency  

### Performance optimization:
- Maintain an **in-memory cache (dictionary)** per lookup table  
- Avoid repeated database queries for identical values  

This ensures consistent and deduplicated reference data.

---

## 4. Failure Handling Strategy

Invalid rows will be **skipped**, while valid rows are ingested.

### Reasoning:
- Prevents blocking large uploads due to a few bad rows  
- Aligns with real-world ingestion systems  
- Improves usability for clients  

All failed rows are returned in a structured error report:
- JSON response or downloadable file  
- Includes row number, column, and reason  

---

## 5. Performance Strategy (Handling 500K Rows)

To ensure scalability:

- **Streaming CSV reading** (avoid full memory load)  
- **Chunk processing** (e.g., 1000–5000 rows per batch)  
- **Bulk insert operations** using ORM batch methods or raw SQL  
- **Lookup caching** to minimize database round trips  

This ensures efficient memory usage and high throughput.

---

## 6. Mapping File Handling

The store-user mapping file is processed **only after** stores and users are ingested.

Validation includes:
- Existence of referenced `store_id` and `user_id`  
- Uniqueness constraint: `(user_id, store_id, date)`  

Invalid references are captured and reported as errors.

---

## 7. Tradeoffs Considered

- **Skip vs Reject entire file**  
  Skipping improves usability and throughput but requires detailed error tracking  

- **Bulk insert vs Row-by-row insert**  
  Bulk insert significantly improves performance at the cost of slightly more complex logic  

- **Normalization strictness**  
  Lowercasing ensures consistency but may lose original casing; chosen for data integrity  

---

## Conclusion

This design focuses on:
- **Correctness**
- **Scalability**
- **Clear failure reporting**

In my previous work, I have implemented similar large-scale processing systems using **FastAPI, Celery, and Redis**, which influenced this approach toward building a reliable and performant ingestion pipeline.