"""
Targeted price refresher — fetches current prices from autovit.ro for stale DB listings.

Usage:
    # Refresh one specific listing by URL
    python refresh_prices.py --url "https://www.autovit.ro/autoturisme/anunt/..."

    # Refresh all active listings not seen in the last N days (default 3)
    python refresh_prices.py --days 3

    # Dry run (print what would change, don't write)
    python refresh_prices.py --days 3 --dry-run

Run from backend/: python refresh_prices.py
"""
import argparse
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent / "cars.db"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:144.0) Gecko/20100101 Firefox/144.0",
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
}


def fetch_price(url: str, session: requests.Session) -> float | None:
    """Return current EUR price from an autovit listing page, or None."""
    try:
        resp = session.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  FETCH ERROR: {e}")
        return None

    soup = BeautifulSoup(resp.content, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if not script or not script.string:
        print("  No __NEXT_DATA__ — listing may be removed")
        return None

    try:
        page_data = json.loads(script.string)
        advert = page_data["props"]["pageProps"]["advert"]
    except (json.JSONDecodeError, KeyError, TypeError):
        print("  Failed to parse __NEXT_DATA__")
        return None

    price_info = advert.get("price", {})
    if not isinstance(price_info, dict) or price_info.get("currency", "").upper() != "EUR":
        print("  Price not in EUR or missing")
        return None

    val = price_info.get("value")
    return float(val) if val else None


def get_stale_listings(conn: sqlite3.Connection, days: int) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    cur = conn.execute(
        """
        SELECT id, source_url, price, last_seen
        FROM cars
        WHERE status = 'active'
          AND source_url IS NOT NULL
          AND source_url LIKE 'https://www.autovit.ro/%'
          AND (last_seen IS NULL OR last_seen < ?)
        ORDER BY last_seen ASC
        """,
        (cutoff.isoformat(),),
    )
    return [{"id": r[0], "url": r[1], "price": r[2], "last_seen": r[3]} for r in cur.fetchall()]


def update_car(conn: sqlite3.Connection, car_id: int, new_price: float, old_price: float) -> None:
    now = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO price_history (car_id, old_price, new_price, changed_at) VALUES (?,?,?,?)",
        (car_id, old_price, new_price, now),
    )
    conn.execute(
        "UPDATE cars SET price=?, last_seen=? WHERE id=?",
        (new_price, now, car_id),
    )
    conn.commit()


def mark_seen(conn: sqlite3.Connection, car_id: int) -> None:
    conn.execute("UPDATE cars SET last_seen=? WHERE id=?", (datetime.utcnow().isoformat(), car_id))
    conn.commit()


def run(urls: list[str] | None, days: int, dry_run: bool) -> None:
    conn = sqlite3.connect(DB_PATH)

    if urls:
        listings = []
        for u in urls:
            cur = conn.execute(
                "SELECT id, price, last_seen FROM cars WHERE source_url=? AND status='active'",
                (u,),
            )
            row = cur.fetchone()
            if row:
                listings.append({"id": row[0], "url": u, "price": row[1], "last_seen": row[2]})
            else:
                print(f"Not found in DB (or not active): {u}")
    else:
        listings = get_stale_listings(conn, days)

    print(f"Listings to refresh: {len(listings)}")
    if not listings:
        conn.close()
        return

    session = requests.Session()
    changed = 0
    removed = 0
    unchanged = 0

    for car in listings:
        print(f"\n[{car['id']}] {car['url']}")
        print(f"  DB price: EUR {car['price']:,.0f}  |  last_seen: {car['last_seen']}")

        new_price = fetch_price(car["url"], session)

        if new_price is None:
            print("  -> Could not fetch price (listing may be gone)")
            removed += 1
        elif abs(new_price - car["price"]) < 0.01:
            print(f"  -> Price unchanged: EUR {new_price:,.0f}")
            if not dry_run:
                mark_seen(conn, car["id"])
            unchanged += 1
        else:
            direction = "DOWN" if new_price < car["price"] else "UP"
            diff = abs(new_price - car["price"])
            print(f"  -> Price {direction}: EUR {car['price']:,.0f} -> EUR {new_price:,.0f}  (diff: EUR {diff:,.0f})")
            if not dry_run:
                update_car(conn, car["id"], new_price, car["price"])
            changed += 1

        time.sleep(0.8)

    conn.close()
    tag = " [DRY RUN]" if dry_run else ""
    print(f"\nDone{tag}: {changed} updated, {unchanged} unchanged, {removed} unreachable")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", nargs="+", help="One or more specific autovit URLs to refresh")
    parser.add_argument("--days", type=int, default=3, help="Refresh listings not seen in N days")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args()

    run(urls=args.url, days=args.days, dry_run=args.dry_run)
