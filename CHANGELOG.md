# Changelog

## [0.3.0](https://github.com/glassflow/glassflow-python/compare/v0.2.0...v0.3.0) (2026-07-05)


### ⚠ BREAKING CHANGES

* Generation.set_model() is now set_response_model(); Generation.set_finish_reason() is now set_finish_reasons().

### Features

* bundled auto-instrumentation via OpenInference ([6945ab1](https://github.com/glassflow/glassflow-python/commit/6945ab13bead44f61d765273e23d9ce26513d6e2))
* pre-1.0 API cleanups from the SDK review ([a294b94](https://github.com/glassflow/glassflow-python/commit/a294b945a01c68da3f918a5e9721b5d67a27433c))


### Bug Fixes

* crash-proofing and semconv corrections ([dd06b18](https://github.com/glassflow/glassflow-python/commit/dd06b187b2396e2648dc60b690f4c6c1367b72bb))
* define init() lifecycle semantics ([4374298](https://github.com/glassflow/glassflow-python/commit/4374298615b5b08920a2b3bda96f4bdd27d760c9))
* emit gen_ai.*.messages in the spec role/parts shape ([a7225d0](https://github.com/glassflow/glassflow-python/commit/a7225d0987c5e63e645b7f5d0f074bb1a42ffd46))
* harden export-stage masking ([9781380](https://github.com/glassflow/glassflow-python/commit/9781380d68936a43b91db45403511d5b2fceeeb7))

## [0.2.0](https://github.com/glassflow/glassflow-python/compare/v0.1.0...v0.2.0) (2026-07-03)


### ⚠ BREAKING CHANGES

* start_generation/start_as_current_generation param 'system' is now 'provider', and the emitted attribute is gen_ai.provider.name (was gen_ai.system).

### Features

* emit gen_ai.provider.name; rename generation param system -&gt; provider ([f30ea71](https://github.com/glassflow/glassflow-python/commit/f30ea71674fe4d2797e9ab5d5842e393b40054c0))
* harden export pipeline reliability ([0934973](https://github.com/glassflow/glassflow-python/commit/093497379eaed0ae0b0d56c9653efc1f37438ed1))
* head-based sampling via sample_rate ([67d4fd1](https://github.com/glassflow/glassflow-python/commit/67d4fd1ea00950645866e391f3c38c6dcbf9cb8b))
* PII masking and content opt-out at export ([2c3b4b0](https://github.com/glassflow/glassflow-python/commit/2c3b4b054bb78e2bc1757e55b944ee8e636aa418))

## [0.1.0](https://github.com/glassflow/glassflow-python/compare/v0.0.1...v0.1.0) (2026-07-02)


### Features

* add `@observe` decorator for tracing user functions ([4e0ba4d](https://github.com/glassflow/glassflow-python/commit/4e0ba4d1013bb527df655012010fcd7accf65004))
* add span-kind model (semconv) and kind param to `@observe` ([e1305d8](https://github.com/glassflow/glassflow-python/commit/e1305d8c05ca03b56975a67645a9c6f004c5a339))
* add start_generation LLM capture helper (gen_ai-native) ([415b168](https://github.com/glassflow/glassflow-python/commit/415b1685403ff2fa6bc4450fe0242e6cd0f5c9a8))
* add start_span manual span API + Observation handle ([70835f8](https://github.com/glassflow/glassflow-python/commit/70835f890ba2e48de22af99b393a9269d27cec1b))
* align span API naming + add manual create/update/end lifecycle ([17e8f31](https://github.com/glassflow/glassflow-python/commit/17e8f31e634963f97c53e2be1fed84d434e85b15))
