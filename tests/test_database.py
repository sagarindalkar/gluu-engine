def test_database_init(app):
    from gluuengine.database import Database

    db = Database(app)
    assert db.app == app
