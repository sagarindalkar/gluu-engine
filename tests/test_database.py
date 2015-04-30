def test_database_init(app):
    from gluuapi.database import Database

    db = Database(app)
    assert db.app == app
