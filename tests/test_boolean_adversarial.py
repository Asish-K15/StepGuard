from partner_b.mutation.mutator import mutate_boolean


class Step:
    problem_id = "adversarial"
    solution_id = "test"
    step_id = "block_01"

    def __init__(self, start_line, end_line):
        self.start_line = start_line
        self.end_line = end_line


def mutate(source):
    step = Step(3, 3)
    return mutate_boolean(source, step)


def test_and_keyword_mutates():
    source = """
def f(x, y):
    return x and y
"""

    result = mutate(source)

    assert result.changed is True
    assert result.original_operator == "and"
    assert result.mutated_operator == "or"
    assert "x or y" in result.mutated_code


def test_or_keyword_mutates():
    source = """
def f(x, y):
    return x or y
"""

    result = mutate(source)

    assert result.changed is True
    assert result.original_operator == "or"
    assert result.mutated_operator == "and"
    assert "x and y" in result.mutated_code


def test_true_mutates():
    source = """
def f():
    return True
"""

    result = mutate(source)

    assert result.changed is True
    assert result.original_operator == "True"
    assert result.mutated_operator == "False"
    assert "return False" in result.mutated_code


def test_false_mutates():
    source = """
def f():
    return False
"""

    result = mutate(source)

    assert result.changed is True
    assert result.original_operator == "False"
    assert result.mutated_operator == "True"
    assert "return True" in result.mutated_code


def test_string_and_is_not_mutated():
    source = '''
def f():
    value = "and"
    return value
'''

    result = mutate(source)

    assert result.changed is False
    assert result.mutated_code == source


def test_string_or_is_not_mutated():
    source = '''
def f():
    value = "or"
    return value
'''

    result = mutate(source)

    assert result.changed is False
    assert result.mutated_code == source


def test_variable_containing_and_is_not_mutated():
    source = """
def f():
    sandwich = 1
    return sandwich
"""

    result = mutate(source)

    assert result.changed is False
    assert result.mutated_code == source


def test_multiple_boolean_operators_mutates_only_one():
    source = """
def f(x, y, z):
    return x and y or z
"""

    result = mutate(source)

    assert result.changed is True

    # Exactly one operator should change.
    assert result.mutated_code.count("or") == 2
    assert result.mutated_code.count("and") == 0 or result.mutated_code.count("and") == 1