from baserow_premium.prompts import get_generate_formula_prompt

from baserow.contrib.database.formula.registries import formula_function_registry


def test_if_prompt_contains_all_formula_functions():
    prompt = get_generate_formula_prompt()

    # These functions are for internal usage, and are not in the web-frontend
    # documentation.
    formula_exceptions = [
        "tovarchar",
        "error_to_nan",
        "bc_to_null",
        "error_to_null",
        "array_agg",
        "array_agg_unnesting",
        "multiple_select_options_agg",
        "get_single_select_value",
        "multiple_select_count",
        "string_agg_multiple_select_values",
        "string_agg_array_of_multiple_select_values",
        "jsonb_extract_path_text",
        "array_agg_no_nesting",
    ]

    for function in formula_function_registry.registry.keys():
        if function not in formula_exceptions and function not in prompt:
            assert False, f"{function} is not present in generate_formula.prompt"
