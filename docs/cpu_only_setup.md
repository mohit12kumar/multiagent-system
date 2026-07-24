# Local Execution Guide: CPU & GPU Acceleration

This guide details configurations for running the clinical NER pipeline efficiently on both CPU-only hosts and GPU-accelerated environments.

## 1. GPU Acceleration (CUDA)

If a compatible NVIDIA GPU and CUDA Toolkit are installed on your host:
1. Install the GPU-enabled PyTorch build in your virtual environment:
   ```bash
   # Example for CUDA 12.1
   pip install torch --index-url https://download.pytorch.org/whl/cu121
   ```
2. The [BiobertAgent](file:///d:/office project/multiagent_system/src/agents/extraction/biobert_agent.py) and [EmbeddingModel](file:///d:/office project/multiagent_system/src/utils/embedding_model.py) will automatically detect CUDA via `torch.cuda.is_available()` and shift model weights and inputs to device `0` ("cuda").
3. You can verify GPU utilisation during extraction runs via:
   ```bash
   nvidia-smi
   ```

To force a specific execution device, edit `config/agents.yaml`:
```yaml
biobert_agent:
  device: 0  # Set to -1 to force CPU execution even when CUDA is present
```

---

## 2. CPU-Only Optimizations

If no GPU is detected, the pipeline automatically falls back to CPU-only execution and uses the following optimizations:

### A. ONNX Runtime Inference Speedup
1. Ensure Optimum and ONNX Runtime are installed:
   ```bash
   pip install "optimum[onnxruntime]"
   ```
2. Export the PyTorch model to ONNX:
   ```bash
   optimum-cli export onnx --model Almannaa/BioBERT-NER-Diseases models/onnx/biomedical-ner-all/
   ```
3. Set `onnx_model_path` in `config/agents.yaml` to load ONNX model files dynamically.

### B. Core Pinning & Thread Control
Restrict PyTorch and ONNX thread pools to prevent CPU thread starvation:
```bash
# Windows PowerShell
$env:OMP_NUM_THREADS="4"
$env:MKL_NUM_THREADS="4"

# Linux/macOS
export OMP_NUM_THREADS=4
```

### C. LLM Capping
The router caps Ollama calls per document via `max_llm_calls_per_document: 5` in `config/agents.yaml`. Ensure you pull the lightweight `llama3.2:3b` model:
```bash
ollama pull llama3.2:3b
```
