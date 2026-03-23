# Terms and Boundaries

This document fixes the working meaning of the core terms used in this repo.

The goal is to avoid mixing infrastructure language with formation language.

## Experience

The smallest event unit.

It records what happened under a condition, with an action, an outcome, and a resulting change.

Experience is not memory. It is memory material.

## Experience Flow

The incoming stream of experiences over time.

It is the raw input stream, not long-term memory.

## Buffer

A short-lived window over recent experience flow.

It exists to support compression and local update, not to serve as long-term storage.

## Condition

A structured representation of the context in which an experience occurs.

Condition is not free text. It must be computable.

Its role is to define what counts as "similar enough" for grouping.

## Condition Schema

The explicit definition of which condition features exist and how they are represented.

This is more important than the specific similarity function. If the schema is wrong, the structure built on top of it will also be wrong.

## Similarity

A computable rule for deciding whether two conditions are close enough to belong to the same pattern candidate.

Similarity is not semantic understanding. It is a grouping decision.

## Compression

The process that extracts the smallest predictive structure from repeated or conflicting experiences.

Compression is the core memory-forming process.

Without compression, there is no memory in the structural sense used here.

## Pattern

A compressed middle-layer statistical structure.

A pattern answers:

`Under similar conditions, what usually happens?`

Patterns are not final policies. They remain probabilistic and revisable.

## Template

A promoted pattern with enough support, stability, and usefulness to be directly reused in future computation.

A template answers:

`Under this condition, what should be the default policy now?`

Template is the first layer that directly governs behavior by default.

## Router

The component that decides which level of structure to use for the current input.

Typical priority:

`Template > Pattern > raw recomputation`

Router does not create memory. It allocates the computation path.

## Update Signal

A deviation signal indicating that an old structure may no longer match reality.

It is not update itself. It is the trigger input for update decisions.

## Updater

The component that decides whether to keep, weaken, or rebuild a structure.

Updater is not a patching mechanism. In this framework, meaningful update should usually mean rebuild through new compression.

## Rebuild

The process of sending new experience back through compression so that a new structure replaces the old one.

Rebuild is the preferred response to structural mismatch.

## Rigidity

A system state in which high-level structures dominate routing long enough that update signals stop changing the structure.

Rigidity is not "no computation".

Rigidity is fixed-path computation.

## Stabilization

The process by which a structure becomes self-reinforcing because it keeps producing acceptable results at lower cost than rebuilding.

Stabilization explains why old templates persist.

## Shell

In this repo, `Shell` is not the person or the agent itself.

It refers to a long-lived, self-reinforcing cluster of high-level templates that filters future input and protects its own continuity.

It is a special rigidified state, not a primitive module.

## Good / Bad

These are not core computational primitives.

They are semantic labels applied after repeated outcomes and resource effects have already been compressed into structure.

## Should

`Should` is not a fundamental variable in this system.

It is a surface-language expression of a high-confidence action bias inside a template.

## Two-layer distinction

This repo uses a strict distinction:

- `Layer 1`: memory infrastructure
- `Layer 2`: memory formation

Layer 1 is about making history available.
Layer 2 is about making history become reusable structure.

The project is centered on Layer 2.
