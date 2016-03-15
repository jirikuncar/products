import pytest
from wtforms import Field
from wtforms.validators import ValidationError

from products import Category, Product, db, validate_categories


@pytest.mark.parametrize("categories", [
        ('Keyboards', 'Computers peripherals'),
        ('Keyboards', 'Mice'),
])
def test_invalid_category_pairs(app, categories):
    """Invalid pairs."""
    categories = Category.query.filter(Category.name.in_(categories)).values('id')
    field = Field()
    field.data = [str(c.id) for c in categories]

    with pytest.raises(ValidationError) as err:
        validate_categories(None, field)


@pytest.mark.parametrize("categories", [
        ('Keyboard', 'Wired'),
        ('Laser', 'Monitor'),
])
def test_valid_category_pairs(app, categories):
    """Valid pairs."""
    categories = Category.query.filter(Category.name.in_(categories)).values('id')
    field = Field()
    field.data = [str(c.id) for c in categories]

    validate_categories(None, field)
