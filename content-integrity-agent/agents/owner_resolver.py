"""
OwnerResolverAgent: Resolves copydoc URLs → Google Doc body → table Page Owner → Directory user.
"""
from agents.base import BaseAgent
from models.schemas import PipelineState, Owner
from utils.table_parser import find_table_in_body, extract_page_owners_from_table


class OwnerResolverAgent(BaseAgent):
    """Looks up page owners via copydoc → Google Doc → Directory API chain."""

    def __init__(self, doc_api, directory_api, verbose: bool = True):
        super().__init__("OwnerResolver", verbose)
        self.doc_api = doc_api
        self.directory = directory_api

    def _resolve_owner_email(self, copydoc_url: str) -> str:
        try:
            doc_info = self.doc_api.get_document_info(copydoc_url)
        except Exception:
            self.log(f"Doc API failed for {copydoc_url}")
            return ""

        direct_owner = doc_info.get("owner_email")
        if direct_owner:
            return direct_owner

        body = doc_info.get("body")
        if not body:
            self.log(f"Doc {copydoc_url} has no body")
            return ""

        table = find_table_in_body(body)
        if not table:
            self.log(f"No table found in doc {copydoc_url}")
            return ""

        owners = extract_page_owners_from_table(table)
        if not owners:
            self.log(f"No Page Owner row found in table")
            return ""

        emails = [p["email"] for p in owners]
        self.log(f"Table owners: {emails}")
        return emails[0]

    def run(self, state: PipelineState) -> PipelineState:
        for url, meta in state.page_meta.items():
            copydoc_url = meta.copydoc_url
            if not copydoc_url:
                self.log(f"No copydoc for {url}, skipping")
                continue

            owner_email = self._resolve_owner_email(copydoc_url)
            if not owner_email:
                self.log(f"No owner found for {copydoc_url}, falling back to ops-team")
                owner_email = "ops-team@canonical.com"

            try:
                user = self.directory.lookup_user(owner_email)
            except Exception:
                user = {}

            if not user:
                self.log(f"Directory lookup failed for {owner_email}")
                user = self.directory.lookup_user("ops-team@canonical.com")

            owner = Owner(
                email=user.get("email", owner_email),
                display_name=user.get("display_name", owner_email),
                team=user.get("team", ""),
                department=user.get("department", ""),
                mattermost_username=user.get("mattermost_username"),
            )
            state.owners[url] = owner
            meta.page_owner_email = user.get("email", owner_email)
            state.page_meta[url] = meta

            self.log(f"{url} → {owner.display_name} <{owner.email}>")

        self.log(f"Resolved {len(state.owners)} owner(s)")
        state.log("OwnerResolver", "RESOLVE",
                   f"pages={len(state.page_meta)}",
                   f"owners={len(state.owners)}")
        return state
