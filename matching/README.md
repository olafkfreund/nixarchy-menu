# Smart Match runtime

The default is **Voice and text**, using **Small (2M)**. Settings are under
nixarchy-menu Settings > Matching. **Only voice** leaves typed queries on the ordinary
matcher. **Off** terminates the engine, clears pending results and releases the
model. Both models ship with the package and run on CPU; switching to **Large (8M)**
restarts the engine on the other model, with no download. An idle engine also exits
after two minutes and reloads on the next eligible query.

The engine runs outside the shell UI process, under the user's account, and needs
no network access. If it does not start within ten seconds, or stops, lexical search
keeps working and the Matching settings screen shows a Retry Smart Match row.

## Engine

Nix builds and ships everything Smart Match runs; nothing is downloaded or built
at runtime.

- `matching-engine`: `matching/engine`, the Rust source, built by
  `buildRustPackage` from its `Cargo.lock` (serde, serde_json,
  unicode-normalization, unicode_categories). The binary is `keystroke-matching`.
- `model-small` and `model-large`: the three files (`config.json`,
  `tokenizer.json`, `model.safetensors`) of potion-base-2M and potion-base-8M at
  the pinned revisions below, fetched by `fetchurl` against fixed SHA-256 digests.
- `plugin`: when Nix builds the plugin it substitutes the engine and both model
  store paths into `matching/Session.qml`, which runs
  `keystroke-matching --model-dir <model> --model <small|large>` directly. A raw
  checkout that was not built by Nix keeps the `@…@` placeholders, so the engine
  fails to start ("Matching helper stopped") and ordinary search keeps working.

The protocol is unchanged: the engine prints `{"type":"ready"}` once the model is
loaded, then answers each request line with a `result` or an `error`. It exits 2
on bad arguments and 1, after an `error` line, when the model cannot be loaded.

Testing: `nix flake check` runs the `engine` check. By hand, with the Nix outputs:

    python3 tests/matching_engine_check.py \
      --engine "$(nix build --no-link --print-out-paths .#matching-engine)/bin/keystroke-matching" \
      --model-dir "$(nix build --no-link --print-out-paths .#model-small)"

It checks the protocol and startup errors, and token-for-token parity with
Hugging Face `tokenizers` on a synthetic vocabulary and on the real model. Without
the Python `tokenizers` package it prints SKIP for parity instead of failing.

The engine is not a deep-learning framework: a Model2Vec model is one embedding
row per vocabulary token, and a text's vector is the mean of its token rows. The
engine implements the BERT WordPiece tokenizer as `tokenizers` performs it
(BertNormalizer, BertPreTokenizer, greedy WordPiece; `[UNK]` dropped as Model2Vec
does), reads the F32 table from the safetensors file and ranks by cosine.
Measured here: 600 KB binary, ready 18 ms after launch, 16 MiB resident,
a 1,500-document catalog embedded in 5 ms, a query answered in under 0.1 ms.

The engine and models live in the Nix store; model revisions and digests are
fixed in `flake.nix`. Loading is local-only. No query or catalog text is sent to a
remote inference service or saved by the engine, and no code is generated or
evaluated.

A single JSON-lines worker keeps normalized static vectors in memory. Catalog
updates reuse unchanged vectors and evict removed documents. Requests contain
only stable IDs and metadata, not executable actions. Replies contain IDs and
similarity scores. The host filters availability and scope before sending metadata
and maps replies back onto fresh provider rows. Each query/catalog/model has its
own request key; old responses cannot populate a newer query. Only the latest
queued query is kept while a request is in flight. The catalog travels with a
request only when its digest changed.

The host retains exact matching, adds bounded typo recovery and a conditional
Chrome-to-Chromium alias, and then adds semantic suggestions above fallbacks but
below exact hits before applying learned query preferences. It filters negation, command family, volume/brightness direction,
start/stop and contradictory on/off setters. A toggle is still presented as a
**Toggle**: unknown current state is never treated as a guaranteed on/off setter.
Equivalent commands are deduplicated while retaining confirmations. Results never
run automatically. Whole spoken arithmetic is parsed separately using the existing
bounded calculator; ambiguous homophones and ordinary prose are not rewritten.

`descriptions.json` is the frozen GPT-5.6 Terra annotation pass: 618 one-sentence
intent descriptions, produced from installed metadata without access to the test
queries. `description-keys.json` binds the descriptions to their original titles
and fingerprints of action/target definitions. Changed/custom/absent entries fall back to live
metadata. App IDs accept the AppLibrary's optional `.desktop` suffix. Community
providers can supply a live `catalog(ctx)` and their own `intentDescription`.
The shipped map does not create or install its catalog's apps or hotkeys.

The default ~8 MB 2M model has 64-dimensional vectors; the ~31 MB 8M model has
256-dimensional vectors. The engine holds the table as is (16 MiB resident
with 2M). Neither
similarity nor a fixed threshold proves intent; this remains a suggestions system
with explicit selection and existing confirmation rules.

Model2Vec and the POTION models are MIT licensed:
https://github.com/MinishLab/model2vec
https://huggingface.co/minishlab/potion-base-2M
https://huggingface.co/minishlab/potion-base-8M

Model revisions:
- small: `389b9f64be5aa4ae7a6bc6fe95ef20ce485ae5da`
- large: `bf8b056651a2c21b8d2565580b8569da283cab23`
