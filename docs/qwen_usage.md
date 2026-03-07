# Using Qwen3.5 locally (Chat Completions API)

To use `inference.py` you need a **local server** that exposes an OpenAI-compatible API. This guide uses vLLM. The model is stored under `models/Qwen/` (e.g. `models/Qwen/Qwen3.5-4B`).

## 0. Download the model

Download the model using the Python script and choose the model you want. You can change the model later by running the script again with a different `--repo-id`.

From the **repository root**:

```bash
python utils/qwen/download_model.py
```

This downloads the default model (Qwen/Qwen3.5-4B) to `models/Qwen/Qwen3.5-4B`.

To select a different Qwen model, pass `--repo-id` with the Hugging Face repo ID:

```bash
python utils/qwen/download_model.py --repo-id Qwen/Qwen3.5-4B
# or e.g. another variant:
# python utils/qwen/download_model.py --repo-id Qwen/Qwen3.5-7B
```

Optional: use a custom base directory for models:

```bash
python utils/qwen/download_model.py --models-dir /path/to/models --repo-id Qwen/Qwen3.5-4B
```

## 1. Install vLLM

Use the same environment as the project (e.g. `annotator`). Install vLLM with:

```bash
uv pip install -U vllm \
    --torch-backend=auto \
    --extra-index-url https://wheels.vllm.ai/nightly
```

## 2. Environment variables

Your `.env` should contain:

- `OPENAI_BASE_URL="http://localhost:8000/v1"`
- `OPENAI_API_KEY="EMPTY"`

If you don't use `.env`, export before running the client:

```bash
export OPENAI_BASE_URL="http://localhost:8000/v1"
export OPENAI_API_KEY="EMPTY"
```

## 3. Start the server

From the **repository root**, run (adjust the model path if you used a different `--repo-id`):

```bash
vllm serve models/Qwen/Qwen3.5-4B --served-model-name "Qwen/Qwen3.5-4B" --port 8000
```

Wait until the model is loaded and you see something like “Application startup complete”. The API will be available at `http://localhost:8000/v1`.

## 4. Run the client

In **another terminal**, with the server running:

```bash
python test/qwen/inference.py
```

(From the repository root, or use the full path to `inference.py`.)

The script uses the recommended sampling parameters for general thinking mode: `temperature=1.0`, `top_p=0.95`, `presence_penalty=1.5`, `top_k=20`.

## Summary

| Step | Action |
|------|--------|
| 0 | Download model: `python utils/qwen/download_model.py` (use `--repo-id` to pick another model) |
| 1 | `uv pip install -U vllm --torch-backend=auto --extra-index-url https://wheels.vllm.ai/nightly` |
| 2 | Set `.env` with `OPENAI_BASE_URL` and `OPENAI_API_KEY=EMPTY` |
| 3 | Terminal 1: `vllm serve models/Qwen/Qwen3.5-4B --served-model-name "Qwen/Qwen3.5-4B" --port 8000` |
| 4 | Terminal 2: `python test/qwen/inference.py` |

If the model name shown by vLLM at startup differs from `Qwen/Qwen3.5-4B`, update the `model="Qwen/Qwen3.5-4B"` argument in `inference.py` to match. If you downloaded a different model with `--repo-id`, use that model path and name when serving and in `inference.py`.
