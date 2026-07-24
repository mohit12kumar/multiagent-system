# Agent Specifications

## 1. Preprocessing Agent
- **Type**: Rule-based text cleaner and parser.
- **Inputs**: Raw document text.
- **Outputs**: Cleaned text and tokenized sentences with absolute start/end offsets.
- **Responsibility**: Clean extra spaces/newlines and segment input.

## 2. SpaCy Agent
- **Type**: Statistical NLP model.
- **Inputs**: Segmented sentences.
- **Outputs**: Entity mentions (PERSON, ORG, GPE, LOC, DATE, TIME) mapped to document-level character indexes.
- **Model**: `en_core_web_sm` (with auto-download capabilities).

## 3. Hugging Face Agent
- **Type**: Deep learning transformer model.
- **Inputs**: Segmented sentences.
- **Outputs**: Contextual named entities (PER, ORG, LOC, MISC).
- **Model**: `dbmdz/bert-large-cased-finetuned-conll03-english` (aggregated simple strategy).

## 4. Ollama Agent
- **Type**: Local Large Language Model (LLM).
- **Inputs**: Segmented sentences.
- **Outputs**: Structural JSON matches (PERSON, ORGANIZATION, LOCATION, PRODUCT, EVENT).
- **Model**: `llama3` (or `mistral` fallback) via local Ollama client. Enforces format validation.

## 5. Date/Time Agent
- **Type**: Rule-based regex parser.
- **Inputs**: Segmented sentences.
- **Outputs**: Highly accurate dates and times (DATE, TIME).
- **Responsibility**: Fast pattern matching without model overhead.

## 6. Aggregation Agent
- **Type**: Conflict resolver and scorer.
- **Inputs**: Combined raw extractions.
- **Outputs**: Merged entity spans.
- **Strategy**: Groups overlaps into clusters. Resolves bounds based on agent weights (HF: 1.5, Ollama: 1.2, SpaCy: 1.0, Date/Time: 2.0). Boosts confidence scores for overlapping matches.

## 7. Validation Agent
- **Type**: Taxonomy aligner.
- **Inputs**: Aggregated entities.
- **Outputs**: Schema-compliant entities.
- **Responsibility**: Maps entity types (e.g. PER -> PERSON, GPE -> LOCATION) and checks constraints (e.g., regex checks, character lengths).

## 8. Disambiguation Agent
- **Type**: Semantic matcher and linker.
- **Inputs**: Validated entities.
- **Outputs**: Entities linked to canonical database keys.
- **Strategy**: Queries Chroma vector store. Links matches > 0.82 similarity. Falls back to Wikidata search APIs. Identifies new/low-confidence entities for human review.

## 9. Formatting Agent
- **Type**: Output decorator.
- **Inputs**: Linked entities.
- **Outputs**: Final formatted JSON response payload.
