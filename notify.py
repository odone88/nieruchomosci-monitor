#!/usr/bin/env python3
"""
Powiadomienia o mega okazjach nieruchomości.
Windows toast notifications + logowanie.
"""

import json
import logging
import ctypes
import ctypes.wintypes
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "deals.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("notify")


def show_windows_toast(title: str, message: str):
    """Show a Windows toast notification using ctypes (MessageBox fallback)."""
    try:
        # Try win10toast first
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            title,
            message,
            duration=10,
            threaded=True,
        )
        return True
    except ImportError:
        pass

    # Fallback: Windows MessageBox (not a toast, but works everywhere)
    try:
        MB_OK = 0x0
        MB_ICONINFORMATION = 0x40
        MB_SYSTEMMODAL = 0x1000
        ctypes.windll.user32.MessageBoxW(
            0,
            message[:500],
            title,
            MB_OK | MB_ICONINFORMATION | MB_SYSTEMMODAL,
        )
        return True
    except Exception as e:
        log.error(f"Nie mogę wyświetlić powiadomienia Windows: {e}")
        return False


def send_notifications(deals: list[dict]):
    """Send notifications for great deals (>30% below market)."""
    if not deals:
        return

    log.info(f"=== POWIADOMIENIA: {len(deals)} mega okazji ===")

    for deal in deals[:5]:  # Max 5 notifications at once
        currency = "PLN"
        if deal.get("market") in ("barcelona", "lizbona"):
            currency = "EUR"

        title = f"OKAZJA: -{deal.get('discount_pct', 0):.0f}% | {deal.get('location', 'Nieznana')}"
        message = (
            f"{deal['title'][:60]}\n"
            f"Cena: {deal['price']:,.0f} {currency} | "
            f"{deal['area']:.0f} m² | {deal['price_m2']:,.0f} {currency}/m²\n"
            f"Rabat: {deal.get('discount_pct', 0):.0f}% poniżej rynku\n"
            f"Źródło: {deal['source'].upper()}"
        )

        log.info(f"  >> {title}")
        log.info(f"     {deal['url']}")

        # Only show toast if running interactively (not from scheduler in background)
        if sys.stdout.isatty():
            show_windows_toast(title, message)

    # Always log all great deals
    log.info(f"Szczegóły w deals.json i deals.html")


if __name__ == "__main__":
    # Test mode — load latest deals and notify
    deals_file = BASE_DIR / "deals.json"
    if deals_file.exists():
        with open(deals_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        great = [d for d in data.get("deals", []) if d.get("discount_pct", 0) >= 30]
        if great:
            send_notifications(great)
        else:
            log.info("Brak mega okazji do powiadomienia")
    else:
        log.info("Brak pliku deals.json — najpierw uruchom monitor.py")
