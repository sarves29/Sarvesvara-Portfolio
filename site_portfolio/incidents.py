"""Static incident data for the hero scroll-theater.

Each step is rendered as a pinned frame; scroll progress advances the active index.
Keep to 6 steps — fewer is thin, more is tiresome.

Source: real PLOS incident, resolved 2026-03 (commit c8cd8ee).
"""

INCIDENT = {
    "slug": "plos-silent-404s-2026-03",
    "title": "PLOS · a ? became a %3F",
    "subtitle": "Half the mobile app rendered empty. Every dashboard said green. One character broke nine providers.",
    "date": "2026-03-18",
    "system": "PLOS Flutter client",
    "severity": "PROD · SEV-2",
    "owner": "Sarvesvara",
    "duration_minutes": 133,
    "nameplate": {
        "role": "FULL-STACK · PRODUCT",
        "name": "SARVESVARA · RAMAR",
        "meta": "CHENNAI · ships and owns it",
    },
    "steps": [
        {
            "idx": 0,
            "time": "11:42",
            "phase": "paged",
            "label": "User reports",
            "headline": "“dashboard shows nothing. finance, mood, health — all zero.”",
            "artifact": {
                "type": "alert",
                "channel": "#plos-alpha",
                "author": "alpha-tester",
                "lines": [
                    "dashboard shows nothing. finance, mood, health — all zero.",
                    "no error though. just empty cards where numbers should be.",
                    "tried pull-to-refresh. same.",
                    "opened a second account. same thing.",
                ],
            },
            "note": "My first instinct was an API outage. Backend was green.",
        },
        {
            "idx": 1,
            "time": "11:55",
            "phase": "observe",
            "label": "Backend green, client blank",
            "headline": "Every /api/* is a 200. The client says empty anyway.",
            "artifact": {
                "type": "reasoning",
                "bullets": [
                    "Backend access log: /api/* → 200 on every endpoint, no spikes, no 5xx",
                    "Mobile screens rendering 'no data' on 5 of 7 dashboards",
                    "List-view endpoints (days=30, limit=50) broken · detail endpoints fine",
                    "No exception dialogs, no Sentry crashes · silent zero-state everywhere",
                ],
            },
            "note": "This was the worst kind of failure: the app was lying to the user, and so was the observability stack.",
        },
        {
            "idx": 2,
            "time": "12:30",
            "phase": "diagnose",
            "label": "Wrong theory, 40 min spent",
            "headline": "I blamed the serializers. They were fine.",
            "artifact": {
                "type": "log",
                "caption": "pytest · re-verifying every API response contract",
                "lines": [
                    "$ pytest tests/api/contracts/ -q",
                    "125 passed in 4.82s",
                    "",
                    "$ curl -s api.plos/api/finance/summary?days=30 | jq .total",
                    "142580",
                    "",
                    "$ curl -s api.plos/api/mood/entries?limit=50 | jq 'length'",
                    "47",
                    "",
                    "# backend is handing back correct data on every request it sees.",
                    "# so why isn't the client seeing it?",
                ],
            },
            "note": "Forty minutes defending a backend that wasn't on trial.",
        },
        {
            "idx": 3,
            "time": "13:15",
            "phase": "root_cause",
            "label": "The client was never asking",
            "headline": "Dart's Uri(path:) percent-encoded every ? into %3F.",
            "artifact": {
                "type": "reasoning",
                "bullets": [
                    "Proxied the device: real requests were `/api/finance/summary%3Fdays=30`",
                    "Dart's Uri(path: '...') treats `?` as a reserved char and percent-encodes it",
                    "Every query-parameterized call became a 404 the backend never saw",
                    "9 providers × ~20 call sites, all made the same wrong assumption",
                    "The 404s lived only in nginx access log — never in Django, never in Sentry",
                ],
            },
            "note": "The whole investigation flipped in ninety seconds.",
        },
        {
            "idx": 4,
            "time": "13:41",
            "phase": "fix",
            "label": "Ten lines. Twenty call sites.",
            "headline": "Split path and query properly. Once. Everywhere.",
            "artifact": {
                "type": "diff",
                "file": "lib/api/api_client.dart",
                "lines": [
                    {"kind": "ctx", "text": "Uri _uri(String endpoint) {"},
                    {"kind": "del", "text": "  return Uri(path: endpoint);"},
                    {"kind": "add", "text": "  final parts = endpoint.split('?');"},
                    {"kind": "add", "text": "  final query = parts.length > 1"},
                    {"kind": "add", "text": "      ? Uri.splitQueryString(parts.last)"},
                    {"kind": "add", "text": "      : null;"},
                    {"kind": "add", "text": "  return Uri("},
                    {"kind": "add", "text": "    path: parts.first,"},
                    {"kind": "add", "text": "    queryParameters: query,"},
                    {"kind": "add", "text": "  );"},
                    {"kind": "ctx", "text": "}"},
                ],
            },
            "note": "Ten lines. Four months of dormant silent failures.",
        },
        {
            "idx": 5,
            "time": "13:55",
            "phase": "resolved",
            "label": "404 rate flat to zero",
            "headline": "Dashboards repopulated the moment users pulled to refresh.",
            "artifact": {
                "type": "metric",
                "caption": "/api/* 404 rate · 10-minute window after deploy",
                "unit": "% of req",
                "series": [
                    {"name": "404 rate", "color": "#FF4D1C", "values": [71, 70, 68, 64, 52, 34, 18, 9, 4, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]},
                    {"name": "success %", "color": "#0E0E0E", "values": [29, 30, 32, 36, 48, 66, 82, 91, 96, 98, 99, 99, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100]},
                ],
            },
            "note": "The test harness now captures every /api/* response code per screen. This class of bug cannot hide again.",
        },
    ],
    "coda": {
        "takeaway": "Silent 404s are worse than 500s. A single encoded character broke half a product, and every dashboard kept saying green.",
        "stack": ["Flutter", "Dart", "Django", "nginx", "pytest", "Uri", "observability"],
    },
}
