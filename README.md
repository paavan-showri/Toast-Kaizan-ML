# FPC Lean AI Scaffold

This scaffold gives you a starter architecture for:

- Flow Process Chart parsing
- semantic extraction
- ontology + ML classification
- graph-based pattern detection
- 5W1H + ECRSSA recommendation generation
- Streamlit integration

## Files included

- `models/schema.py`
- `models/label_sets.py`
- `models/ontology.py`
- `engine/normalizer.py`
- `engine/parser.py`
- `engine/semantic_extractor.py`
- `engine/embedding_matcher.py`
- `engine/ml_classifier.py`
- `engine/graph_builder.py`
- `engine/pattern_detector.py`
- `engine/llm_reasoner.py`
- `engine/validator.py`
- `engine/confidence.py`
- `engine/orchestrator.py`
- `pages/3_5W1H_ECRSSA_Analysis.py`
- `requirements.txt`

## How to use

1. Copy the folders into your Streamlit project.
2. Install the requirements.
3. Run your app.
4. Open the `3_5W1H_ECRSSA_Analysis.py` page.
5. Upload an Excel or CSV flow process chart.

## Notes

- The page works without a real LLM connection because `engine/llm_reasoner.py`
  includes a deterministic fallback reasoner.
- You can later connect your own LLM by passing a callback into `run_pipeline()`.
- `sentence-transformers` and `transformers` may take time to download models on first run.
- If those ML packages are unavailable, the code falls back to safe uniform scores.

## Recommended next improvements

- add spaCy-based action/object extraction
- create your own labeled FPC dataset
- fine-tune step/waste/ECRS classifiers
- add future-state precedence revision logic
- connect OR-Tools for future-state scheduling
