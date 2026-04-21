"""
En çok kullanılan nView'ları (kbindb.node tablosunda) listeler — tek seferlik yardımcı.
generate_nview_skills.py bu listeyi girdi olarak kullanır.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "mcps" / "scada" / "src"))

from scada_mcp.config import load_instance  # noqa: E402
from scada_mcp import db as dbmod  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--instance",
        default="korubin_main",
        help="instances/ altındaki isim (default: korubin_main)",
    )
    ap.add_argument("--top", type=int, default=60)
    ap.add_argument(
        "--require-common",
        default="//10.10.10.72/public/dev.korubin/app/views/point/display/common",
        help="Bu path altında <nView>/GENEL.phtml olan nView'ları işaretle",
    )
    args = ap.parse_args(argv)

    inst_dir = ROOT / "mcps" / "scada" / "instances" / args.instance
    cfg = load_instance(inst_dir)
    if not cfg.db:
        print("DB config yok", file=sys.stderr)
        return 2
    common_root = Path(args.require_common) if args.require_common else None
    with dbmod.connect(cfg.db) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COALESCE(nView, '') AS nv, COUNT(*) AS c
                FROM kbindb.node
                WHERE nState IN (-1, 0, 1, 100) AND nView IS NOT NULL AND nView <> ''
                GROUP BY nView
                ORDER BY c DESC
                LIMIT %s
                """,
                (int(args.top),),
            )
            rows = list(cur.fetchall())

    print(f"{'nView':<40}  {'count':>6}  has_genel  has_ui_settings")
    for r in rows:
        nv = str(r["nv"])
        c = int(r["c"])
        has_genel = False
        has_ui = False
        if common_root and common_root.is_dir():
            p = common_root / nv
            has_genel = (p / "GENEL.phtml").is_file()
            has_ui = (p / "uisettings.phtml").is_file()
        print(f"{nv:<40}  {c:>6}  {'Y' if has_genel else '-':>9}  {'Y' if has_ui else '-':>15}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
