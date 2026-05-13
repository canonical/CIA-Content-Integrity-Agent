import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.app import create_app
from api.extensions import db as _db


class TestSettings:
    db_path = ""
    cors_origin = "http://localhost:5173"
    openrouter_api_key = ""
    openrouter_model = "openai/gpt-4o-mini"
    llm_temperature = 0.3
    auto_fix_threshold = 0.90
    notify_threshold = 0.60
    http_timeout = 15
    enable_llm = True
    cache_dir = ".cache"
    fixtures_dir = "fixtures"
    dry_run = True


@pytest.fixture(scope="function")
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    TestSettings.db_path = db_path
    app = create_app(settings=TestSettings())

    with app.app_context():
        _db.create_all()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db
