"""Unit tests for assess_input."""

from src.tools.assess_input import DIMENSIONS, assess_input


def test_empty_text_is_sparse_and_misses_all_dimensions():
    result = assess_input("")

    assert result.density == "sparse"
    assert result.covered_dimensions == []
    assert set(result.missing_dimensions) == set(DIMENSIONS)


def test_text_mentioning_only_stack_is_sparse():
    result = assess_input("python")

    assert result.density == "sparse"
    assert result.covered_dimensions == ["stack"]
    assert "stack" not in result.missing_dimensions
    assert len(result.missing_dimensions) == len(DIMENSIONS) - 1


def test_text_with_exactly_four_dimensions_is_rich():
    # "cli" → project_type, "python" → stack,
    # "script" → deliverable, "días" → time_available
    result = assess_input("cli python script días")

    assert result.density == "rich"
    assert set(result.covered_dimensions) == {
        "project_type",
        "stack",
        "deliverable",
        "time_available",
    }
    assert set(result.missing_dimensions) == {
        "data_sources",
        "constraints",
        "acceptance_criteria",
    }


def test_text_covering_all_seven_dimensions_is_rich_with_no_missing():
    # one keyword per dimension, in spec order:
    # project_type / stack / data_sources / constraints /
    # acceptance_criteria / deliverable / time_available
    result = assess_input("cli python csv sin validar script días")

    assert result.density == "rich"
    assert set(result.covered_dimensions) == set(DIMENSIONS)
    assert result.missing_dimensions == []
