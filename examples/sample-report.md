# Claude Code Usage Analysis Report

**Analysis Period:** 2025-09-09 to 2025-10-09 (31 days)
**Report Generated:** 2025-10-09 21:08:50

## Executive Summary

- **Total Cost:** $989.90
- **Total Tokens:** 1,126,304,159
- **Total Input Tokens:** 178,304
- **Total Output Tokens:** 1,243,028
- **Cache Creation Tokens:** 81,262,860
- **Cache Read Tokens:** 1,043,619,967
- **Overall Cache Efficiency:** 92.66%

## Model Usage Patterns

**Model Combinations Used:**

- **opus-4-1 + sonnet-4**: 20 days
- **sonnet-4 + sonnet-4-5**: 5 days
- **sonnet-4-5**: 5 days
- **sonnet-4**: 1 days

## Daily Cost Analysis

### Total Daily Cost

| Metric | Mean | Median | P95 | Min | Max |
|--------|------|--------|-----|-----|-----|
| **Total Cost** | $31.93 | $29.54 | $65.15 | $1.14 | $75.29 |

### Daily Cost Breakdown by Token Type

| Token Type | Mean | Median | P95 | Total | % of Total |
|------------|------|--------|-----|-------|------------|
| **Input Tokens** | $0.02 | $0.01 | $0.09 | $0.60 | 0.06% |
| **Output Tokens** | $0.98 | $0.81 | $2.54 | $30.42 | 3.07% |
| **Cache Creation** | $15.00 | $13.19 | $26.44 | $465.06 | 46.98% |
| **Cache Read** | $15.93 | $12.16 | $36.06 | $493.83 | 49.89% |

## Daily Token Usage Statistics

| Token Type | Mean | Median | P95 | Min | Max |
|------------|------|--------|-----|-----|-----|
| **Input Tokens** | 5,751 | 1,382 | 30,315 | 150 | 32,101 |
| **Output Tokens** | 40,097 | 24,119 | 101,381 | 671 | 155,491 |
| **Cache Creation** | 2,621,382 | 2,525,177 | 4,850,357 | 65,333 | 4,889,013 |
| **Cache Read** | 33,665,160 | 30,549,742 | 67,909,864 | 139,109 | 99,625,038 |
| **Total Tokens** | 36,332,392 | 32,582,596 | 72,665,530 | 205,894 | 103,829,819 |

## Cache Efficiency Analysis

**Cache efficiency** is calculated as: `(Cache Read Tokens / Total Tokens) × 100`

Higher percentages indicate better cache utilization, meaning:
- Fewer tokens need to be processed from scratch
- Lower costs per request (cache reads cost ~10-20x less than new tokens)
- Faster response times

| Metric | Mean | Median | P95 | Min | Max |
|--------|------|--------|-----|-----|-----|
| **Cache Efficiency** | 90.18% | 92.05% | 95.59% | 60.71% | 95.95% |

## Model-Specific Analysis

### opus-4-1

**Days Used:** 20
**Cache Efficiency:** 93.26%

**Pricing (per million tokens):**
- Input: $15.00
- Output: $75.00
- Cache Creation: $18.75
- Cache Read: $1.50

#### Cost Breakdown by Token Type

| Cost Type | Mean | Median | P95 | Total | % of Model Cost |
|-----------|------|--------|-----|-------|-----------------|
| **Input Tokens** | $0.00 | $0.00 | $0.01 | $0.08 | 0.02% |
| **Output Tokens** | $0.74 | $0.72 | $1.40 | $14.72 | 3.34% |
| **Cache Creation** | $10.02 | $9.23 | $17.95 | $200.40 | 45.43% |
| **Cache Read** | $11.30 | $12.09 | $21.47 | $225.92 | 51.22% |
| **TOTAL** | $22.06 | $24.00 | $37.88 | $441.13 | 100.00% |

#### Token Statistics

| Token Type | Mean | Median | P95 | Total |
|------------|------|--------|-----|-------|
| **Input** | 268 | 267 | 466 | 5,363 |
| **Output** | 9,812 | 9,635 | 18,642 | 196,242 |
| **Cache Create** | 534,412 | 492,291 | 957,542 | 10,688,249 |
| **Cache Read** | 7,530,807 | 8,058,841 | 14,315,724 | 150,616,154 |
| **Total** | 8,075,300 | 8,625,333 | 14,941,489 | 161,506,008 |

### sonnet-4

**Days Used:** 26
**Cache Efficiency:** 93.51%

**Pricing (per million tokens):**
- Input: $3.00
- Output: $15.00
- Cache Creation: $3.75
- Cache Read: $0.30

#### Cost Breakdown by Token Type

| Cost Type | Mean | Median | P95 | Total | % of Model Cost |
|-----------|------|--------|-----|-------|-----------------|
| **Input Tokens** | $0.01 | $0.00 | $0.05 | $0.21 | 0.05% |
| **Output Tokens** | $0.58 | $0.45 | $1.56 | $15.19 | 3.77% |
| **Cache Creation** | $6.83 | $6.03 | $15.74 | $177.64 | 44.13% |
| **Cache Read** | $8.06 | $7.24 | $18.43 | $209.47 | 52.04% |
| **TOTAL** | $15.48 | $14.63 | $34.35 | $402.52 | 100.00% |

#### Token Statistics

| Token Type | Mean | Median | P95 | Total |
|------------|------|--------|-----|-------|
| **Input** | 2,734 | 943 | 16,484 | 71,106 |
| **Output** | 38,951 | 30,277 | 104,019 | 1,012,736 |
| **Cache Create** | 1,821,968 | 1,608,737 | 4,197,573 | 47,371,180 |
| **Cache Read** | 26,855,323 | 24,141,513 | 61,440,682 | 698,238,405 |
| **Total** | 28,718,977 | 25,977,821 | 65,496,008 | 746,693,427 |

### sonnet-4-5

**Days Used:** 10
**Cache Efficiency:** 89.30%

**Pricing (per million tokens):**
- Input: $3.00
- Output: $15.00
- Cache Creation: $3.75
- Cache Read: $0.30

#### Cost Breakdown by Token Type

| Cost Type | Mean | Median | P95 | Total | % of Model Cost |
|-----------|------|--------|-----|-------|-----------------|
| **Input Tokens** | $0.03 | $0.03 | $0.07 | $0.31 | 0.21% |
| **Output Tokens** | $0.05 | $0.05 | $0.12 | $0.51 | 0.35% |
| **Cache Creation** | $8.70 | $8.04 | $15.21 | $87.01 | 59.49% |
| **Cache Read** | $5.84 | $5.22 | $12.44 | $58.43 | 39.95% |
| **TOTAL** | $14.63 | $12.61 | $27.68 | $146.26 | 100.00% |

#### Token Statistics

| Token Type | Mean | Median | P95 | Total |
|------------|------|--------|-----|-------|
| **Input** | 10,183 | 10,064 | 22,411 | 101,835 |
| **Output** | 3,405 | 3,050 | 7,868 | 34,050 |
| **Cache Create** | 2,320,343 | 2,145,119 | 4,056,837 | 23,203,431 |
| **Cache Read** | 19,476,540 | 17,409,218 | 41,471,662 | 194,765,408 |
| **Total** | 21,810,472 | 19,273,762 | 45,386,523 | 218,104,724 |

## Key Insights

1. **Daily Cost Composition:** Your average daily cost of $31.93 breaks down as:
   - Input tokens: $0.02 (0.06%)
   - Output tokens: $0.98 (3.07%)
   - Cache creation: $15.00 (46.98%)
   - Cache reads: $15.93 (49.89%)

2. **Cost Variability:** With a P95 of $65.15, your highest usage days cost approximately 2.0x the average.

3. **Cache Utilization:** Your average cache efficiency of 90.18% is excellent, significantly reducing processing costs.

4. **Primary Model:** opus-4-1 accounts for $441.13 (44.56%) of total costs.

5. **Monthly Projection:** Based on average daily cost, projected monthly cost is approximately $957.97.
