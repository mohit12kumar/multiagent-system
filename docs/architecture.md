# System Architecture

## Overview
This system uses a Multi-Agent Named Entity Recognition (NER) architecture to extract, resolve, validate, link, and format structured entities from raw documents.

```
                  ┌──────────────────────┐
                  │   FastAPI Client     │
                  └──────────┬───────────┘
                             │ Submit Document
                             ▼
                  ┌──────────────────────┐
                  │ Coordinator Pipeline │◄───[LangSmith Tracing]
                  └──────────┬───────────┘
                             │
            ┌────────────────┼────────────────┬──────────────┐
            │                │                │              │
            ▼                ▼                ▼              ▼
     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
     │ SpaCy Agent │  │  HF Agent   │  │Ollama Agent │  │ Date Agent  │
     └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
            │                │                │              │
            └────────────────┼────────────────┴──────────────┘
                             │ Raw Mentions
                             ▼
                  ┌──────────────────────┐
                  │  Aggregation Agent   │
                  └──────────┬───────────┘
                             │ Merged & Weighted Spans
                             ▼
                  ┌──────────────────────┐
                  │   Validation Agent   │
                  └──────────┬───────────┘
                             │ Taxonomy Mapped
                             ▼
                  ┌──────────────────────┐
                  │ Disambiguation Agent │◄───[ChromaDB / Wikidata]
                  └──────────┬───────────┘
                             │ Canonical ID
                             ▼
                  ┌──────────────────────┐
                  │   Formatting Agent   │
                  └──────────┬───────────┘
                             │ Save to MySQL / Respond
                             ▼
                  ┌──────────────────────┐
                  │     MySQL Store      │
                  └──────────────────────┘
```

## Core Layers

1. **API & Orchestrator Layer**:
   - `FastAPI`: Exposes HTTP endpoints for extraction runs and feedback ingestion.
   - `Coordinator`: Executes stages sequentially, handling failures and parallel extractions.
   - `Router`: Directs which extractors run based on text metadata.

2. **Multi-Agent Processing Layer**:
   - `PreprocessingAgent`: Cleans text and splits it into offset-tracked sentences.
   - `ExtractionAgents`: Extractor workers (SpaCy, HuggingFace transformers, Ollama LLM, Date/Time regex rules).
   - `AggregationAgent`: Groups overlapping boundaries and boosts confidence of agreed matches.
   - `ValidationAgent`: Validates and fits entities into a standardized schema/taxonomy.
   - `DisambiguationAgent`: Queries vector store (ChromaDB) to fetch candidates and links canonical identities.

3. **Storage & Memory Layer**:
   - `MySQL` (via `SQLAlchemy`): Stores documents, sessions, entity mentions, review queue items, and audit logs.
   - `ChromaDB`: High-performance vector database storing embeddings of canonical entities for semantic entity linking.

4. **Observability**:
   - `LangSmith`: Optional SDK integration logs coordinator pipelines and child agent execution spans automatically if environment keys are set.
   - `Prometheus & Grafana`: Metric scraper tracks API latency and request count volumes.
