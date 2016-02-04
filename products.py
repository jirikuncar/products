"""Simple product database."""

from flask import Flask, jsonify, request
from flask_cli import FlaskCLI
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/products.db'
app.config['SQLALCHEMY_ECHO'] = True
FlaskCLI(app)
db = SQLAlchemy(app)


class Product(db.Model):
    """Product information."""

    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class Retailer(db.Model):
    """Retailer information."""

    __tablename__ = 'retailer'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, index=True)


class ProductPrice(db.Model):
    """Information about product prices."""

    __tablename__ = 'product_price'

    product_id = db.Column(db.Integer, db.ForeignKey(Product.id), primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey(Retailer.id), primary_key=True)
    price = db.Column(db.Float)

    product = db.relationship(Product)
    retailer = db.relationship(Retailer)

    __table_args__ = (
        db.Index('idx_retailer_price', retailer_id, price),
    )


@app.route('/')
def index():
    """Return most expensive products."""
    query = ProductPrice.query.join(
        ProductPrice.product, ProductPrice.retailer
    ).order_by(
        db.desc(ProductPrice.price)
    )
    if request.args.get('retailer'):
        query = query.filter(Retailer.name.like(
            request.args.get('retailer') + '%'
        ))
    return jsonify(products=[
        {'product': p, 'retailer': r, 'price': pp} for p, r, pp in
        query.values(Product.name, Retailer.name, ProductPrice.price)
    ])



def populate():
    """Create demo data."""
    products = {'apple': 1, 'car': 8000, 'milk': 1.5, 'yogurt': 2}
    retailers = {'COOP': 1.1, 'Migros': 1, 'Aldi': 0.95}

    product_objs = {product: Product(name=product) for product in products.keys()}

    for retailer_name, coeficient in retailers.items():
        retailer = Retailer(name=retailer_name)
        for product, price in products.items():
            db.session.add(
                ProductPrice(
                    product=product_objs[product], retailer=retailer,
                    price=price*coeficient
                )
            )


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
