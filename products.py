"""Simple product database."""

from flask import Flask, jsonify, request, render_template, redirect
from flask_admin import Admin
from flask_cli import FlaskCLI
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import joinedload
from werkzeug.local import LocalProxy
from wtforms import StringField, DecimalField, SelectMultipleField
from wtforms.validators import DataRequired, ValidationError


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/products.db'
# app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'CHANGEME'
FlaskCLI(app)
db = SQLAlchemy(app)


class Category(db.Model):
    """Category."""

    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'),
                          nullable=True)

    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

    @classmethod
    def fixture(cls, name, children):
        """Create category from a fixture."""
        obj = Category(name=name)
        children = children or {}
        for key, values in children.items():
            obj.children.append(cls.fixture(key, values))
        return obj


def category_creator(value):
    """Find correct category."""
    return ProductCategories(category_id=int(value))


class Product(db.Model):
    """Product information."""

    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    manufacturer = db.Column(db.String)
    ean = db.Column(db.String)
    price = db.Column(db.Float, nullable=False)

    categories = association_proxy('product_categories', 'category',
                                   creator=category_creator)


class ProductCategories(db.Model):
    """Store information about product categories."""

    __tablename__ = 'product_category'

    product_id = db.Column(
        db.Integer, db.ForeignKey(Product.id), primary_key=True
    )
    category_id = db.Column(
        db.Integer, db.ForeignKey(Category.id), primary_key=True
    )

    product = db.relationship(Product, backref=db.backref('product_categories'))
    category = db.relationship(Category)


def validate_categories(form, field):
    """Validate selected categories."""
    category_ids = set([int(id_) for id_ in field.data])
    for category in Category.query.filter(Category.id.in_(category_ids),
                                          Category.parent_id.isnot(None)).all():
        # Check only categories with a parent
        direct_siblings_ids = set(c.id for c in category.parent.children)
        invalid_ids = category_ids & (
            direct_siblings_ids | set([category.parent.id])
        ) - set([category.id])
        if invalid_ids:
            raise ValidationError("Category '{0}' can not be included.".format(category.name))


class ProductForm(Form):
    """Define validation for a product."""

    name = StringField('name', validators=[DataRequired()])
    manufacturer = StringField('manufacturer')
    ean = StringField('ean')
    price = DecimalField('price', validators=[DataRequired()])

    categories = SelectMultipleField('categories', choices=LocalProxy(lambda: [
        (str(c.id), c.name) for c in Category.query.all()
    ]), validators=[DataRequired(), validate_categories])


@app.route('/')
def index():
    """Return most expensive products."""
    return render_template(
        'index.html',
        products=Product.query.all(),
        categories=Category.query.filter(
            Category.parent_id.is_(None)
        ).all(),
    )

@app.route('/add', methods=['GET', 'POST'])
def add():
    """Add new product."""
    form = ProductForm()
    if form.validate_on_submit():
        db.session.add(Product(**form.data))
        db.session.commit()
        return redirect('/')
    return render_template('add.html', form=form)


@app.route('/edit/<product_id>', methods=['GET', 'POST'])
def edit(product_id):
    """Edit a product."""
    product = Product.query.get(product_id)
    form = ProductForm(request.form, obj=product)
    if form.validate_on_submit():
        product.update(**form.data)
        db.session.commit()
        return redirect('/')
    return render_template('edit.html', form=form)


@app.route('/delete/<product_id>')
def delete(product_id):
    """Delete a product."""
    Product.query.filter_by(id=product_id).delete()
    db.session.commit()
    return redirect('/')


def populate():
    """Create demo data."""
    categories = {
        'Electronics': {
            'TV sets': None,
            'Radios': None,
            'Alarm systems': None,
            'Cameras': {
                'SLRD': None,
                'Point and shoot': None,
            },
        },
        'Computers': {
            'Desktops': {
                'Accessories': None,
            },
            'Servers': None,
            'Computers peripherals': {
                'Mice': {
                    'Wired': None,
                    'Cordless': None,
                },
                'Keyboards': None,
                'Monitors': None,
                'Printers': {
                    'Laser': None,
                    'Inkjet': None,
                },
            },
        },
    }

    for name, children in categories.items():
        db.session.add(Category.fixture(name, children))


@app.cli.command()
def init():
    """Lazy initialization."""
    try:
        db.drop_all()
    except:
        pass

    db.create_all()
    populate()
    db.session.commit()
