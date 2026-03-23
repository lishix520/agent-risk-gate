# Continuity Kernel

Continuity Kernel is an exploration of memory beyond storage.

Most agent memory systems solve `Layer 1`: persistence, retrieval, summaries, and profile recall. This project focuses on `Layer 2`: how experience becomes reusable structure, how that structure rigidifies, and when it should be rebuilt.

In this view, memory is not just a database attached to intelligence. Memory is part of intelligence itself: a resource-constrained system for compression, reuse, forgetting, and reconstruction.

## Core claim

History existing is not the same as memory existing.

An agent can have transcripts, files, summaries, and vector search, yet still fail in the way humans describe as "it did not remember". The missing layer is not storage. It is structure formation.

This repo studies that missing layer:

- how raw experience becomes a reusable pattern
- how stable patterns become high-level templates
- how templates take over future computation
- why old templates resist updating
- what kind of error should trigger rebuild instead of patching

## What this repo is

- A position on agent memory architecture
- A prototype-oriented implementation package
- A distinction between memory infrastructure and memory formation

## What this repo is not

- Another vector database wrapper
- A user-profile memory system
- A claim that storage and retrieval are unimportant

`Layer 1` still matters. This repo argues that it is not sufficient.

## Read first

- [Position Paper](docs/position-paper.md)
- [Terms and Boundaries](docs/terms.md)
- [Architecture Notes](docs/architecture/architecture.md)
- [Protocol Docs](docs/protocol/reality-first.md)
- [MCP Boundary](docs/protocol/mcp-boundary.md)

## Working model

The current working model is:

```text
Experience Flow
-> Buffer
-> Condition Similarity
-> Compression
-> Pattern
-> Template
-> Router
-> Action / Output
-> Outcome Feedback
-> Updater / Rebuild
```

The implementation package in this repo is still pragmatic and partial. The conceptual layer is ahead of the validated product layer.

## Why publish now

Because the problem is already clear enough to discuss:

- many "memory" projects stop at storage and retrieval
- real agent failure often happens after retrieval
- the hard question is when prior experience should become structure
- the harder question is when that structure should stop being trusted

This repo is published as an engineering research note, not as a finished claim of superiority.
