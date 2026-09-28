# StepGuard Independent Human-Validation Study: Blind Annotation Sheet

> [!IMPORTANT]
> **BLIND STUDY PROTOCOL**:
> This annotation sheet is strictly blinded. All mutation-derived labels, PRM predictions,
> detection outcomes, and confidence scores have been withheld to guarantee evaluator independence.
> Do not consult external mutation result logs during annotation.

## Evaluator Instructions
For each sample below:
1. Read the **Problem Specification** and the provided **Test Suite Assertions**.
2. Review the **Complete Candidate Solution** and identify the highlighted **Target Step** (`>>`).
3. Evaluate the step's correctness and semantic soundness in the context of the program:
   - **CORRECT**: The step represents a correct, valid intermediate operation towards fulfilling the specification.
   - **UNCERTAIN**: The step contains flawed logic, redundant or ineffective conditions, unverified edge case handling, or ambiguity under-constrained by the tests.
4. Fill in the **Human Label** and optionally provide your **Rationale**.

---

## Sample ID: SG-VAL-001

### 1. Problem Context
- **Problem Task ID**: MBPP Task 783
- **Prompt / Specification**:
  > Write a function to convert rgb color to hsv color. https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
- **Available Test Assertions**:
  ```python
  assert rgb_to_hsv(255, 255, 255)==(0, 0.0, 100.0)
  ```
  ```python
  assert rgb_to_hsv(0, 215, 0)==(120.0, 100.0, 84.31372549019608)
  ```
  ```python
  assert rgb_to_hsv(10, 215, 110)==(149.26829268292684, 95.34883720930233, 84.31372549019608)
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_05` (Block decomposition, Lines 6-7)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def rgb_to_hsv(r, g, b):
    2 |     r, g, b = r / 255.0, g / 255.0, b / 255.0
    3 |     mx = max(r, g, b)
    4 |     mn = min(r, g, b)
    5 |     df = mx - mn
>>  6 |     if mx == mn:
>>  7 |         h = 0
    8 |     elif mx == r:
    9 |         h = (60 * ((g - b) / df) + 360) % 360
   10 |     elif mx == g:
   11 |         h = (60 * ((b - r) / df) + 120) % 360
   12 |     elif mx == b:
   13 |         h = (60 * ((r - g) / df) + 240) % 360
   14 |     if mx == 0:
   15 |         s = 0
   16 |     else:
   17 |         s = (df / mx) * 100
   18 |     v = mx * 100
   19 |     return h, s, v
```
- **Isolated Target Step Source**:
```python
    if mx == mn:
        h = 0
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 6 to 7.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-002

### 1. Problem Context
- **Problem Task ID**: MBPP Task 797
- **Prompt / Specification**:
  > Write a python function to find the sum of all odd natural numbers within the range l and r.
- **Available Test Assertions**:
  ```python
  assert sum_in_range(2,5) == 8
  ```
  ```python
  assert sum_in_range(5,7) == 12
  ```
  ```python
  assert sum_in_range(7,13) == 40
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function decomposition, Lines 1-2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def sum_in_range(l, r):
>>  2 |     return sum(num for num in range(l, r + 1) if num % 2 != 0)
```
- **Isolated Target Step Source**:
```python
def sum_in_range(l, r):
    return sum(num for num in range(l, r + 1) if num % 2 != 0)
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST function segment spanning lines 1 to 2.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-003

### 1. Problem Context
- **Problem Task ID**: MBPP Task 790
- **Prompt / Specification**:
  > Write a python function to check whether every even index contains even numbers of a given list.
- **Available Test Assertions**:
  ```python
  assert even_position([3,2,1]) == False
  ```
  ```python
  assert even_position([1,2,3]) == False
  ```
  ```python
  assert even_position([2,1,4]) == True
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function decomposition, Lines 1-2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def even_position(lst):
>>  2 |     return all(lst[i] % 2 == 0 for i in range(0, len(lst), 2))
```
- **Isolated Target Step Source**:
```python
def even_position(lst):
    return all(lst[i] % 2 == 0 for i in range(0, len(lst), 2))
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST function segment spanning lines 1 to 2.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-004

### 1. Problem Context
- **Problem Task ID**: MBPP Task 783
- **Prompt / Specification**:
  > Write a function to convert rgb color to hsv color. https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
- **Available Test Assertions**:
  ```python
  assert rgb_to_hsv(255, 255, 255)==(0, 0.0, 100.0)
  ```
  ```python
  assert rgb_to_hsv(0, 215, 0)==(120.0, 100.0, 84.31372549019608)
  ```
  ```python
  assert rgb_to_hsv(10, 215, 110)==(149.26829268292684, 95.34883720930233, 84.31372549019608)
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function decomposition, Lines 1-19)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def rgb_to_hsv(r, g, b):
>>  2 |     r, g, b = r / 255.0, g / 255.0, b / 255.0
>>  3 |     mx = max(r, g, b)
>>  4 |     mn = min(r, g, b)
>>  5 |     df = mx - mn
>>  6 |     if mx == mn:
>>  7 |         h = 0
>>  8 |     elif mx == r:
>>  9 |         h = (60 * ((g - b) / df) + 360) % 360
>> 10 |     elif mx == g:
>> 11 |         h = (60 * ((b - r) / df) + 120) % 360
>> 12 |     elif mx == b:
>> 13 |         h = (60 * ((r - g) / df) + 240) % 360
>> 14 |     if mx == 0:
>> 15 |         s = 0
>> 16 |     else:
>> 17 |         s = (df / mx) * 100
>> 18 |     v = mx * 100
>> 19 |     return h, s, v
```
- **Isolated Target Step Source**:
```python
def rgb_to_hsv(r, g, b):
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    mx = max(r, g, b)
    mn = min(r, g, b)
    df = mx - mn
    if mx == mn:
        h = 0
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
    elif mx == g:
        h = (60 * ((b - r) / df) + 120) % 360
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
    if mx == 0:
        s = 0
    else:
        s = (df / mx) * 100
    v = mx * 100
    return h, s, v
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST function segment spanning lines 1 to 19.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-005

### 1. Problem Context
- **Problem Task ID**: MBPP Task 807
- **Prompt / Specification**:
  > Write a python function to find the first odd number in a given list of numbers.
- **Available Test Assertions**:
  ```python
  assert first_odd([1,3,5]) == 1
  ```
  ```python
  assert first_odd([2,4,1,3]) == 1
  ```
  ```python
  assert first_odd ([8,9,1]) == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Block decomposition, Lines 3-4)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def first_odd(numbers):
    2 |     for number in numbers:
>>  3 |         if number % 2 != 0:
>>  4 |             return number
    5 |     return None
```
- **Isolated Target Step Source**:
```python
        if number % 2 != 0:
            return number
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 3 to 4.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-006

### 1. Problem Context
- **Problem Task ID**: MBPP Task 747
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
  ```
  ```python
  assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
  ```
  ```python
  assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_05` (Block decomposition, Lines 9-10)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lcs_of_three(X, Y, Z):
    2 |     m = len(X)
    3 |     n = len(Y)
    4 |     o = len(Z)
    5 |     L = [[[0 for _ in range(o+1)] for _ in range(n+1)] for _ in range(m+1)]
    6 |     for i in range(m+1):
    7 |         for j in range(n+1):
    8 |             for k in range(o+1):
>>  9 |                 if i == 0 or j == 0 or k == 0:
>> 10 |                     L[i][j][k] = 0
   11 |                 elif X[i-1] == Y[j-1] == Z[k-1]:
   12 |                     L[i][j][k] = L[i-1][j-1][k-1] + 1
   13 |                 else:
   14 |                     L[i][j][k] = max(max(L[i-1][j][k], L[i][j-1][k]), L[i][j][k-1])
   15 |     return L[m][n][o]
```
- **Isolated Target Step Source**:
```python
                if i == 0 or j == 0 or k == 0:
                    L[i][j][k] = 0
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 9 to 10.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-007

### 1. Problem Context
- **Problem Task ID**: MBPP Task 747
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
  ```
  ```python
  assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
  ```
  ```python
  assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function decomposition, Lines 1-17)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def lcs_of_three(X, Y, Z):
>>  2 |     m = len(X)
>>  3 |     n = len(Y)
>>  4 |     o = len(Z)
>>  5 |     L = [[[0 for _ in range(o+1)] for _ in range(n+1)] for _ in range(m+1)]
>>  6 |     
>>  7 |     for i in range(m+1):
>>  8 |         for j in range(n+1):
>>  9 |             for k in range(o+1):
>> 10 |                 if i == 0 or j == 0 or k == 0:
>> 11 |                     L[i][j][k] = 0
>> 12 |                 elif X[i-1] == Y[j-1] == Z[k-1]:
>> 13 |                     L[i][j][k] = L[i-1][j-1][k-1] + 1
>> 14 |                 else:
>> 15 |                     L[i][j][k] = max(max(L[i-1][j][k], L[i][j-1][k]), L[i][j][k-1])
>> 16 |     
>> 17 |     return L[m][n][o]
```
- **Isolated Target Step Source**:
```python
def lcs_of_three(X, Y, Z):
    m = len(X)
    n = len(Y)
    o = len(Z)
    L = [[[0 for _ in range(o+1)] for _ in range(n+1)] for _ in range(m+1)]
    
    for i in range(m+1):
        for j in range(n+1):
            for k in range(o+1):
                if i == 0 or j == 0 or k == 0:
                    L[i][j][k] = 0
                elif X[i-1] == Y[j-1] == Z[k-1]:
                    L[i][j][k] = L[i-1][j-1][k-1] + 1
                else:
                    L[i][j][k] = max(max(L[i-1][j][k], L[i][j-1][k]), L[i][j][k-1])
    
    return L[m][n][o]
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST function segment spanning lines 1 to 17.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-008

### 1. Problem Context
- **Problem Task ID**: MBPP Task 790
- **Prompt / Specification**:
  > Write a python function to check whether every even index contains even numbers of a given list.
- **Available Test Assertions**:
  ```python
  assert even_position([3,2,1]) == False
  ```
  ```python
  assert even_position([1,2,3]) == False
  ```
  ```python
  assert even_position([2,1,4]) == True
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Block decomposition, Lines 3-4)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def even_position(lst):
    2 |     for i, num in enumerate(lst):
>>  3 |         if i % 2 == 0 and num % 2 != 0:
>>  4 |             return False
    5 |     return True
```
- **Isolated Target Step Source**:
```python
        if i % 2 == 0 and num % 2 != 0:
            return False
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 3 to 4.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-009

### 1. Problem Context
- **Problem Task ID**: MBPP Task 797
- **Prompt / Specification**:
  > Write a python function to find the sum of all odd natural numbers within the range l and r.
- **Available Test Assertions**:
  ```python
  assert sum_in_range(2,5) == 8
  ```
  ```python
  assert sum_in_range(5,7) == 12
  ```
  ```python
  assert sum_in_range(7,13) == 40
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function decomposition, Lines 1-2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def sum_in_range(l, r):
>>  2 |     return sum(x for x in range(l, r + 1) if x % 2 != 0)
```
- **Isolated Target Step Source**:
```python
def sum_in_range(l, r):
    return sum(x for x in range(l, r + 1) if x % 2 != 0)
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST function segment spanning lines 1 to 2.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-010

### 1. Problem Context
- **Problem Task ID**: MBPP Task 747
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
  ```
  ```python
  assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
  ```
  ```python
  assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function decomposition, Lines 1-18)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def lcs_of_three(X, Y, Z):
>>  2 |     m = len(X)
>>  3 |     n = len(Y)
>>  4 |     o = len(Z)
>>  5 |     
>>  6 |     L = [[[0 for k in range(o+1)] for j in range(n+1)] for i in range(m+1)]
>>  7 |     
>>  8 |     for i in range(m+1):
>>  9 |         for j in range(n+1):
>> 10 |             for k in range(o+1):
>> 11 |                 if i == 0 or j == 0 or k == 0:
>> 12 |                     L[i][j][k] = 0
>> 13 |                 elif X[i-1] == Y[j-1] == Z[k-1]:
>> 14 |                     L[i][j][k] = L[i-1][j-1][k-1] + 1
>> 15 |                 else:
>> 16 |                     L[i][j][k] = max(max(L[i-1][j][k], L[i][j-1][k]), L[i][j][k-1])
>> 17 |     
>> 18 |     return L[m][n][o]
```
- **Isolated Target Step Source**:
```python
def lcs_of_three(X, Y, Z):
    m = len(X)
    n = len(Y)
    o = len(Z)
    
    L = [[[0 for k in range(o+1)] for j in range(n+1)] for i in range(m+1)]
    
    for i in range(m+1):
        for j in range(n+1):
            for k in range(o+1):
                if i == 0 or j == 0 or k == 0:
                    L[i][j][k] = 0
                elif X[i-1] == Y[j-1] == Z[k-1]:
                    L[i][j][k] = L[i-1][j-1][k-1] + 1
                else:
                    L[i][j][k] = max(max(L[i-1][j][k], L[i][j-1][k]), L[i][j][k-1])
    
    return L[m][n][o]
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST function segment spanning lines 1 to 18.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-011

### 1. Problem Context
- **Problem Task ID**: MBPP Task 747
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
  ```
  ```python
  assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
  ```
  ```python
  assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_06` (Block decomposition, Lines 11-12)
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
- **Isolated Target Step Source**:
```python
                elif X[i - 1] == Y[j - 1] == Z[k - 1]:
                    L[i][j][k] = L[i - 1][j - 1][k - 1] + 1
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 11 to 12.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-012

### 1. Problem Context
- **Problem Task ID**: MBPP Task 790
- **Prompt / Specification**:
  > Write a python function to check whether every even index contains even numbers of a given list.
- **Available Test Assertions**:
  ```python
  assert even_position([3,2,1]) == False
  ```
  ```python
  assert even_position([1,2,3]) == False
  ```
  ```python
  assert even_position([2,1,4]) == True
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_02` (Block decomposition, Lines 5-5)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def even_position(lst):
    2 |     for i, num in enumerate(lst):
    3 |         if i % 2 == 0 and num % 2 != 0:
    4 |             return False
>>  5 |     return True
```
- **Isolated Target Step Source**:
```python
return True
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 5 to 5.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-013

### 1. Problem Context
- **Problem Task ID**: MBPP Task 783
- **Prompt / Specification**:
  > Write a function to convert rgb color to hsv color. https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
- **Available Test Assertions**:
  ```python
  assert rgb_to_hsv(255, 255, 255)==(0, 0.0, 100.0)
  ```
  ```python
  assert rgb_to_hsv(0, 215, 0)==(120.0, 100.0, 84.31372549019608)
  ```
  ```python
  assert rgb_to_hsv(10, 215, 110)==(149.26829268292684, 95.34883720930233, 84.31372549019608)
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_06` (Block decomposition, Lines 8-9)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def rgb_to_hsv(r, g, b):
    2 |     r, g, b = r / 255.0, g / 255.0, b / 255.0
    3 |     mx = max(r, g, b)
    4 |     mn = min(r, g, b)
    5 |     df = mx - mn
    6 |     if mx == mn:
    7 |         h = 0
>>  8 |     elif mx == r:
>>  9 |         h = (60 * ((g - b) / df) + 360) % 360
   10 |     elif mx == g:
   11 |         h = (60 * ((b - r) / df) + 120) % 360
   12 |     elif mx == b:
   13 |         h = (60 * ((r - g) / df) + 240) % 360
   14 |     if mx == 0:
   15 |         s = 0
   16 |     else:
   17 |         s = (df / mx) * 100
   18 |     v = mx * 100
   19 |     return h, s, v
```
- **Isolated Target Step Source**:
```python
    elif mx == r:
        h = (60 * ((g - b) / df) + 360) % 360
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 8 to 9.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-014

### 1. Problem Context
- **Problem Task ID**: MBPP Task 797
- **Prompt / Specification**:
  > Write a python function to find the sum of all odd natural numbers within the range l and r.
- **Available Test Assertions**:
  ```python
  assert sum_in_range(2,5) == 8
  ```
  ```python
  assert sum_in_range(5,7) == 12
  ```
  ```python
  assert sum_in_range(7,13) == 40
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Block decomposition, Lines 2-2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def sum_in_range(l, r):
>>  2 |     return sum(x for x in range(l, r + 1) if x % 2 != 0)
```
- **Isolated Target Step Source**:
```python
return sum(x for x in range(l, r + 1) if x % 2 != 0)
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 2 to 2.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-015

### 1. Problem Context
- **Problem Task ID**: MBPP Task 807
- **Prompt / Specification**:
  > Write a python function to find the first odd number in a given list of numbers.
- **Available Test Assertions**:
  ```python
  assert first_odd([1,3,5]) == 1
  ```
  ```python
  assert first_odd([2,4,1,3]) == 1
  ```
  ```python
  assert first_odd ([8,9,1]) == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function decomposition, Lines 1-5)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def first_odd(numbers):
>>  2 |     for num in numbers:
>>  3 |         if num % 2 != 0:
>>  4 |             return num
>>  5 |     return None
```
- **Isolated Target Step Source**:
```python
def first_odd(numbers):
    for num in numbers:
        if num % 2 != 0:
            return num
    return None
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST function segment spanning lines 1 to 5.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-016

### 1. Problem Context
- **Problem Task ID**: MBPP Task 783
- **Prompt / Specification**:
  > Write a function to convert rgb color to hsv color. https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
- **Available Test Assertions**:
  ```python
  assert rgb_to_hsv(255, 255, 255)==(0, 0.0, 100.0)
  ```
  ```python
  assert rgb_to_hsv(0, 215, 0)==(120.0, 100.0, 84.31372549019608)
  ```
  ```python
  assert rgb_to_hsv(10, 215, 110)==(149.26829268292684, 95.34883720930233, 84.31372549019608)
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_08` (Block decomposition, Lines 12-13)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def rgb_to_hsv(r, g, b):
    2 |     r, g, b = r / 255.0, g / 255.0, b / 255.0
    3 |     mx = max(r, g, b)
    4 |     mn = min(r, g, b)
    5 |     df = mx - mn
    6 |     if mx == mn:
    7 |         h = 0
    8 |     elif mx == r:
    9 |         h = (60 * ((g - b) / df) + 360) % 360
   10 |     elif mx == g:
   11 |         h = (60 * ((b - r) / df) + 120) % 360
>> 12 |     elif mx == b:
>> 13 |         h = (60 * ((r - g) / df) + 240) % 360
   14 |     if mx == 0:
   15 |         s = 0
   16 |     else:
   17 |         s = (df / mx) * 100
   18 |     v = mx * 100
   19 |     return h, s, v
```
- **Isolated Target Step Source**:
```python
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 12 to 13.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-017

### 1. Problem Context
- **Problem Task ID**: MBPP Task 790
- **Prompt / Specification**:
  > Write a python function to check whether every even index contains even numbers of a given list.
- **Available Test Assertions**:
  ```python
  assert even_position([3,2,1]) == False
  ```
  ```python
  assert even_position([1,2,3]) == False
  ```
  ```python
  assert even_position([2,1,4]) == True
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Block decomposition, Lines 2-2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def even_position(lst):
>>  2 |     return all(lst[i] % 2 == i % 2 for i in range(len(lst)))
```
- **Isolated Target Step Source**:
```python
return all(lst[i] % 2 == i % 2 for i in range(len(lst)))
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 2 to 2.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-018

### 1. Problem Context
- **Problem Task ID**: MBPP Task 783
- **Prompt / Specification**:
  > Write a function to convert rgb color to hsv color. https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
- **Available Test Assertions**:
  ```python
  assert rgb_to_hsv(255, 255, 255)==(0, 0.0, 100.0)
  ```
  ```python
  assert rgb_to_hsv(0, 215, 0)==(120.0, 100.0, 84.31372549019608)
  ```
  ```python
  assert rgb_to_hsv(10, 215, 110)==(149.26829268292684, 95.34883720930233, 84.31372549019608)
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_08` (Block decomposition, Lines 12-13)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def rgb_to_hsv(r, g, b):
    2 |     r, g, b = r / 255.0, g / 255.0, b / 255.0
    3 |     mx = max(r, g, b)
    4 |     mn = min(r, g, b)
    5 |     df = mx - mn
    6 |     if mx == mn:
    7 |         h = 0
    8 |     elif mx == r:
    9 |         h = (60 * ((g - b) / df) + 360) % 360
   10 |     elif mx == g:
   11 |         h = (60 * ((b - r) / df) + 120) % 360
>> 12 |     elif mx == b:
>> 13 |         h = (60 * ((r - g) / df) + 240) % 360
   14 |     if mx == 0:
   15 |         s = 0
   16 |     else:
   17 |         s = (df / mx) * 100
   18 |     v = mx * 100
   19 |     return h, s, v
```
- **Isolated Target Step Source**:
```python
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 12 to 13.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-019

### 1. Problem Context
- **Problem Task ID**: MBPP Task 797
- **Prompt / Specification**:
  > Write a python function to find the sum of all odd natural numbers within the range l and r.
- **Available Test Assertions**:
  ```python
  assert sum_in_range(2,5) == 8
  ```
  ```python
  assert sum_in_range(5,7) == 12
  ```
  ```python
  assert sum_in_range(7,13) == 40
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Block decomposition, Lines 2-2)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def sum_in_range(l, r):
>>  2 |     return sum(i for i in range(l, r + 1) if i % 2 != 0)
```
- **Isolated Target Step Source**:
```python
return sum(i for i in range(l, r + 1) if i % 2 != 0)
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 2 to 2.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-020

### 1. Problem Context
- **Problem Task ID**: MBPP Task 807
- **Prompt / Specification**:
  > Write a python function to find the first odd number in a given list of numbers.
- **Available Test Assertions**:
  ```python
  assert first_odd([1,3,5]) == 1
  ```
  ```python
  assert first_odd([2,4,1,3]) == 1
  ```
  ```python
  assert first_odd ([8,9,1]) == 9
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_01` (Block decomposition, Lines 3-4)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def first_odd(numbers):
    2 |     for number in numbers:
>>  3 |         if number % 2 != 0:
>>  4 |             return number
```
- **Isolated Target Step Source**:
```python
        if number % 2 != 0:
            return number
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 3 to 4.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-021

### 1. Problem Context
- **Problem Task ID**: MBPP Task 747
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
  ```
  ```python
  assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
  ```
  ```python
  assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_05` (Block decomposition, Lines 10-11)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lcs_of_three(X, Y, Z):
    2 |     m = len(X)
    3 |     n = len(Y)
    4 |     o = len(Z)
    5 |     L = [[[0 for _ in range(o+1)] for _ in range(n+1)] for _ in range(m+1)]
    6 |     
    7 |     for i in range(m+1):
    8 |         for j in range(n+1):
    9 |             for k in range(o+1):
>> 10 |                 if i == 0 or j == 0 or k == 0:
>> 11 |                     L[i][j][k] = 0
   12 |                 elif X[i-1] == Y[j-1] == Z[k-1]:
   13 |                     L[i][j][k] = L[i-1][j-1][k-1] + 1
   14 |                 else:
   15 |                     L[i][j][k] = max(max(L[i-1][j][k], L[i][j-1][k]), L[i][j][k-1])
   16 |     
   17 |     return L[m][n][o]
```
- **Isolated Target Step Source**:
```python
                if i == 0 or j == 0 or k == 0:
                    L[i][j][k] = 0
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 10 to 11.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-022

### 1. Problem Context
- **Problem Task ID**: MBPP Task 747
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
  ```
  ```python
  assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
  ```
  ```python
  assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function decomposition, Lines 1-13)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
>>  1 | def lcs_of_three(X, Y, Z):
>>  2 |     m = len(X)
>>  3 |     n = len(Y)
>>  4 |     o = len(Z)
>>  5 |     L = [[[0 for _ in range(o+1)] for _ in range(n+1)] for _ in range(m+1)]
>>  6 |     for i in range(m-1, -1, -1):
>>  7 |         for j in range(n-1, -1, -1):
>>  8 |             for k in range(o-1, -1, -1):
>>  9 |                 if X[i] == Y[j] == Z[k]:
>> 10 |                     L[i][j][k] = L[i+1][j+1][k+1] + 1
>> 11 |                 else:
>> 12 |                     L[i][j][k] = max(max(L[i+1][j][k], L[i][j+1][k]), L[i][j][k+1])
>> 13 |     return L[0][0][0]
```
- **Isolated Target Step Source**:
```python
def lcs_of_three(X, Y, Z):
    m = len(X)
    n = len(Y)
    o = len(Z)
    L = [[[0 for _ in range(o+1)] for _ in range(n+1)] for _ in range(m+1)]
    for i in range(m-1, -1, -1):
        for j in range(n-1, -1, -1):
            for k in range(o-1, -1, -1):
                if X[i] == Y[j] == Z[k]:
                    L[i][j][k] = L[i+1][j+1][k+1] + 1
                else:
                    L[i][j][k] = max(max(L[i+1][j][k], L[i][j+1][k]), L[i][j][k+1])
    return L[0][0][0]
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST function segment spanning lines 1 to 13.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-023

### 1. Problem Context
- **Problem Task ID**: MBPP Task 747
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
  ```
  ```python
  assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
  ```
  ```python
  assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `func_01` (Function decomposition, Lines 1-15)
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
- **Isolated Target Step Source**:
```python
def lcs_of_three(X, Y, Z):
    m = len(X)
    n = len(Y)
    o = len(Z)
    L = [[[0 for _ in range(o + 1)] for _ in range(n + 1)] for _ in range(m + 1)]
    for i in range(m + 1):
        for j in range(n + 1):
            for k in range(o + 1):
                if i == 0 or j == 0 or k == 0:
                    L[i][j][k] = 0
                elif X[i - 1] == Y[j - 1] == Z[k - 1]:
                    L[i][j][k] = L[i - 1][j - 1][k - 1] + 1
                else:
                    L[i][j][k] = max(max(L[i - 1][j][k], L[i][j - 1][k]), L[i][j][k - 1])
    return L[m][n][o]
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST function segment spanning lines 1 to 15.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-024

### 1. Problem Context
- **Problem Task ID**: MBPP Task 747
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
  ```
  ```python
  assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
  ```
  ```python
  assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_05` (Block decomposition, Lines 11-12)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def lcs_of_three(X, Y, Z):
    2 |     m = len(X)
    3 |     n = len(Y)
    4 |     o = len(Z)
    5 |     
    6 |     L = [[[0 for k in range(o+1)] for j in range(n+1)] for i in range(m+1)]
    7 |     
    8 |     for i in range(m+1):
    9 |         for j in range(n+1):
   10 |             for k in range(o+1):
>> 11 |                 if i == 0 or j == 0 or k == 0:
>> 12 |                     L[i][j][k] = 0
   13 |                 elif X[i-1] == Y[j-1] == Z[k-1]:
   14 |                     L[i][j][k] = L[i-1][j-1][k-1] + 1
   15 |                 else:
   16 |                     L[i][j][k] = max(max(L[i-1][j][k], L[i][j-1][k]), L[i][j][k-1])
   17 |     
   18 |     return L[m][n][o]
```
- **Isolated Target Step Source**:
```python
                if i == 0 or j == 0 or k == 0:
                    L[i][j][k] = 0
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 11 to 12.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-025

### 1. Problem Context
- **Problem Task ID**: MBPP Task 747
- **Prompt / Specification**:
  > Write a function to find the longest common subsequence for the given three string sequence. https://www.geeksforgeeks.org/lcs-longest-common-subsequence-three-strings/
- **Available Test Assertions**:
  ```python
  assert lcs_of_three('AGGT12', '12TXAYB', '12XBA') == 2
  ```
  ```python
  assert lcs_of_three('Reels', 'Reelsfor', 'ReelsforReels') == 5
  ```
  ```python
  assert lcs_of_three('abcd1e2', 'bc12ea', 'bd1ea') == 3
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_04` (Block decomposition, Lines 5-5)
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
- **Isolated Target Step Source**:
```python
L = [[[0 for _ in range(o + 1)] for _ in range(n + 1)] for _ in range(m + 1)]
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 5 to 5.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-026

### 1. Problem Context
- **Problem Task ID**: MBPP Task 783
- **Prompt / Specification**:
  > Write a function to convert rgb color to hsv color. https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
- **Available Test Assertions**:
  ```python
  assert rgb_to_hsv(255, 255, 255)==(0, 0.0, 100.0)
  ```
  ```python
  assert rgb_to_hsv(0, 215, 0)==(120.0, 100.0, 84.31372549019608)
  ```
  ```python
  assert rgb_to_hsv(10, 215, 110)==(149.26829268292684, 95.34883720930233, 84.31372549019608)
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_08` (Block decomposition, Lines 12-13)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def rgb_to_hsv(r, g, b):
    2 |     r, g, b = r / 255.0, g / 255.0, b / 255.0
    3 |     mx = max(r, g, b)
    4 |     mn = min(r, g, b)
    5 |     df = mx - mn
    6 |     if mx == mn:
    7 |         h = 0
    8 |     elif mx == r:
    9 |         h = (60 * ((g - b) / df) + 360) % 360
   10 |     elif mx == g:
   11 |         h = (60 * ((b - r) / df) + 120) % 360
>> 12 |     elif mx == b:
>> 13 |         h = (60 * ((r - g) / df) + 240) % 360
   14 |     if mx == 0:
   15 |         s = 0
   16 |     else:
   17 |         s = (df / mx) * 100
   18 |     v = mx * 100
   19 |     return h, s, v
```
- **Isolated Target Step Source**:
```python
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 12 to 13.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-027

### 1. Problem Context
- **Problem Task ID**: MBPP Task 783
- **Prompt / Specification**:
  > Write a function to convert rgb color to hsv color. https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
- **Available Test Assertions**:
  ```python
  assert rgb_to_hsv(255, 255, 255)==(0, 0.0, 100.0)
  ```
  ```python
  assert rgb_to_hsv(0, 215, 0)==(120.0, 100.0, 84.31372549019608)
  ```
  ```python
  assert rgb_to_hsv(10, 215, 110)==(149.26829268292684, 95.34883720930233, 84.31372549019608)
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_08` (Block decomposition, Lines 12-13)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def rgb_to_hsv(r, g, b):
    2 |     r, g, b = r / 255.0, g / 255.0, b / 255.0
    3 |     mx = max(r, g, b)
    4 |     mn = min(r, g, b)
    5 |     df = mx - mn
    6 |     if mx == mn:
    7 |         h = 0
    8 |     elif mx == r:
    9 |         h = (60 * ((g - b) / df) + 360) % 360
   10 |     elif mx == g:
   11 |         h = (60 * ((b - r) / df) + 120) % 360
>> 12 |     elif mx == b:
>> 13 |         h = (60 * ((r - g) / df) + 240) % 360
   14 |     if mx == 0:
   15 |         s = 0
   16 |     else:
   17 |         s = (df / mx) * 100
   18 |     v = mx * 100
   19 |     return h, s, v
```
- **Isolated Target Step Source**:
```python
    elif mx == b:
        h = (60 * ((r - g) / df) + 240) % 360
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 12 to 13.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---

## Sample ID: SG-VAL-028

### 1. Problem Context
- **Problem Task ID**: MBPP Task 783
- **Prompt / Specification**:
  > Write a function to convert rgb color to hsv color. https://www.geeksforgeeks.org/program-change-rgb-color-model-hsv-color-model/
- **Available Test Assertions**:
  ```python
  assert rgb_to_hsv(255, 255, 255)==(0, 0.0, 100.0)
  ```
  ```python
  assert rgb_to_hsv(0, 215, 0)==(120.0, 100.0, 84.31372549019608)
  ```
  ```python
  assert rgb_to_hsv(10, 215, 110)==(149.26829268292684, 95.34883720930233, 84.31372549019608)
  ```

### 2. Relevant Candidate Solution and Target Step
- **Target Step Identifier**: `block_09` (Block decomposition, Lines 14-15)
- **Full Candidate Code** (target step lines indicated with `>>`):
```python
    1 | def rgb_to_hsv(r, g, b):
    2 |     r, g, b = r / 255.0, g / 255.0, b / 255.0
    3 |     mx = max(r, g, b)
    4 |     mn = min(r, g, b)
    5 |     df = mx - mn
    6 |     if mx == mn:
    7 |         h = 0
    8 |     elif mx == r:
    9 |         h = (60 * ((g - b) / df) + 360) % 360
   10 |     elif mx == g:
   11 |         h = (60 * ((b - r) / df) + 120) % 360
   12 |     elif mx == b:
   13 |         h = (60 * ((r - g) / df) + 240) % 360
>> 14 |     if mx == 0:
>> 15 |         s = 0
   16 |     else:
   17 |         s = (df / mx) * 100
   18 |     v = mx * 100
   19 |     return h, s, v
```
- **Isolated Target Step Source**:
```python
    if mx == 0:
        s = 0
```

### 3. Execution & Contextual Evidence
- **Baseline Execution Outcome**: `PASS` (Candidate solution executed cleanly and passed all provided problem test assertions).
- **Decomposition Unit**: Non-overlapping AST block segment spanning lines 14 to 15.
- **Syntactic Verification**: Valid Python AST segment; clean execution without unhandled exceptions at baseline.

### 4. Human Evaluator Assessment
- **Human Label**: `[  ] CORRECT      [  ] UNCERTAIN`
- **Rationale (Optional)**:
  ```
  
  ```

---
