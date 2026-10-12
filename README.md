# moltrust-ads-example

An agent that manages Amazon Ads through the Amazon Ads MCP Server can change a daily
budget, a bid or a campaign state in one tool call. This example puts a check in front of
each of those calls: before your code sends the call to Amazon, it asks MolTrust whether
the change is inside the mandate your agency set for that ad account. The answer is allow,
hold (a person approves first) or forbid, with a record you can recompute yourself.

Your Amazon credentials stay in your process. MolTrust receives the tool name and the few
numbers the mandate limits (account ID, brand, budget, bid change), and never calls Amazon.

## Quickstart (about 10 minutes)

Python 3.10 or newer.

```bash
git clone https://github.com/MoltyCel/moltrust-ads-example
cd moltrust-ads-example
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# free API key (one ad account, 1,000 checks a month); shown once
curl -s -X POST https://api.moltrust.ch/auth/signup \
     -H 'Content-Type: application/json' -d '{"email": "you@agency.com"}'
export MOLTRUST_API_KEY=...      # the api_key from the answer

python quickstart.py
```

You can also get the key on <https://moltrust.ch/ads/pricing.html>.

Expected output, four calls against one mandate:

```
ALLOW   raise a daily budget to 150.00: call ran -> {...}
HOLD    raise a daily budget to 350.00: waits for approval (...)
FORBID  touch another client's campaign: budget_daily[CAMP-OTHER]: brand 'Another Client' not allowed
FORBID  grant a user access to the account: ... is not in the mandate
first verdicts received.
```

The `quickstart` workflow in this repository runs exactly these steps on a fresh GitHub
runner with a 10-minute limit.

## What to change

| File | What it holds |
|---|---|
| `profile.json` | The mandate: allowed tools, ad account IDs, brands, budget caps (in cents), hold threshold, bid limits, validity window |
| `my_ads_call.py` | Your own Amazon Ads MCP call. The guard runs it only after an allow or an approved hold |
| `quickstart.py` | `ACCOUNT_STATE` is your view of the account (current budgets and bids, brand per campaign). Take it from your own reporting, never from the model |

Values the guard cannot work out (an unknown campaign, a missing current bid) count as
unknown, and unknown ends in forbid.

## How a hold gets approved

Above `hold_threshold` the verdict is hold and the call does not run. A person named in
the mandate's `ratification_authorities` signs the approval; the guard sends it to
`POST /enforce/ratify` and runs the call only if the answer is RATIFIED. Pass an
`approver` to `AmazonAdsGuard` to wire this to your approval queue. The SDK README shows
the signature step: <https://github.com/MoltyCel/moltrust-api/tree/main/sdk/python>.

## Checking a decision later

Every check carries an AER record. `moltrust-verify` recomputes it offline, without the
MolTrust server:

```bash
moltrust-verify --input decision.json --trust-list trust.json
```

The encoding of the `ads` profile and the Amazon tool facts it rests on:
<https://github.com/MoltyCel/moltrust-api/blob/main/docs/spec-fakten/aae-ads-profile.md>.

## Limits

- The Amazon Ads MCP Server is in beta. Tool names come from Amazon's public tool schemas
  as of October 2026 and may change.
- MolTrust's kernel keeps no state. The current budgets, bids and the account's daily
  total come from your side; the guard trusts what you pass in `context`.
- The free tier covers one ad account. Pricing: <https://moltrust.ch/ads>.

MolTrust is an independent service provider and is not affiliated with or endorsed by
Amazon. Amazon Ads is a trademark of Amazon.com, Inc. or its affiliates.

Operated by CryptoKRI GmbH, Zurich, Switzerland. MIT licence.
