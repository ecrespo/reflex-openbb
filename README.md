# reflex-openbb

> Open-source OpenBB UI in pure Python (Reflex). Equity / Crypto / Economy dashboards consuming the `openbb` SDK.

**Status:** WIP — see the spec kit in [`specs/`](./specs/) for the full design and tasks.

## Why

[OpenBB Pro](https://pro.openbb.co/) (the official UI) is closed-source SaaS. The
[OpenBB Python SDK](https://github.com/OpenBB-finance/OpenBB) is open-source but
has no first-class UI. This project is a polished open-source alternative,
written in pure Python, that consumes the OpenBB SDK and reuses
[ecrespo's catalog of 22 Reflex custom components](https://github.com/ecrespo).

## Install

```bash
pip install reflex-openbb
```

(Not on PyPI yet — v0.1.0 is the first release target.)

## Quickstart

```bash
reflex-openbb
# Opens http://localhost:3000
```

## License

Apache-2.0.
