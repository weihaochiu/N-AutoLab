"""Tests for Recipe and RecipeStep declarations."""

import pytest

from nautolab.core import Action, InvalidRecipeError, Recipe, RecipeStep


def wait_step(step_id: str, order: int) -> RecipeStep:
    return RecipeStep(
        step_id=step_id,
        order=order,
        action=Action(id=f"action_{step_id}", action_type="WAIT"),
    )


def test_recipe_orders_steps_without_executing_them() -> None:
    recipe = Recipe(id="demo_recipe", name="Demo", steps=(wait_step("second", 2), wait_step("first", 1)))
    assert [step.step_id for step in recipe.steps] == ["first", "second"]
    assert not hasattr(recipe, "execute")
    assert not hasattr(recipe, "run")


def test_recipe_rejects_duplicate_step_ids() -> None:
    with pytest.raises(InvalidRecipeError, match="identifiers"):
        Recipe(id="demo_recipe", name="Demo", steps=(wait_step("same", 1), wait_step("same", 2)))


def test_recipe_rejects_duplicate_order_values() -> None:
    with pytest.raises(InvalidRecipeError, match="order"):
        Recipe(id="demo_recipe", name="Demo", steps=(wait_step("one", 1), wait_step("two", 1)))


def test_recipe_add_step_preserves_invariants() -> None:
    recipe = Recipe(id="demo_recipe", name="Demo")
    recipe.add_step(wait_step("first", 0))
    assert len(recipe.steps) == 1


def test_recipe_serialization_contains_actions() -> None:
    recipe = Recipe(id="demo_recipe", name="Demo", steps=(wait_step("first", 0),))
    assert recipe.to_dict()["steps"][0]["action"]["action_type"] == "WAIT"


def test_empty_recipe_preserves_metadata() -> None:
    recipe = Recipe(id="empty_recipe", name="Empty", metadata={"owner": "test"})
    assert recipe.steps == ()
    assert recipe.to_dict()["metadata"] == {"owner": "test"}
