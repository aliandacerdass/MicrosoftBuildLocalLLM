# Microsoft Foundry Local

Foundry Local is Microsoft's runtime for running large language models entirely on your own
device. It ships a model catalog, a download/cache manager, hardware-accelerated inference,
and SDKs for Python, C#, JavaScript and Rust. No Azure subscription, no cloud account, and
no network calls at inference time.

> Summarised in our own words from the official documentation:
> https://learn.microsoft.com/en-us/azure/foundry-local/get-started

## Why it matters for this project

A cloud LLM sends every question — and every document chunk you attach to it — to somebody
else's server. For private notes, internal manuals, or coursework, that is often
unacceptable. Foundry Local removes the network from the equation: the model weights sit on
your disk and the inference happens on your CPU, GPU or NPU.

The practical consequences:

- **Privacy.** Your documents never leave the machine.
- **No per-token cost.** Once the model is downloaded, questions are free.
- **Offline capability.** The assistant works on a plane, in a lab with no Wi-Fi, or behind
  an air-gapped network.
- **Latency floor.** No round trip to a datacenter, but you are limited by local hardware.

## Supported platforms

Foundry Local runs on Windows, macOS (Apple silicon) and Linux. On Windows there is a
separate package variant that binds to the Windows ML runtime and exposes a wider range of
hardware acceleration; the cross-platform package exposes the same API surface.

For Python the install is:

```bash
pip install foundry-local-sdk        # cross-platform (macOS, Linux)
pip install foundry-local-sdk-winml  # Windows, binds to Windows ML
```

The SDK requires Python 3.11 or later. This project was built and verified with
`foundry-local-sdk` version 1.2.4 on Python 3.13, on an Apple M4 Mac.

## Execution providers

An execution provider (EP) is the backend that actually runs the model's math — CPU, a
specific GPU stack, or an NPU. The SDK can discover which EPs your machine supports and
download the ones that are missing:

```python
for ep in manager.discover_eps():
    print(ep.name, ep.is_registered)
manager.download_and_register_eps()
```

On the Apple M4 machine used to build this project, only `WebGpuExecutionProvider` was
listed and it was not registered, so inference ran on the CPU. That is a fully supported
configuration — it just sets expectations for speed: a 0.5B model answered in about
1.2 seconds, and larger models take proportionally longer.

## The model catalog

The catalog is the list of models Foundry Local knows how to fetch and run. Each entry has
an **alias** (a short stable name like `phi-3.5-mini`), a concrete **model id** that encodes
the hardware variant (like `Phi-3.5-mini-instruct-generic-gpu:2`), a context length, and a
capability string such as `embedding`, `reasoning` or `tool-calling`.

```python
models = manager.catalog.list_models()
model = manager.catalog.get_model("phi-3.5-mini")
```

When this project was built the catalog held 47 models, including the Phi family, several
generations of Qwen, Mistral, DeepSeek distillations, Whisper speech models, and two
embedding models (`qwen3-embedding-0.6b` and `qwen3-embedding-8b`).

Always list the catalog on your own machine instead of trusting an alias you read in a
tutorial. The catalog changes over time and varies by platform.

## Model lifecycle

Every model goes through the same four steps:

```python
model = manager.catalog.get_model("qwen3-embedding-0.6b")
model.download(lambda pct: print(f"{pct:.1f}%"))  # skipped if already cached
model.load()                                      # weights into memory
client = model.get_chat_client()                  # or get_embedding_client()
model.unload()                                    # free the memory
```

`download()` is idempotent: it returns immediately if the model is already in the local
cache. Downloading is the only step that needs an internet connection, and it is a one-time
setup cost — on the machine used here roughly 290 seconds per model. Loading a cached model
took between 1.6 and 3.3 seconds.

A note on the API shape: `is_cached`, `is_loaded`, `context_length` and `capabilities` are
properties, not methods. Calling `model.is_cached()` raises
`TypeError: 'bool' object is not callable`.

## Choosing a model size

Smaller models load faster and answer faster, but they know less and hallucinate more. When
we tested `qwen2.5-0.5b` with the plain question "what is RAG?", it confidently invented the
expansion "Retributionary Amplification Game". That is exactly the failure mode retrieval
augmentation is meant to fix — but it also shows that a model can be too small to be useful
even with good context.

The rule of thumb: pick the smallest model that still answers your evaluation set
correctly, and measure rather than guess.
