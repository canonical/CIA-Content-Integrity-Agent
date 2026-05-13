#!/usr/bin/env python3
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import PipelineState
from cli import create_pipeline
from config.settings import Settings


def test_pipeline():
    settings = Settings.from_env()
    settings.dry_run = True

    pipeline = create_pipeline(
        input_path="fixtures/linkchecker-output.txt",
        verbose=False,
        dry_run=True,
        settings=settings,
    )
    state = pipeline.run(PipelineState())

    assert len(state.failures) == 6, f"Expected 6 failures, got {len(state.failures)}"
    assert len(state.page_meta) == 4, f"Expected 4 page_meta, got {len(state.page_meta)}"
    assert len(state.owners) >= 3, f"Expected >=3 owners, got {len(state.owners)}"
    assert len(state.notifications) >= 1, f"Expected >=1 notification, got {len(state.notifications)}"

    for n in state.notifications:
        assert n.recipient.email, "Notification missing recipient email"
        assert n.subject, "Notification missing subject"
        assert n.body, "Notification missing body"

    assert len(state.audit_log) >= 6, f"Expected >=6 audit entries, got {len(state.audit_log)}"

    print("ALL E2E TESTS PASSED")


if __name__ == "__main__":
    test_pipeline()
