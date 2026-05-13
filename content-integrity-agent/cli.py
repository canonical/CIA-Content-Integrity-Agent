#!/usr/bin/env python3
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from models.schemas import PipelineState
from services.http_client import HTTPClient
from services.llm_client import LLMClient
from services.mock_google_doc_api import MockGoogleDocAPI
from services.mock_directory_api import MockDirectoryAPI
from services.sitemap_service import SitemapService
from services.google_doc_fetcher import GoogleDocFetcher
from agents.discovery import DiscoveryAgent
from agents.resolver import ResolverAgent
from agents.owner_resolver import OwnerResolverAgent
from agents.suggestion import SuggestionAgent
from agents.compliance import ComplianceAgent
from agents.confidence_router import RouterAgent
from agents.notifier import NotifierAgent
from agents.orchestrator import OrchestratorAgent

FIXTURE_MAP = {
    "https://canonical.com/data": "fixtures/pages/data.html",
    "https://canonical.com/kubernetes": "fixtures/pages/kubernetes.html",
    "https://canonical.com/microk8s": "fixtures/pages/microk8s.html",
    "https://canonical.com/openstack": "fixtures/pages/openstack.html",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Content Integrity Agent - Autonomous broken link detection and fix suggestions"
    )
    parser.add_argument(
        "--input", "-i",
        default="fixtures/linkchecker-output.txt",
        help="Path to linkchecker output file"
    )
    parser.add_argument(
        "--url",
        help="URL to check compliance against UX standards and style guide"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Print detailed agent logs"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not send notifications, just preview"
    )
    parser.add_argument(
        "--agent",
        choices=["discovery", "resolver", "owner", "suggestion", "router", "notifier", "all"],
        default="all",
        help="Run specific agent only"
    )
    return parser.parse_args()


def create_pipeline(input_path: str, verbose: bool = True, dry_run: bool = True,
                    settings: Settings = None, compliance_url: str = None) -> OrchestratorAgent:
    if settings is None:
        settings = Settings.from_env()

    http_client = HTTPClient()
    llm_client = LLMClient(api_key=settings.openrouter_api_key, model=settings.openrouter_model)
    doc_api = MockGoogleDocAPI()
    directory_api = MockDirectoryAPI()
    sitemap = SitemapService(http_client)

    agents = [
        DiscoveryAgent(input_path=input_path, verbose=verbose),
        ResolverAgent(http_client=http_client, verbose=verbose),
    ]

    if compliance_url and settings.google_service_account_info:
        fixture_path = FIXTURE_MAP.get(compliance_url, "")
        doc_fetcher = GoogleDocFetcher(
            service_account_info=settings.google_service_account_info,
            cache_ttl=settings.compliance_cache_ttl,
        )
        agents.append(ComplianceAgent(
            doc_fetcher=doc_fetcher,
            llm_client=llm_client,
            page_url=compliance_url,
            fixture_path=fixture_path,
            standard_doc_ids={
                "UX Standards": settings.ux_standards_doc_id,
                "Copy Style Guide": settings.copy_style_guide_doc_id,
            },
            verbose=verbose,
        ))

    agents.extend([
        OwnerResolverAgent(doc_api=doc_api, directory_api=directory_api, verbose=verbose),
        SuggestionAgent(http_client=http_client, llm_client=llm_client, sitemap=sitemap, verbose=verbose),
        RouterAgent(verbose=verbose),
        NotifierAgent(dry_run=dry_run or settings.dry_run, verbose=verbose),
    ])

    return OrchestratorAgent(agents=agents, verbose=verbose)


def main():
    args = parse_args()
    verbose = not args.quiet
    settings = Settings.from_env()

    if not os.path.exists(args.input):
        print(f"Input file not found: {args.input}")
        sys.exit(1)

    if verbose:
        print("Content Integrity Agent v0.1")
        print(f"   Input: {args.input}")
        print(f"   Dry run: {args.dry_run or settings.dry_run}")
        if args.url:
            print(f"   Compliance check: {args.url}")
        print()

    pipeline = create_pipeline(
        input_path=args.input,
        verbose=verbose,
        dry_run=args.dry_run,
        settings=settings,
        compliance_url=args.url,
    )
    state = PipelineState()
    pipeline.run(state)


if __name__ == "__main__":
    main()
