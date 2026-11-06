# What is retrieval augmented generation?

*2026-11-06 · engine: offline:planner + template · 7 tool calls*

## Steps

1. `wikipedia('What is retrieval augmented generation?')` → FAILED: ProxyError: HTTPSConnectionPool(host='en.wikipedia.org', port=443): Max retries exceeded with url: /w/api.php?action=query&list=search&srsearch=What+is+retrieval+augmented+
2. `web_search('What is retrieval augmented generation?')` → FAILED: ProxyError: HTTPSConnectionPool(host='html.duckduckgo.com', port=443): Max retries exceeded with url: /html/?q=What+is+retrieval+augmented+generation%3F (Caused by ProxyErr
3. `github_search('retrieval augmented generation')` → ok, 5 results
4. `pypi_package('ragflow')` → ok, 1 results
5. `pypi_package('lightrag')` → ok, 1 results
6. `pypi_package('graphrag')` → ok, 1 results
7. `pypi_package('rag_techniques')` → FAILED: HTTPError: 404 Client Error: Not Found for url: https://pypi.org/pypi/rag_techniques/json

## Answer

**Question:** What is retrieval augmented generation?

**Most-starred matching repositories on GitHub** (searched 2026-11-06):
- **infiniflow/ragflow**: 93,680 stars, last push 2026-11-06 (active); its PyPI namesake doesn't link back to this repo, so no version is claimed. RAGFlow is an agent-native database: a Retrieval-Augmented Generation (RAG) engine that grew into context infr [1]
- **HKUDS/LightRAG**: 40,576 stars, last push 2026-11-05 (active); its PyPI namesake doesn't link back to this repo, so no version is claimed. [EMNLP2025] LightRAG: Simple and Fast Retrieval-Augmented Generation [2]
- **microsoft/graphrag**: 36,580 stars, last push 2026-11-02 (active); PyPI 3.3.0 released 2026-10-08 [3]. A modular graph-based Retrieval-Augmented Generation (RAG) system [4]
- **NirDiamant/RAG_Techniques**: 30,252 stars, last push 2026-11-02 (active). This repository showcases various advanced techniques for Retrieval-Augmented Generation (RAG) systems. Each t [5]
- **SciPhi-AI/R2R**: 8,066 stars, last push 2025-11-07 (364 days ago). SoTA production-ready AI retrieval system. Agentic Retrieval-Augmented Generation (RAG) with a RESTful API. [6]

**Answer:** by GitHub stars the leaders are infiniflow/ragflow, HKUDS/LightRAG, microsoft/graphrag. 4 of 5 were pushed to in the last 90 days, a reasonable sign of active maintenance. Stars measure popularity, not quality, so check the docs and issue tracker before choosing.

*Tools that failed (unreachable from this environment):* wikipedia(What is retrieval augmented generation?): ProxyError: HTTPSConnectionPool(host='en.wikipedia.org', port=443): Max retries exceeded with url: /w/api.php?action=query&list=search&srsearch=What+is+retrieval+augmented+; web_search(What is retrieval augmented generation?): ProxyError: HTTPSConnectionPool(host='html.duckduckgo.com', port=443): Max retries exceeded with url: /html/?q=What+is+retrieval+augmented+generation%3F (Caused by ProxyErr; pypi_package(rag_techniques): HTTPError: 404 Client Error: Not Found for url: https://pypi.org/pypi/rag_techniques/json

## Sources

1. https://github.com/infiniflow/ragflow
2. https://github.com/HKUDS/LightRAG
3. https://pypi.org/project/graphrag/
4. https://github.com/microsoft/graphrag
5. https://github.com/NirDiamant/RAG_Techniques
6. https://github.com/SciPhi-AI/R2R
