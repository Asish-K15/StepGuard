# StepGuard Gate C Blind Evaluation Study: N=37 Held-Out Assessment Sheet

> [!IMPORTANT]
> **UNANNOTATED PROTOCOL MATERIAL — NOT SEMANTIC GROUND TRUTH**
> This evaluation sheet is strictly blinded and unannotated.
> All mutation-derived labels, heuristic rationales, PRM predictions, detection outcomes,
> confidence scores, and feature extractors have been withheld to guarantee evaluator independence.
> Do not consult external mutation result logs, verifier labels, or training splits during annotation.

## Evaluator Instructions
For each of the 37 held-out evaluation samples below:
1. Read the **Problem Specification** and the provided **Test Suite Assertions**.
2. Review the **Complete Candidate Solution** and identify the highlighted **Target Step** (indicated with `>>`).
3. Evaluate the step's correctness and semantic soundness in the context of the program:
   - **`CORRECT`**: The step represents a mathematically and semantically sound, valid intermediate or terminal operation towards fulfilling the specification.
   - **`UNCERTAIN`**: The step contains flawed logic, ineffective or redundant conditions, unverified edge case handling, or semantic ambiguity arising from an under-constrained test suite.
4. Record your **Human / Evaluator Label** (`CORRECT` or `UNCERTAIN`) and your **Rationale / Evidence**.

---

## Sample ID: SG-GATE-C-001

### 1. Problem Context
- **Problem Task ID**: `eval_001` (MBPP Task 120)
- **Prompt / Specification**:
  > Write a function to find the maximum absolute product between numbers in pairs of tuples within a given list.
- **Available Test Assertions**:
  ```python
  assert max_product_tuple([(2, 7), (2, 6), (1, 8), (4, 9)] )==36
assert max_product_tuple([(10,20), (15,2), (5,10)] )==200
assert max_product_tuple([(11,44), (10,15), (20,5), (12, 9)] )==484
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Line 2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def max_product_tuple(lst):
>> 2 |     return max(abs(a * b) for a, b in lst)
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-002

### 1. Problem Context
- **Problem Task ID**: `eval_001` (MBPP Task 120)
- **Prompt / Specification**:
  > Write a function to find the maximum absolute product between numbers in pairs of tuples within a given list.
- **Available Test Assertions**:
  ```python
  assert max_product_tuple([(2, 7), (2, 6), (1, 8), (4, 9)] )==36
assert max_product_tuple([(10,20), (15,2), (5,10)] )==200
assert max_product_tuple([(11,44), (10,15), (20,5), (12, 9)] )==484
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Line 2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def max_product_tuple(lst):
>> 2 |     return max(abs(a * b) for a, b in lst)
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-003

### 1. Problem Context
- **Problem Task ID**: `eval_002` (MBPP Task 127)
- **Prompt / Specification**:
  > Write a function to multiply two integers.
- **Available Test Assertions**:
  ```python
  assert multiply_int(10,20)==200
assert multiply_int(5,10)==50
assert multiply_int(4,8)==32
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Line 2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def multiply_int(a, b):
>> 2 |     return a * b
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-004

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_02` (Block, Line 3)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
>>  3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
   11 |             if s[i] == s[j] and cl == 2:
   12 |                 dp[i][j] = 2
   13 |             elif s[i] == s[j]:
   14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   15 |             else:
   16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
   18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-005

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_05` (Block, Lines 11-12)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
>> 11 |             if s[i] == s[j] and cl == 2:
>> 12 |                 dp[i][j] = 2
   13 |             elif s[i] == s[j]:
   14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   15 |             else:
   16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
   18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-006

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_06` (Block, Lines 13-14)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
   11 |             if s[i] == s[j] and cl == 2:
   12 |                 dp[i][j] = 2
>> 13 |             elif s[i] == s[j]:
>> 14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   15 |             else:
   16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
   18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-007

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_07` (Block, Lines 15-16)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
   11 |             if s[i] == s[j] and cl == 2:
   12 |                 dp[i][j] = 2
   13 |             elif s[i] == s[j]:
   14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
>> 15 |             else:
>> 16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
   18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-008

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_08` (Block, Line 18)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
   11 |             if s[i] == s[j] and cl == 2:
   12 |                 dp[i][j] = 2
   13 |             elif s[i] == s[j]:
   14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   15 |             else:
   16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
>> 18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-009

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function, Lines 1-18)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def lps(s):
>>  2 |     n = len(s)
>>  3 |     dp = [[0] * n for _ in range(n)]
>>  4 |     
>>  5 |     for i in range(n):
>>  6 |         dp[i][i] = 1
>>  7 |     
>>  8 |     for cl in range(2, n + 1):
>>  9 |         for i in range(n - cl + 1):
>> 10 |             j = i + cl - 1
>> 11 |             if s[i] == s[j] and cl == 2:
>> 12 |                 dp[i][j] = 2
>> 13 |             elif s[i] == s[j]:
>> 14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
>> 15 |             else:
>> 16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
>> 17 |     
>> 18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-010

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_02` (Block, Line 3)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
>>  3 |     dp = [[0] * n for _ in range(n)]
    4 |     for i in range(n):
    5 |         dp[i][i] = 1
    6 |     for length in range(2, n + 1):
    7 |         for i in range(n - length + 1):
    8 |             j = i + length - 1
    9 |             if s[i] == s[j] and length == 2:
   10 |                 dp[i][j] = 2
   11 |             elif s[i] == s[j]:
   12 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   13 |             else:
   14 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   15 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-011

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_05` (Block, Lines 9-10)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     for i in range(n):
    5 |         dp[i][i] = 1
    6 |     for length in range(2, n + 1):
    7 |         for i in range(n - length + 1):
    8 |             j = i + length - 1
>>  9 |             if s[i] == s[j] and length == 2:
>> 10 |                 dp[i][j] = 2
   11 |             elif s[i] == s[j]:
   12 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   13 |             else:
   14 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   15 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-012

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_06` (Block, Lines 11-12)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     for i in range(n):
    5 |         dp[i][i] = 1
    6 |     for length in range(2, n + 1):
    7 |         for i in range(n - length + 1):
    8 |             j = i + length - 1
    9 |             if s[i] == s[j] and length == 2:
   10 |                 dp[i][j] = 2
>> 11 |             elif s[i] == s[j]:
>> 12 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   13 |             else:
   14 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   15 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-013

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_07` (Block, Lines 13-14)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     for i in range(n):
    5 |         dp[i][i] = 1
    6 |     for length in range(2, n + 1):
    7 |         for i in range(n - length + 1):
    8 |             j = i + length - 1
    9 |             if s[i] == s[j] and length == 2:
   10 |                 dp[i][j] = 2
   11 |             elif s[i] == s[j]:
   12 |                 dp[i][j] = dp[i + 1][j - 1] + 2
>> 13 |             else:
>> 14 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   15 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-014

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_08` (Block, Line 15)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     for i in range(n):
    5 |         dp[i][i] = 1
    6 |     for length in range(2, n + 1):
    7 |         for i in range(n - length + 1):
    8 |             j = i + length - 1
    9 |             if s[i] == s[j] and length == 2:
   10 |                 dp[i][j] = 2
   11 |             elif s[i] == s[j]:
   12 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   13 |             else:
   14 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
>> 15 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-015

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function, Lines 1-15)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def lps(s):
>>  2 |     n = len(s)
>>  3 |     dp = [[0] * n for _ in range(n)]
>>  4 |     for i in range(n):
>>  5 |         dp[i][i] = 1
>>  6 |     for length in range(2, n + 1):
>>  7 |         for i in range(n - length + 1):
>>  8 |             j = i + length - 1
>>  9 |             if s[i] == s[j] and length == 2:
>> 10 |                 dp[i][j] = 2
>> 11 |             elif s[i] == s[j]:
>> 12 |                 dp[i][j] = dp[i + 1][j - 1] + 2
>> 13 |             else:
>> 14 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
>> 15 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-016

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_02` (Block, Line 3)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
>>  3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
   11 |             if s[i] == s[j] and cl == 2:
   12 |                 dp[i][j] = 2
   13 |             elif s[i] == s[j]:
   14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   15 |             else:
   16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
   18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-017

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_05` (Block, Lines 11-12)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
>> 11 |             if s[i] == s[j] and cl == 2:
>> 12 |                 dp[i][j] = 2
   13 |             elif s[i] == s[j]:
   14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   15 |             else:
   16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
   18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-018

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_06` (Block, Lines 13-14)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
   11 |             if s[i] == s[j] and cl == 2:
   12 |                 dp[i][j] = 2
>> 13 |             elif s[i] == s[j]:
>> 14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   15 |             else:
   16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
   18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-019

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_07` (Block, Lines 15-16)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
   11 |             if s[i] == s[j] and cl == 2:
   12 |                 dp[i][j] = 2
   13 |             elif s[i] == s[j]:
   14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
>> 15 |             else:
>> 16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
   18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-020

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_08` (Block, Line 18)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lps(s):
    2 |     n = len(s)
    3 |     dp = [[0] * n for _ in range(n)]
    4 |     
    5 |     for i in range(n):
    6 |         dp[i][i] = 1
    7 |     
    8 |     for cl in range(2, n + 1):
    9 |         for i in range(n - cl + 1):
   10 |             j = i + cl - 1
   11 |             if s[i] == s[j] and cl == 2:
   12 |                 dp[i][j] = 2
   13 |             elif s[i] == s[j]:
   14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
   15 |             else:
   16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
   17 |     
>> 18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-021

### 1. Problem Context
- **Problem Task ID**: `eval_004` (MBPP Task 247)
- **Prompt / Specification**:
  > Write a function to find the length of the longest palindromic subsequence in the given string.
- **Available Test Assertions**:
  ```python
  assert lps("TENS FOR TENS") == 5
assert lps("CARDIO FOR CARDS") == 7
assert lps("PART OF THE JOURNEY IS PART") == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function, Lines 1-18)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def lps(s):
>>  2 |     n = len(s)
>>  3 |     dp = [[0] * n for _ in range(n)]
>>  4 |     
>>  5 |     for i in range(n):
>>  6 |         dp[i][i] = 1
>>  7 |     
>>  8 |     for cl in range(2, n + 1):
>>  9 |         for i in range(n - cl + 1):
>> 10 |             j = i + cl - 1
>> 11 |             if s[i] == s[j] and cl == 2:
>> 12 |                 dp[i][j] = 2
>> 13 |             elif s[i] == s[j]:
>> 14 |                 dp[i][j] = dp[i + 1][j - 1] + 2
>> 15 |             else:
>> 16 |                 dp[i][j] = max(dp[i][j - 1], dp[i + 1][j])
>> 17 |     
>> 18 |     return dp[0][n - 1]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-022

### 1. Problem Context
- **Problem Task ID**: `eval_007` (MBPP Task 392)
- **Prompt / Specification**:
  > Write a function to find the maximum sum possible by using the given equation f(n) = max( (f(n/2) + f(n/3) + f(n/4) + f(n/5)), n).
- **Available Test Assertions**:
  ```python
  assert get_max_sum(60) == 106
assert get_max_sum(10) == 12
assert get_max_sum(2) == 2
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Lines 2-3)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def get_max_sum(n, memo={}):
>> 2 |     if n in memo:
>> 3 |         return memo[n]
   4 |     if n == 0:
   5 |         return 0
   6 |     result = max(n, get_max_sum(n//2, memo) + get_max_sum(n//3, memo) + get_max_sum(n//4, memo) + get_max_sum(n//5, memo))
   7 |     memo[n] = result
   8 |     return result
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-023

### 1. Problem Context
- **Problem Task ID**: `eval_007` (MBPP Task 392)
- **Prompt / Specification**:
  > Write a function to find the maximum sum possible by using the given equation f(n) = max( (f(n/2) + f(n/3) + f(n/4) + f(n/5)), n).
- **Available Test Assertions**:
  ```python
  assert get_max_sum(60) == 106
assert get_max_sum(10) == 12
assert get_max_sum(2) == 2
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_02` (Block, Lines 4-5)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def get_max_sum(n, memo={}):
   2 |     if n in memo:
   3 |         return memo[n]
>> 4 |     if n == 0:
>> 5 |         return 0
   6 |     result = max(n, get_max_sum(n//2, memo) + get_max_sum(n//3, memo) + get_max_sum(n//4, memo) + get_max_sum(n//5, memo))
   7 |     memo[n] = result
   8 |     return result
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-024

### 1. Problem Context
- **Problem Task ID**: `eval_013` (MBPP Task 744)
- **Prompt / Specification**:
  > Write a function to check if the given tuple has any none value or not.
- **Available Test Assertions**:
  ```python
  assert check_none((10, 4, 5, 6, None)) == True
assert check_none((7, 8, 9, 11, 14)) == False
assert check_none((1, 2, 3, 4, None)) == True
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Line 2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def check_none(tup):
>> 2 |     return any(item is None for item in tup)
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-025

### 1. Problem Context
- **Problem Task ID**: `eval_014` (MBPP Task 770)
- **Prompt / Specification**:
  > Write a python function to find the sum of fourth power of first n odd natural numbers.
- **Available Test Assertions**:
  ```python
  assert odd_num_sum(2) == 82
assert odd_num_sum(3) == 707
assert odd_num_sum(4) == 3108
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Line 2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def odd_num_sum(n):
>> 2 |     return sum((2*i + 1)**4 for i in range(n))
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-026

### 1. Problem Context
- **Problem Task ID**: `eval_014` (MBPP Task 770)
- **Prompt / Specification**:
  > Write a python function to find the sum of fourth power of first n odd natural numbers.
- **Available Test Assertions**:
  ```python
  assert odd_num_sum(2) == 82
assert odd_num_sum(3) == 707
assert odd_num_sum(4) == 3108
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Line 2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def odd_num_sum(n):
>> 2 |     return sum((2*i + 1)**4 for i in range(n))
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-027

### 1. Problem Context
- **Problem Task ID**: `eval_016` (MBPP Task 793)
- **Prompt / Specification**:
  > Write a python function to find the last position of an element in a sorted array.
- **Available Test Assertions**:
  ```python
  assert last([1,2,3],1) == 0
assert last([1,1,1,2,3,4],1) == 2
assert last([2,3,2,3,6,8,9],3) == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_04` (Block, Lines 6-8)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def last(nums, target):
    2 |     left, right = 0, len(nums) - 1
    3 |     result = -1
    4 |     while left <= right:
    5 |         mid = (left + right) // 2
>>  6 |         if nums[mid] == target:
>>  7 |             result = mid
>>  8 |             left = mid + 1
    9 |         elif nums[mid] < target:
   10 |             left = mid + 1
   11 |         else:
   12 |             right = mid - 1
   13 |     return result
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-028

### 1. Problem Context
- **Problem Task ID**: `eval_016` (MBPP Task 793)
- **Prompt / Specification**:
  > Write a python function to find the last position of an element in a sorted array.
- **Available Test Assertions**:
  ```python
  assert last([1,2,3],1) == 0
assert last([1,1,1,2,3,4],1) == 2
assert last([2,3,2,3,6,8,9],3) == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_05` (Block, Lines 9-10)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def last(nums, target):
    2 |     left, right = 0, len(nums) - 1
    3 |     result = -1
    4 |     while left <= right:
    5 |         mid = (left + right) // 2
    6 |         if nums[mid] == target:
    7 |             result = mid
    8 |             left = mid + 1
>>  9 |         elif nums[mid] < target:
>> 10 |             left = mid + 1
   11 |         else:
   12 |             right = mid - 1
   13 |     return result
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-029

### 1. Problem Context
- **Problem Task ID**: `eval_016` (MBPP Task 793)
- **Prompt / Specification**:
  > Write a python function to find the last position of an element in a sorted array.
- **Available Test Assertions**:
  ```python
  assert last([1,2,3],1) == 0
assert last([1,1,1,2,3,4],1) == 2
assert last([2,3,2,3,6,8,9],3) == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function, Lines 1-13)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def last(nums, target):
>>  2 |     left, right = 0, len(nums) - 1
>>  3 |     result = -1
>>  4 |     while left <= right:
>>  5 |         mid = (left + right) // 2
>>  6 |         if nums[mid] == target:
>>  7 |             result = mid
>>  8 |             left = mid + 1
>>  9 |         elif nums[mid] < target:
>> 10 |             left = mid + 1
>> 11 |         else:
>> 12 |             right = mid - 1
>> 13 |     return result
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-030

### 1. Problem Context
- **Problem Task ID**: `mbpp_002` (MBPP Task 797)
- **Prompt / Specification**:
  > Write a python function to find the sum of all odd natural numbers within the range l and r.
- **Available Test Assertions**:
  ```python
  assert sum_in_range(2,5) == 8
assert sum_in_range(5,7) == 12
assert sum_in_range(7,13) == 40
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Line 2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def sum_in_range(l, r):
>> 2 |     return sum(x for x in range(l, r + 1) if x % 2 != 0)
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-031

### 1. Problem Context
- **Problem Task ID**: `mbpp_004` (MBPP Task 747)
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_04` (Block, Line 5)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lcs_of_three(X, Y, Z):
    2 |     m = len(X)
    3 |     n = len(Y)
    4 |     o = len(Z)
>>  5 |     L = [[[0 for _ in range(o + 1)] for _ in range(n + 1)] for _ in range(m + 1)]
    6 |     for i in range(m + 1):
    7 |         for j in range(n + 1):
    8 |             for k in range(o + 1):
    9 |                 if i == 0 or j == 0 or k == 0:
   10 |                     L[i][j][k] = 0
   11 |                 elif X[i - 1] == Y[j - 1] == Z[k - 1]:
   12 |                     L[i][j][k] = L[i - 1][j - 1][k - 1] + 1
   13 |                 else:
   14 |                     L[i][j][k] = max(max(L[i - 1][j][k], L[i][j - 1][k]), L[i][j][k - 1])
   15 |     return L[m][n][o]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-032

### 1. Problem Context
- **Problem Task ID**: `mbpp_004` (MBPP Task 747)
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_05` (Block, Lines 9-10)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lcs_of_three(X, Y, Z):
    2 |     m = len(X)
    3 |     n = len(Y)
    4 |     o = len(Z)
    5 |     L = [[[0 for _ in range(o + 1)] for _ in range(n + 1)] for _ in range(m + 1)]
    6 |     for i in range(m + 1):
    7 |         for j in range(n + 1):
    8 |             for k in range(o + 1):
>>  9 |                 if i == 0 or j == 0 or k == 0:
>> 10 |                     L[i][j][k] = 0
   11 |                 elif X[i - 1] == Y[j - 1] == Z[k - 1]:
   12 |                     L[i][j][k] = L[i - 1][j - 1][k - 1] + 1
   13 |                 else:
   14 |                     L[i][j][k] = max(max(L[i - 1][j][k], L[i][j - 1][k]), L[i][j][k - 1])
   15 |     return L[m][n][o]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-033

### 1. Problem Context
- **Problem Task ID**: `mbpp_004` (MBPP Task 747)
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_06` (Block, Lines 11-12)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lcs_of_three(X, Y, Z):
    2 |     m = len(X)
    3 |     n = len(Y)
    4 |     o = len(Z)
    5 |     L = [[[0 for _ in range(o + 1)] for _ in range(n + 1)] for _ in range(m + 1)]
    6 |     for i in range(m + 1):
    7 |         for j in range(n + 1):
    8 |             for k in range(o + 1):
    9 |                 if i == 0 or j == 0 or k == 0:
   10 |                     L[i][j][k] = 0
>> 11 |                 elif X[i - 1] == Y[j - 1] == Z[k - 1]:
>> 12 |                     L[i][j][k] = L[i - 1][j - 1][k - 1] + 1
   13 |                 else:
   14 |                     L[i][j][k] = max(max(L[i - 1][j][k], L[i][j - 1][k]), L[i][j][k - 1])
   15 |     return L[m][n][o]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-034

### 1. Problem Context
- **Problem Task ID**: `mbpp_004` (MBPP Task 747)
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_07` (Block, Lines 13-14)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lcs_of_three(X, Y, Z):
    2 |     m = len(X)
    3 |     n = len(Y)
    4 |     o = len(Z)
    5 |     L = [[[0 for _ in range(o + 1)] for _ in range(n + 1)] for _ in range(m + 1)]
    6 |     for i in range(m + 1):
    7 |         for j in range(n + 1):
    8 |             for k in range(o + 1):
    9 |                 if i == 0 or j == 0 or k == 0:
   10 |                     L[i][j][k] = 0
   11 |                 elif X[i - 1] == Y[j - 1] == Z[k - 1]:
   12 |                     L[i][j][k] = L[i - 1][j - 1][k - 1] + 1
>> 13 |                 else:
>> 14 |                     L[i][j][k] = max(max(L[i - 1][j][k], L[i][j - 1][k]), L[i][j][k - 1])
   15 |     return L[m][n][o]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-035

### 1. Problem Context
- **Problem Task ID**: `mbpp_004` (MBPP Task 747)
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function, Lines 1-15)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def lcs_of_three(X, Y, Z):
>>  2 |     m = len(X)
>>  3 |     n = len(Y)
>>  4 |     o = len(Z)
>>  5 |     L = [[[0 for _ in range(o + 1)] for _ in range(n + 1)] for _ in range(m + 1)]
>>  6 |     for i in range(m + 1):
>>  7 |         for j in range(n + 1):
>>  8 |             for k in range(o + 1):
>>  9 |                 if i == 0 or j == 0 or k == 0:
>> 10 |                     L[i][j][k] = 0
>> 11 |                 elif X[i - 1] == Y[j - 1] == Z[k - 1]:
>> 12 |                     L[i][j][k] = L[i - 1][j - 1][k - 1] + 1
>> 13 |                 else:
>> 14 |                     L[i][j][k] = max(max(L[i - 1][j][k], L[i][j - 1][k]), L[i][j][k - 1])
>> 15 |     return L[m][n][o]
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-036

### 1. Problem Context
- **Problem Task ID**: `mbpp_005` (MBPP Task 807)
- **Prompt / Specification**:
  > Write a python function to find the first odd number in a given list of numbers.
- **Available Test Assertions**:
  ```python
  assert first_odd([1,3,5]) == 1
assert first_odd([2,4,1,3]) == 1
assert first_odd ([8,9,1]) == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Lines 3-4)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def first_odd(numbers):
   2 |     for number in numbers:
>> 3 |         if number % 2 != 0:
>> 4 |             return number
   5 |     return None
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---

## Sample ID: SG-GATE-C-037

### 1. Problem Context
- **Problem Task ID**: `mbpp_005` (MBPP Task 807)
- **Prompt / Specification**:
  > Write a python function to find the first odd number in a given list of numbers.
- **Available Test Assertions**:
  ```python
  assert first_odd([1,3,5]) == 1
assert first_odd([2,4,1,3]) == 1
assert first_odd ([8,9,1]) == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Unified func block, Lines 3-4)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
   1 | def first_odd(numbers):
   2 |     for number in numbers:
>> 3 |         if number % 2 != 0:
>> 4 |             return number
   5 |     return None
```

### 3. Independent Semantic Evaluation (To be completed by Evaluator)
- **Evaluator Label**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`
- **Evaluator Rationale**: `[ UNANNOTATED — PENDING EVALUATOR INPUT ]`

---
