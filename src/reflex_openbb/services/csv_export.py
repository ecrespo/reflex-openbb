"""csv_export service (T-503).

REQ: REQ-008

Pure functions to convert Pydantic models to CSV strings. No I/O.
The page (or the export_button) calls these and then either:
- Writes to a file server-side (download)
- Streams via rx.download (client-side)

Functions:
- to_csv_bars(bars) — convert list[OHLCBar] to CSV
- to_csv_macro(points) — convert list[MacroPoint] to CSV
"""

from __future__ import annotations

import csv
import io

from reflex_openbb.data.types import MacroPoint, OHLCBar

__all__ = ["to_csv_bars", "to_csv_macro"]


def to_csv_bars(bars: list[OHLCBar]) -> str:
    """Convert a list of OHLCBar to a CSV string.

    The header is: date, open, high, low, close, volume.
    Decimal values are written as strings (preserving precision).
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "open", "high", "low", "close", "volume"])
    for bar in bars:
        writer.writerow(
            [
                bar.date.isoformat(),
                str(bar.open),
                str(bar.high),
                str(bar.low),
                str(bar.close),
                bar.volume,
            ]
        )
    return buf.getvalue()


def to_csv_macro(points: list[MacroPoint]) -> str:
    """Convert a list of MacroPoint to a CSV string.

    The header is: year, value, country, indicator.
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["year", "value", "country", "indicator"])
    for p in points:
        writer.writerow([p.year, str(p.value), p.country, p.indicator])
    return buf.getvalue()
