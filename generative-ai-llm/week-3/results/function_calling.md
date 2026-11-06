# Function calling runs

## What's the latest version of fastapi?

*engine: rule planner*

Function calls (validated against the JSON schema before running):

- `{"name": "get_package_info", "arguments": {"name": "fastapi"}}` → ✅ ok

**fastapi 0.162.0** (released 2026-10-23, 359 releases, licence MIT): FastAPI framework, high performance, easy to learn, fast to code, ready for production. https://pypi.org/project/fastapi/

## Compare httpx, requests and aiohttp

*engine: rule planner*

Function calls (validated against the JSON schema before running):

- `{"name": "compare_packages", "arguments": {"names": ["httpx", "requests", "aiohttp"]}}` → ✅ ok

| Package | Latest | Released | Releases |
|---|---|---|---|
| httpx | 0.28.1 | 2024-12-06 | 77 |
| requests | 2.34.2 | 2026-05-14 | 163 |
| aiohttp | 3.14.5 | 2026-10-11 | 314 |

## Find the top 25 vector database repositories in rust

*engine: rule planner*

Function calls (validated against the JSON schema before running):

- `{"name": "search_github", "arguments": {"query": "vector database", "sort": "stars", "limit": 25, "language": "rust"}}` → ❌ invalid arguments for search_github: 25 is greater than the maximum of 10
- `{"name": "search_github", "arguments": {"query": "vector database", "sort": "stars", "limit": 10, "language": "rust"}}` → ✅ ok

- [qdrant/qdrant](https://github.com/qdrant/qdrant): 35,448 ★, updated 2026-11-06. Qdrant - High-performance, massive-scale Vector Database and Vector Search Engine for the next gener
- [xerj-org/xerj](https://github.com/xerj-org/xerj): 18,466 ★, updated 2026-11-06. AI search engine and MCP server for bots and agents. One Rust binary indexes code, docs, logs, JSONL
- [HelixDB/helix-db](https://github.com/HelixDB/helix-db): 6,270 ★, updated 2026-11-06. HelixDB is an OLTP graph database with native vector and full-text search built in Rust on Object St
- [cozodb/cozo](https://github.com/cozodb/cozo): 4,141 ★, updated 2024-12-04. A transactional, relational-graph-vector database that uses Datalog for query. The hippocampus for A
- [tensorchord/pgvecto.rs](https://github.com/tensorchord/pgvecto.rs): 2,191 ★, updated 2025-02-26. Scalable, Low-latency and Hybrid-enabled Vector Search in Postgres. Revolutionize Vector Search, not
- [microsoft/DiskANN](https://github.com/microsoft/DiskANN): 1,968 ★, updated 2026-11-06. A vector indexing library to bring fast, fresh and filtered search to your database
- [skyzh/type-exercise-in-rust](https://github.com/skyzh/type-exercise-in-rust): 1,519 ★, updated 2026-10-06. Learn advanced Rust by building a type-safe, auto-vectorized database expression engine
- [kividbio/kividb](https://github.com/kividbio/kividb): 964 ★, updated 2026-11-06. A fast, multi-threaded Redis® and Valkey alternative written in Rust: drop-in compatible, with full-
- [lanterndata/lantern](https://github.com/lanterndata/lantern): 896 ★, updated 2024-12-12. PostgreSQL vector database extension for building AI applications
- [Pometry/Raphtory](https://github.com/Pometry/Raphtory): 651 ★, updated 2026-11-06. Scalable graph analytics database powered by a multithreaded, vectorized temporal engine, written in

## Convert 3.5 GB to MB

*engine: rule planner*

Function calls (validated against the JSON schema before running):

- `{"name": "convert_units", "arguments": {"value": 3.5, "from_unit": "gb", "to_unit": "mb"}}` → ✅ ok

3.5 gb = **3584 mb**

## What's the licence of the package definitely-not-a-real-package-xyz?

*engine: rule planner*

Function calls (validated against the JSON schema before running):

- `{"name": "get_package_info", "arguments": {"name": "definitely-not-a-real-package-xyz"}}` → ✅ ok

no package called 'definitely-not-a-real-package-xyz' on PyPI

## Book me a flight to Goa

*engine: rule planner*

Function calls (validated against the JSON schema before running):

- none

I couldn't map that request to any of my functions (PyPI info, package comparison, GitHub search, unit conversion).

