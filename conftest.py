import pytest

@pytest.fixture
def app(request):
    """Initialize application."""
    from products import app as _app, db, populate
    with _app.app_context():
        db.create_all()

    populate()
    db.session.commit()

    def teardown():
        with _app.app_context():
            db.drop_all()

    request.addfinalizer(teardown)
    return _app
