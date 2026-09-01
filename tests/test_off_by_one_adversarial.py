from partner_b.mutation.mutator import mutate_off_by_one


class Step:
    problem_id = "adversarial"
    solution_id = "test"
    step_id = "block_01"

    def __init__(self, start_line, end_line):
        self.start_line = start_line
        self.end_line = end_line


def mutate(source, start_line=3, end_line=3):
    step = Step(start_line, end_line)
    return mutate_off_by_one(source, step)


def test_index_plus_one_mutates():
    source = """
def f(nums, i):
    return nums[i + 1]
"""

    result = mutate(source)

    assert result.changed is True
    assert result.original_operator == "+"
    assert result.mutated_operator == "-"
    assert "nums[i - 1]" in result.mutated_code


def test_index_minus_one_mutates():
    source = """
def f(nums, i):
    return nums[i - 1]
"""

    result = mutate(source)

    assert result.changed is True
    assert result.original_operator == "-"
    assert result.mutated_operator == "+"
    assert "nums[i + 1]" in result.mutated_code


def test_plus_two_is_not_mutated():
    source = """
def f(i):
    return i + 2
"""

    result = mutate(source)

    assert result.changed is False
    assert result.mutated_code == source


def test_minus_two_is_not_mutated():
    source = """
def f(i):
    return i - 2
"""

    result = mutate(source)

    assert result.changed is False
    assert result.mutated_code == source


def test_string_is_not_mutated():
    source = '''
def f():
    value = "i + 1"
    return value
'''

    result = mutate(source)

    assert result.changed is False
    assert result.mutated_code == source


def test_comment_is_not_mutated():
    source = """
def f(i):
    # i + 1 should remain unchanged
    return i
"""

    result = mutate(source)

    assert result.changed is False
    assert result.mutated_code == source


def test_outside_target_block_is_not_mutated():
    source = """
def f(i):
    x = i + 1
    return i
"""

    result = mutate(source, start_line=4, end_line=4)

    assert result.changed is False
    assert result.mutated_code == source


def test_only_one_index_candidate_is_mutated():
    source = """
def f(a, b, i):
    x = a[i + 1]
    y = b[i + 1]
    return x + y
"""

    result = mutate(source, start_line=3, end_line=4)

    assert result.changed is True

    original_lines = source.splitlines()
    mutated_lines = result.mutated_code.splitlines()

    changed_lines = [
        index
        for index, (before, after)
        in enumerate(
            zip(original_lines, mutated_lines),
            start=1,
        )
        if before != after
    ]

    assert len(changed_lines) == 1


def test_parenthesized_index_expression_mutates():
    source = """
def f(nums, i):
    return nums[(i + 1)]
"""

    result = mutate(source)

    assert result.changed is True
    assert result.original_operator == "+"
    assert result.mutated_operator == "-"
    assert "i - 1" in result.mutated_code


def test_float_one_is_not_mutated():
    source = """
def f(i):
    return i + 1.0
"""

    result = mutate(source)

    assert result.changed is False
    assert result.mutated_code == source

