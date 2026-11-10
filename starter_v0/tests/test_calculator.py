from tools.calculator.tool import calculate


def test_calculator_arithmetic_and_sqrt():
    assert calculate("1200 * 0.65")["result"] == 780
    assert calculate("sqrt(144) + 10")["result"] == 22


def test_calculator_rejects_code_execution():
    for expression in ("__import__('os').system('echo x')", "(1).__class__", "[x for x in range(3)]"):
        assert "error" in calculate(expression)


def test_calculator_rejects_unbounded_and_invalid_input():
    for expression in ("2 ** 99999", "1 / 0", "9" * 201, ""):
        assert "error" in calculate(expression)
