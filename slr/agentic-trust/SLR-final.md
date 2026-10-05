# SLR: Trust & Orchestration in Agentic / Multi-Agent Systems

Proyek: `slr/agentic-trust/` · 321 paper IEEE (2021–2026, open access, journals) → 22 included.
File sumber: `protocol.json`, `decisions.csv`, `extraction.csv`, `gaps.md`, `prisma.svg`.

## 1. Protokol

**RQ1:** Metode orkestrasi/koordinasi apa yang dipakai pada agentic/multi-agent system?
**RQ2:** Bagaimana trust/confidence dikalibrasi dan diukur antar agen?
**RQ3:** Bagaimana konflik, cost, latency, dan governance/policy enforcement ditangani?

**Inklusi:** jurnal 2021–2026, open access, bahas agentic/multi-agent DAN orchestration/coordination DAN trust/governance/confidence.
**Eksklusi:** non-Inggris, non-jurnal, tanpa evaluasi/metode jelas.
**QA:** (qa1) metode orkestrasi jelas & replicable, bobot 1; (qa2) evaluasi empiris, bobot 2; (qa3) trust diukur eksplisit, bobot 2. Skor maks 5.

## 2. Alir PRISMA

| Tahap | n |
|---|---|
| Identified (IEEE) | 321 |
| Excluded title/abstract | 281 |
| Full-text assessed | 40 |
| Excluded full-text: trust/governance tak dibahas | 16 |
| Excluded full-text: di luar fokus RQ | 2 |
| **Included** | **22** |

## 3. Studi included (22)

| # | Paper | QA | Temuan kunci |
|---|---|---|---|
| 1 | Secure Trust Method, smart grid blockchain (2021) | 5 | T3FT repeated game + proof-of-cooperation consensus; trust via distorsi/konsistensi/reliabilitas evaluator |
| 2 | Consensus-Based Distributed Connectivity Control (2022) | 5 | Konsensus berbasis trust estimasi nilai Fiedler; trust = kualitas link komunikasi; adaptasi topologi |
| 3 | Trust Fair Resource Allocation, community energy (2024) | 5 | Negosiasi + protokol komunikasi; trust = reliabilitas vs aturan komunitas |
| 4 | One-to-Many Concurrent Composite Negotiations, P2P energy (2025) | 3 | Negosiasi konkuren multistage; trust dari riwayat transaksi postpaid |
| 5 | Physics-Informed MARL, supply chain (2025) | 5 | Lagrangian duality, update multiplier desentral; trust via CVaR distributional value |
| 6 | Self-Triggered DNMPC + ADMM, cooperative MAS (2025) | 5 | Threshold komunikasi adaptif; kurangi transmisi; recursive feasibility |
| 7 | **Orchestrator-Agent Trust**, visual classification (2026) | 5 | Orkestrasi trust-aware: confidence + justifikasi NL; metrik ECE/OCR/CG; re-evaluation loop RAG |
| 8 | Virtual Trust Bubbles, V2V airspace blockchain (2026) | 5 | 5-layer + smart contract + BFT; quantum optimization real-time |
| 9 | Beyond Connectivity, AI agents edge (2026) | 5 | Trust & Governance Levels: deployability terpisah dari kompetensi agentic |
| 10 | Beyond Single-Framework: CrewAI+AutoGen+LangChain (2026) | 5 | Hierarki delegasi + koordinasi konversasional + rantai; kompetensi perilaku terstandar |
| 11 | CAMAC-DRA, EV charging GNN+DRL (2026) | 5 | GNN + DRL context-aware; bobot stakeholder dinamis via attention |
| 12 | Digital Twin cross-layer, 6G drone MARL (2026) | 5 | MARL + model probabilistik; recovery sub-detik; hirarki operasional-taktis-strategis |
| 13 | OMARF, offshore wind resilience (2026) | 5 | Agen self-healing/self-defense lintas control-data-knowledge plane; trust dari kontribusi operasional |
| 14 | Hybrid RL-Blockchain, decentralised coordination (2026) | 5 | DApps + smart contract + ROS middleware; latensi blockchain ~45,7 dtk masih OK untuk supervisi |
| 15 | Ask-type communication, POMDP trade-off (2026) | 5 | Minta info tim hanya bila perlu; trust = value of communication vs cost; async |
| 16 | A2A+MCP, construction lifecycle (2026) | 0 | Messaging schema-validated; tanpa evaluasi empiris terdeteksi |
| 17 | LLM Societies CGS, emergent coordination (2026) | 5 | Fermi social learning + trust-weighted advisory (Solver–Critic–Aggregator) |
| 18 | AE-MAPPO, 6G O-RAN slicing (2026) | 0 | Centralized-training decentralized-execution + attention; tanpa evaluasi terdeteksi |
| 19 | 6G Needs Agents, agentic AI-native networks (2026) | 5 | Semantic control plane + policy-governed reasoning; device-edge-core continuum |
| 20 | Agentic-Defined Networking ADN (2026) | 5 | Orkestrasi desentral tanpa controller pusat; belief update dari observasi lokal |
| 21 | IRAIVI, hate-speech detection + counter-speech (2026) | 0 | Confidence threshold + eskalasi manusia; tanpa evaluasi terdeteksi |
| 22 | LAC-DSA, 6G decision support fuzzy CRITIC-TOPSIS (2026) | 3 | MCP + A2A + FRAM/FMEA untuk policy enforcement |

Catatan: 3 paper skor QA 0 (no. 16, 18, 21) — ekstraksi tak temukan evaluasi empiris; pertimbangkan eksklusi manual sebelum sitasi.

## 4. Sintesis per RQ

**RQ1 — metode orkestrasi.** Spektrum sentralisasi: (a) orchestrator pusat trust-aware (#7: ECE/OCR/CG + RAG loop); (b) hibrida framework (#10: CrewAI/AutoGen/LangChain; #22: MCP/A2A); (c) desentral penuh (#20 ADN; #5 Lagrangian duality; #14 blockchain). Tren 2026: LLM-agent + protokol interoperabilitas (MCP, A2A).

**RQ2 — kalibrasi trust.** Tiga keluarga pengukuran: metrik kalibrasi modern (ECE/OCR/CG, #7); reputasi berbasis interaksi (riwayat transaksi #4, kontribusi operasional #13); trust struktural (kualitas link #2, smart contract/BFT #8). Dinamis & kontekstual, bukan skor statis.

**RQ3 — konflik/cost/latency/governance.** Pola berulang: kurangi komunikasi (self-triggered #6, ask-type #15), verifikasi desentral (#8, #14; trade-off latensi blockchain), policy embedded di framework (#22 FRAM/FMEA, #9 Trust & Governance Levels).

## 5. Research gaps → kandidat RQ baru

| Gap | Bukti | Kandidat RQ |
|---|---|---|
| Orkestrasi hibrida lintas konteks minim | #10 | Arsitektur terintegrasi multifaset untuk MAS kompleks? |
| Trust dinamis adaptif konteks | #4 | Trust beradaptasi seiring perubahan interaksi? |
| Integrasi protokol untuk konflik+cost | #3 | Integrasi protokol tingkatkan efisiensi biaya/konflik? |
| Policy enforcement terintegrasi koordinasi | #12 | Kebijakan adaptif di lingkungan MAS dinamis? |

**Kontradiksi:** proof-of-cooperation (#1) vs trust-based consensus (#2) — belum ada perbandingan head-to-head. **Topik jenuh:** pengukuran trust generik; diferensiasi ada di integrasi + skenario real-world.
