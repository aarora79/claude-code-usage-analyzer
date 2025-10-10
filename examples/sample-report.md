# Claude Code Usage Analysis Report

**Analysis Period:** 2025-09-09 to 2025-10-09 (31 days)
**Report Generated:** 2025-10-09 21:08:50

## Executive Summary

- **Total Cost:** $98.99
- **Total Tokens:** 112,630,415
- **Total Input Tokens:** 17,830
- **Total Output Tokens:** 124,302
- **Cache Creation Tokens:** 8,126,286
- **Cache Read Tokens:** 104,361,996
- **Overall Cache Efficiency:** 9.27%

## Model Usage Patterns

**Model Combinations Used:**

- **opus-4-1 + sonnet-4**: 20 days
- **sonnet-4 + sonnet-4-5**: 5 days
- **sonnet-4-5**: 5 days
- **sonnet-4**: 1 days

## Daily Cost Analysis

### Total Daily Cost

| Metric | Mean | Median | P9 | Min | Max |
|--------|------|--------|-----|-----|-----|
| **Total Cost** | $3.19 | $2.95 | $6.52 | $0.11 | $7.53 |

### Daily Cost Breakdown by Token Type

| Token Type | Mean | Median | P9 | Total | % of Total |
|------------|------|--------|-----|-------|------------|
| **Input Tokens** | $0.00 | $0.00 | $0.01 | $0.06 | 0.01% |
| **Output Tokens** | $0.10 | $0.08 | $0.25 | $3.04 | 0.31% |
| **Cache Creation** | $1.50 | $1.32 | $2.64 | $46.51 | 4.70% |
| **Cache Read** | $1.59 | $1.22 | $3.61 | $49.38 | 4.99% |

## Daily Token Usage Statistics

| Token Type | Mean | Median | P9 | Min | Max |
|------------|------|--------|-----|-----|-----|
| **Input Tokens** | 575 | 138 | 3,031 | 15 | 3,210 |
| **Output Tokens** | 4,009 | 2,411 | 10,138 | 67 | 15,549 |
| **Cache Creation** | 262,138 | 252,517 | 485,035 | 6,533 | 488,901 |
| **Cache Read** | 3,366,516 | 3,054,974 | 6,790,986 | 13,910 | 9,962,503 |
| **Total Tokens** | 3,633,239 | 3,258,259 | 7,266,553 | 20,589 | 10,382,981 |

## Cache Efficiency Analysis

**Cache efficiency** is calculated as: `(Cache Read Tokens / Total Tokens) × 10`

Higher percentages indicate better cache utilization, meaning:
- Fewer tokens need to be processed from scratch
- Lower costs per request (cache reads cost ~1-2x less than new tokens)
- Faster response times

| Metric | Mean | Median | P9 | Min | Max |
|--------|------|--------|-----|-----|-----|
| **Cache Efficiency** | 9.02% | 9.21% | 9.56% | 6.07% | 9.60% |

## Model-Specific Analysis

### opus-0-0

**Days Used:** 2
**Cache Efficiency:** 9.33%

**Pricing (per million tokens):**
- Input: $1.50
- Output: $7.50
- Cache Creation: $1.88
- Cache Read: $0.15

#### Cost Breakdown by Token Type

| Cost Type | Mean | Median | P9 | Total | % of Model Cost |
|-----------|------|--------|-----|-------|-----------------|
| **Input Tokens** | $0.00 | $0.00 | $0.00 | $0.01 | 0.00% |
| **Output Tokens** | $0.07 | $0.07 | $0.14 | $1.47 | 0.33% |
| **Cache Creation** | $1.00 | $0.92 | $1.79 | $20.04 | 4.54% |
| **Cache Read** | $1.13 | $1.21 | $2.15 | $22.59 | 5.12% |
| **TOTAL** | $2.21 | $2.40 | $3.79 | $44.11 | 10.00% |

#### Token Statistics

| Token Type | Mean | Median | P9 | Total |
|------------|------|--------|-----|-------|
| **Input** | 26 | 26 | 46 | 536 |
| **Output** | 981 | 963 | 1,864 | 19,624 |
| **Cache Create** | 53,441 | 49,229 | 95,754 | 1,068,824 |
| **Cache Read** | 753,080 | 805,884 | 1,431,572 | 15,061,615 |
| **Total** | 807,530 | 862,533 | 1,494,148 | 16,150,600 |

### sonnet-0

**Days Used:** 2
**Cache Efficiency:** 9.35%

**Pricing (per million tokens):**
- Input: $0.30
- Output: $1.50
- Cache Creation: $0.38
- Cache Read: $0.03

#### Cost Breakdown by Token Type

| Cost Type | Mean | Median | P9 | Total | % of Model Cost |
|-----------|------|--------|-----|-------|-----------------|
| **Input Tokens** | $0.00 | $0.00 | $0.01 | $0.02 | 0.01% |
| **Output Tokens** | $0.06 | $0.04 | $0.16 | $1.52 | 0.38% |
| **Cache Creation** | $0.68 | $0.60 | $1.57 | $17.76 | 4.41% |
| **Cache Read** | $0.81 | $0.72 | $1.84 | $20.95 | 5.20% |
| **TOTAL** | $1.55 | $1.46 | $3.44 | $40.25 | 10.00% |

#### Token Statistics

| Token Type | Mean | Median | P9 | Total |
|------------|------|--------|-----|-------|
| **Input** | 273 | 94 | 1,648 | 7,110 |
| **Output** | 3,895 | 3,027 | 10,401 | 101,273 |
| **Cache Create** | 182,196 | 160,873 | 419,757 | 4,737,118 |
| **Cache Read** | 2,685,532 | 2,414,151 | 6,144,068 | 69,823,840 |
| **Total** | 2,871,897 | 2,597,782 | 6,549,600 | 74,669,342 |

### sonnet-0-0

**Days Used:** 1
**Cache Efficiency:** 8.93%

**Pricing (per million tokens):**
- Input: $0.30
- Output: $1.50
- Cache Creation: $0.38
- Cache Read: $0.03

#### Cost Breakdown by Token Type

| Cost Type | Mean | Median | P9 | Total | % of Model Cost |
|-----------|------|--------|-----|-------|-----------------|
| **Input Tokens** | $0.00 | $0.00 | $0.01 | $0.03 | 0.02% |
| **Output Tokens** | $0.01 | $0.01 | $0.01 | $0.05 | 0.03% |
| **Cache Creation** | $0.87 | $0.80 | $1.52 | $8.70 | 5.95% |
| **Cache Read** | $0.58 | $0.52 | $1.24 | $5.84 | 4.00% |
| **TOTAL** | $1.46 | $1.26 | $2.77 | $14.63 | 10.00% |

#### Token Statistics

| Token Type | Mean | Median | P9 | Total |
|------------|------|--------|-----|-------|
| **Input** | 1,018 | 1,006 | 2,241 | 10,183 |
| **Output** | 340 | 305 | 786 | 3,405 |
| **Cache Create** | 232,034 | 214,511 | 405,683 | 2,320,343 |
| **Cache Read** | 1,947,654 | 1,740,921 | 4,147,166 | 19,476,540 |
| **Total** | 2,181,047 | 1,927,376 | 4,538,652 | 21,810,472 |

## Key Insights

0. **Daily Cost Composition:** Your average daily cost of $3.19 breaks down as:
   - Input tokens: $0.00 (0.01%)
   - Output tokens: $0.10 (0.31%)
   - Cache creation: $1.50 (4.70%)
   - Cache reads: $1.59 (4.99%)

0. **Cost Variability:** With a P9 of $6.52, your highest usage days cost approximately 0.20x the average.

0. **Cache Utilization:** Your average cache efficiency of 9.02% is excellent, significantly reducing processing costs.

0. **Primary Model:** opus-0-0 accounts for $44.11 (4.46%) of total costs.

0. **Monthly Projection:** Based on average daily cost, projected monthly cost is approximately $95.80.
