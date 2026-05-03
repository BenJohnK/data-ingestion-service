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

## 8. Supervisor Resolution Strategy (Users)

User data includes a `supervisor_username` instead of a direct foreign key.

To handle this efficiently:

- **Phase 1**: Insert all valid users with `supervisor_id = NULL`
- **Phase 2**: Resolve supervisor relationships using a username → id map

This avoids:
- Multiple database lookups per row
- Ordering issues where supervisors may appear later in the file

This two-phase approach ensures correctness while maintaining performance.

## Conclusion

This design focuses on:
- **Correctness**
- **Scalability**
- **Clear failure reporting**

In my previous work, I have implemented similar large-scale processing systems using **FastAPI, Celery, and Redis**, which influenced this approach toward building a reliable and performant ingestion pipeline.

---

## Setup & Run Instructions

### 1. Clone the repository

```bash
git clone https://github.com/BenJohnK/data-ingestion-service.git
cd data-ingestion-service
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup PostgreSQL

- Create a database (e.g., `ingestion_db`)
- Copy `.env.example` → `.env`
- Update DB credentials in `.env`

### 5. Run the application

```bash
uvicorn app.main:app --reload
```

---

## API Endpoints

### 1. Upload Stores

```bash
curl -X POST "http://127.0.0.1:8000/upload/stores" -F "file=@stores_master.csv"
```

### 2. Upload Users

```bash
curl -X POST "http://127.0.0.1:8000/upload/users" -F "file=@users_master.csv"
```

### 3. Upload Store-User Mapping (PJP)

```bash
curl -X POST "http://127.0.0.1:8000/upload/pjp" -F "file=@store_user_mapping.csv"
```

### 4. Download error file (csv)

```bash
curl -X GET "http://127.0.0.1:8000/download-errors/<error_filename.csv>"
```

---

## Performance Evidence

A performance test was conducted using the provided `stores_master_500k.csv` file.

### Results

- **Total rows processed:** 500,000  
- **Valid rows ingested:** 492,846  
- **Invalid rows skipped:** 7,154  
- **Total processing time:** 36.94 seconds  
- **Chunks processed:** 500

### 💻 Environment

Tested locally on:
- Ubuntu 24.04
- Intel i5 (13th Gen)
- 16GB RAM

### ⚙️ Processing Strategy

- **Synchronous processing** using FastAPI endpoint  
- **Chunked CSV reading** (streaming, avoids loading full file into memory)  
- **Batch processing per chunk**  
- **Bulk insert operations** using SQLAlchemy (`bulk_save_objects`)  
- **In-file deduplication** to prevent duplicate entries  
- **Database-level deduplication** using indexed lookups  
- **Lookup caching (in-memory, request-scoped)** to minimize repeated DB queries  

### ❌ Failure Handling

- Invalid rows are **skipped**, not blocking ingestion  
- Detailed error reporting is generated with:
  - Row number  
  - Field name  
  - Error reason  

- Full error report is generated as a CSV file:
  - Example: `errors_store_<timestamp>.csv`

### 📎 Evidence

- Execution proof:  
  `performance_evidence/ingestion_500k_screenshot.png`

- Sample error report (trimmed):  
  `performance_evidence/sample_error_report.csv`