"""Quickstart: put a MolTrust verdict in front of your agent's Amazon Ads calls.

    python -m venv .venv && . .venv/bin/activate
    pip install -r requirements.txt
    python quickstart.py

The script creates an agency key on first run (agency_key.hex, keep it private), builds a
mandate from profile.json and asks api.moltrust.ch for verdicts on four tool calls. The
Amazon call itself is `my_ads_call.py`: a stub until you plug in your own MCP client.
Nothing here sends anything to Amazon, and MolTrust never sees an Amazon credential.

Set MOLTRUST_API_KEY to use your key; without it the script identifies by the agency DID.
"""
import json
import os
import pathlib
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from moltrust_enforce import EnforceClient
from moltrust_enforce.adapters.amazon_ads import (
    DOCUMENTED_TOOLS, AdsProfile, AmazonAdsGuard, Forbidden, HoldRequired)

from my_ads_call import my_ads_call

HERE = pathlib.Path(__file__).resolve().parent
KEY_FILE = HERE / "agency_key.hex"


def agency_key():
    if not KEY_FILE.exists():
        KEY_FILE.write_text(Ed25519PrivateKey.generate().private_bytes_raw().hex() + "\n")
        KEY_FILE.chmod(0o600)
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(KEY_FILE.read_text().strip()))


def agency_did(key):
    # A local identifier for this example. Register a real one at https://moltrust.ch.
    return "did:moltrust:" + key.public_key().public_bytes_raw()[:8].hex()


def load_profile(key):
    cfg = json.loads((HERE / "profile.json").read_text())
    tools = {t: DOCUMENTED_TOOLS[t] for t in cfg.pop("tools")}
    return AdsProfile(
        principal={"did": agency_did(key),
                   "public_key": key.public_key().public_bytes_raw().hex()},
        tools=tools, account_ids=tuple(cfg.pop("account_ids")),
        brands=tuple(cfg.pop("brands")), **cfg)


def budget(campaign, value):
    return {"body": {"accessRequestedAccount": {"advertiserAccountId": "ENTITY1EXAMPLE"},
                     "campaigns": [{"campaignId": campaign, "budgets": [{
                         "budgetType": "MONETARY", "recurrenceTimePeriod": "DAILY",
                         "budgetValue": {"monetaryBudgetValue": {
                             "monetaryBudget": {"value": value}}}}]}]}}


# Your own view of the account, from your reporting store. Never from the model.
ACCOUNT_STATE = {
    "campaigns": {"CAMP-1": {"brand": "Example Brand", "daily_budget": 10_000},
                  "CAMP-OTHER": {"brand": "Another Client", "daily_budget": 10_000}},
    "account_daily_total": 20_000,
}

CALLS = [
    ("raise a daily budget to 150.00", "campaign_management-update_campaign_budget",
     budget("CAMP-1", 150.0)),
    ("raise a daily budget to 350.00", "campaign_management-update_campaign_budget",
     budget("CAMP-1", 350.0)),
    ("touch another client's campaign", "campaign_management-update_campaign_budget",
     budget("CAMP-OTHER", 50.0)),
    ("grant a user access to the account", "user_permissions-update_user_permissions",
     {"body": {"accessRequestedAccount": {"advertiserAccountId": "ENTITY1EXAMPLE"},
               "userPermissions": []}}),
]


def main():
    key = agency_key()
    base = os.environ.get("MOLTRUST_URL", "https://api.moltrust.ch")
    api_key = os.environ.get("MOLTRUST_API_KEY")
    client = (EnforceClient(base, api_key=api_key) if api_key
              else EnforceClient(base, did=agency_did(key)))
    guard = AmazonAdsGuard(client, load_profile(key))

    print(f"agency {agency_did(key)} -> {base}\n")
    seen = set()
    for label, tool, args in CALLS:
        try:
            out = guard.call(tool, args, my_ads_call, context=ACCOUNT_STATE)
            line = f"ALLOW   {label}: call ran -> {out.result}"
        except HoldRequired as e:
            out = e.outcome
            line = f"HOLD    {label}: waits for approval ({out.reason})"
        except Forbidden as e:
            out = e.outcome
            line = f"FORBID  {label}: {out.reason}"
        seen.add(out.disposition)
        print(line)
        digest = out.checks[0].verdict.core_digest
        print(f"        record {digest}\n" if digest else "        no server record\n")
    ok = seen == {"allow", "hold", "forbid"}
    print("first verdicts received." if ok else "unexpected verdicts, see above.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
