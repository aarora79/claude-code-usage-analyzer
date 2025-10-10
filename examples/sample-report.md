# Claude Code Usage Analysis Report

**Analysis Period:** 2025-09-10 to 2025-10-10 (31 days)
**Report Generated:** 2025-10-10 00:46:15

## Executive Summary

- **Total Cost:** $98.26
- **Total Tokens:** 112,150,494
- **Total Input Tokens:** 17,884
- **Total Output Tokens:** 122,907
- **Cache Creation Tokens:** 8,234,895
- **Cache Read Tokens:** 103,774,807
- **Overall Cache Efficiency:** 9.25%

### Estimated Usage Per Minute (0-hour workday)

- **Mean Usage:** On an average day, you process 7,536 tokens per minute at a cost of $0.01 per minute. This means your daily spend is $3.17 for 3,617,757 total tokens.
  - This is composed of 1 input tokens, 8 output tokens, 553 cache creation tokens, and 6,974 cache read tokens per minute.
- **Median Usage:** On a typical day, you process 6,788 tokens per minute at a cost of $0.01 per minute. This means your daily spend is $2.95 for 3,258,259 total tokens.
  - This is composed of 0 input tokens, 5 output tokens, 562 cache creation tokens, and 6,364 cache read tokens per minute.
- **P9 Usage:** On your busiest days (9th percentile), you process 15,138 tokens per minute at a cost of $0.01 per minute. This means your daily spend is $6.52 for 7,266,553 total tokens.
  - This is composed of 6 input tokens, 21 output tokens, 1,010 cache creation tokens, and 14,147 cache read tokens per minute.

## Model Usage Patterns

**Model Combinations Used:**

- **opus-4-1 + sonnet-4**: 19 days
- **sonnet-4-5**: 6 days
- **sonnet-4 + sonnet-4-5**: 5 days
- **sonnet-4**: 1 days

## Daily Cost Analysis

### Total Daily Cost

| Metric | Mean | Median | P9 | Min | Max |
|--------|------|--------|-----|-----|-----|
| **Total Cost** | $3.17 | $2.95 | $6.52 | $0.11 | $7.53 |

### Daily Cost Breakdown by Token Type

| Token Type | Mean | Median | P9 | Total | % of Total |
|------------|------|--------|-----|-------|------------|
| **Input Tokens** | $0.00 | $0.00 | $0.01 | $0.06 | 0.01% |
| **Output Tokens** | $0.10 | $0.08 | $0.25 | $2.98 | 0.30% |
| **Cache Creation** | $1.50 | $1.35 | $2.64 | $46.39 | 4.72% |
| **Cache Read** | $1.57 | $1.22 | $3.61 | $48.84 | 4.97% |

## Daily Token Usage Statistics

| Token Type | Mean | Median | P9 | Min | Max |
|------------|------|--------|-----|-----|-----|
| **Input Tokens** | 576 | 138 | 3,031 | 12 | 3,210 |
| **Output Tokens** | 3,964 | 2,411 | 10,138 | 25 | 15,549 |
| **Cache Creation** | 265,641 | 269,994 | 485,035 | 6,533 | 488,901 |
| **Cache Read** | 3,347,574 | 3,054,974 | 6,790,986 | 13,910 | 9,962,503 |
| **Total Tokens** | 3,617,757 | 3,258,259 | 7,266,553 | 20,589 | 10,382,981 |

## Cache Efficiency Analysis

**Cache efficiency** is calculated as: `(Cache Read Tokens / Total Tokens) × 10`

Higher percentages indicate better cache utilization, meaning:
- Fewer tokens need to be processed from scratch
- Lower costs per request (cache reads cost ~1-2x less than new tokens)
- Faster response times

| Metric | Mean | Median | P9 | Min | Max |
|--------|------|--------|-----|-----|-----|
| **Cache Efficiency** | 9.01% | 9.14% | 9.56% | 6.76% | 9.60% |

## Model-Specific Analysis

### opus-0-0

**Days Used:** 1
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
| **Output Tokens** | $0.07 | $0.07 | $0.14 | $1.42 | 0.33% |
| **Cache Creation** | $1.02 | $0.94 | $1.86 | $19.38 | 4.51% |
| **Cache Read** | $1.17 | $1.25 | $2.18 | $22.13 | 5.15% |
| **TOTAL** | $2.26 | $2.51 | $3.82 | $42.94 | 10.00% |

#### Token Statistics

| Token Type | Mean | Median | P9 | Total |
|------------|------|--------|-----|-------|
| **Input** | 27 | 26 | 47 | 521 |
| **Output** | 993 | 970 | 1,891 | 18,882 |
| **Cache Create** | 54,409 | 50,196 | 99,257 | 1,033,780 |
| **Cache Read** | 776,641 | 834,652 | 1,454,563 | 14,756,187 |
| **Total** | 832,072 | 898,951 | 1,516,137 | 15,809,371 |

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
| **Output Tokens** | $0.06 | $0.05 | $0.16 | $1.51 | 0.38% |
| **Cache Creation** | $0.70 | $0.65 | $1.58 | $17.50 | 4.43% |
| **Cache Read** | $0.82 | $0.77 | $1.86 | $20.52 | 5.19% |
| **TOTAL** | $1.58 | $1.60 | $3.45 | $39.55 | 10.00% |

#### Token Statistics

| Token Type | Mean | Median | P9 | Total |
|------------|------|--------|-----|-------|
| **Input** | 282 | 94 | 1,730 | 7,060 |
| **Output** | 4,012 | 3,089 | 10,523 | 100,303 |
| **Cache Create** | 186,675 | 173,469 | 422,052 | 4,666,875 |
| **Cache Read** | 2,735,800 | 2,550,444 | 6,215,837 | 68,395,002 |
| **Total** | 2,926,769 | 2,763,419 | 6,619,184 | 73,169,241 |

### sonnet-0-0

**Days Used:** 1
**Cache Efficiency:** 8.90%

**Pricing (per million tokens):**
- Input: $0.30
- Output: $1.50
- Cache Creation: $0.38
- Cache Read: $0.03

#### Cost Breakdown by Token Type

| Cost Type | Mean | Median | P9 | Total | % of Model Cost |
|-----------|------|--------|-----|-------|-----------------|
| **Input Tokens** | $0.00 | $0.00 | $0.01 | $0.03 | 0.02% |
| **Output Tokens** | $0.01 | $0.01 | $0.01 | $0.06 | 0.03% |
| **Cache Creation** | $0.86 | $0.81 | $1.61 | $9.50 | 6.02% |
| **Cache Read** | $0.56 | $0.51 | $1.24 | $6.19 | 3.92% |
| **TOTAL** | $1.43 | $1.35 | $2.74 | $15.78 | 10.00% |

#### Token Statistics

| Token Type | Mean | Median | P9 | Total |
|------------|------|--------|-----|-------|
| **Input** | 936 | 918 | 2,215 | 10,302 |
| **Output** | 338 | 358 | 768 | 3,721 |
| **Cache Create** | 230,385 | 216,728 | 428,519 | 2,534,239 |
| **Cache Read** | 1,874,874 | 1,705,397 | 4,135,899 | 20,623,617 |
| **Total** | 2,106,534 | 1,860,544 | 4,535,082 | 23,171,881 |

## Key Insights

0. **Daily Cost Composition:** Your average daily cost of $3.17 breaks down as:
   - Input tokens: $0.00 (0.01%)
   - Output tokens: $0.10 (0.30%)
   - Cache creation: $1.50 (4.72%)
   - Cache reads: $1.57 (4.97%)

0. **Cost Variability:** With a P9 of $6.52, your highest usage days cost approximately 0.21x the average.

0. **Cache Utilization:** Your average cache efficiency of 9.01% is excellent, significantly reducing processing costs.

0. **Primary Model:** opus-0-0 accounts for $42.94 (4.37%) of total costs.

0. **Monthly Projection:** Based on average daily cost, projected monthly cost is approximately $95.09.
