#!/usr/bin/env python3
"""Suggest which WhatsApp groups are job groups (where site walk videos land).

Reads WhatsApp's chat file read-only (a copy), scores every group, prints the ranking.
Only if you type yes does it write the suggested groups into the capture's save list,
then opens that list for checking. Nothing is saved from WhatsApp until the list is
checked and saved with Cmd + S.
"""
import os
import re
import shutil
import sys
import time

APP = os.path.expanduser("~/.gill-whatsapp")
sys.path.insert(0, APP)
try:
    import wa_capture as W
except ImportError:
    sys.exit("The capture is not installed in ~/.gill-whatsapp")

APPLE_EPOCH = 978307200
DAYS = 120
NEVER = re.compile(r"police|nsw ?pol|gun|range|firearm|jll|corrigo|family|mum|dad|kids|footy|wedding|"
                   r"birthday|bucks|hens|church|school mums|personal", re.I)
JOBBY = re.compile(r"\b(st|street|rd|road|ave|avenue|lane|ln|drive|dr|hwy|highway|parade|pde|pl|place|"
                   r"cres|crescent|blvd|way|tce|terrace|level|lvl|suite|shop|unit|site|job|jobs|fitout|fit out|"
                   r"reno|renovation|refurb|project|works|maintenance|make ?good|office|warehouse|building|"
                   r"tenancy|strata|repair|install|ceiling|partition|carpet|paint|glazing|joinery)\b", re.I)


def main():
    cfg = W.load_config()
    con, tmp = W.need_db()
    try:
        cutoff = time.time() - APPLE_EPOCH - DAYS * 86400
        rows = con.execute(
            "SELECT s.Z_PK, s.ZPARTNERNAME, s.ZCONTACTJID,"
            " SUM(CASE WHEN m.ZMESSAGETYPE=2 THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN m.ZMESSAGETYPE=2 AND m.ZISFROMME=1 THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN m.ZMESSAGETYPE=2 AND m.ZMESSAGEDATE>=? THEN 1 ELSE 0 END),"
            " SUM(CASE WHEN m.ZMESSAGETYPE IN (1,8) THEN 1 ELSE 0 END),"
            " COUNT(m.Z_PK), MAX(m.ZMESSAGEDATE)"
            " FROM ZWACHATSESSION s LEFT JOIN ZWAMESSAGE m ON m.ZCHATSESSION=s.Z_PK"
            " WHERE s.ZCONTACTJID LIKE '%g.us' GROUP BY s.Z_PK", (cutoff,)).fetchall()
    finally:
        con.close()
        shutil.rmtree(tmp, ignore_errors=True)

    scored = []
    for pk, name, jid, vids, my_vids, recent_vids, pics, msgs, last in rows:
        name = (name or jid or "").replace("\n", " ").strip()
        if not name:
            continue
        vids, my_vids, recent_vids, pics = vids or 0, my_vids or 0, recent_vids or 0, pics or 0
        why, score = [], 0
        if NEVER.search(name):
            verdict = "NEVER"
            why.append("never-save word in the name")
        else:
            if my_vids:
                score += 5 + min(my_vids, 10)
                why.append("%d video(s) James posted" % my_vids)
            if recent_vids:
                score += 3
                why.append("%d video(s) in the last %d days" % (recent_vids, DAYS))
            elif vids:
                score += 1
                why.append("%d older video(s)" % vids)
            if JOBBY.search(name):
                score += 3
                why.append("job-style name")
            if pics >= 5:
                score += 1
                why.append("%d photos/files" % pics)
            verdict = "JOB" if score >= 10 else ("MAYBE" if score >= 4 else "-")
        last_d = time.strftime("%Y-%m-%d", time.localtime(last + APPLE_EPOCH)) if last else ""
        scored.append((verdict, score, name, last_d, ", ".join(why)))

    order = {"JOB": 0, "MAYBE": 1, "NEVER": 3, "-": 2}
    scored.sort(key=lambda r: (order[r[0]], -r[1], r[2].lower()))
    shown = [r for r in scored if r[0] != "-"]
    print("\n%-6s %-5s %-11s %s" % ("", "SCORE", "LAST MSG", "GROUP  (why)"))
    for v, s, n, d, w in shown:
        print("%-6s %-5s %-11s %s  (%s)" % (v, s if v != "NEVER" else "", d, n, w))
    jobs = [r[2] for r in scored if r[0] == "JOB"]
    maybes = [r[2] for r in scored if r[0] == "MAYBE"]
    hidden = len(scored) - len(shown)
    print("\n%d JOB, %d MAYBE, %d never-save, %d other groups with no job signs (not shown)."
          % (len(jobs), len(maybes), sum(1 for r in scored if r[0] == "NEVER"), hidden))

    if not jobs and not maybes:
        print("No job groups found. Nothing changed.")
        return
    ans = input("\nType yes to put the JOB and MAYBE groups into the save list for checking (anything else = no): ")
    if ans.strip().lower() != "yes":
        print("Nothing changed.")
        return
    out = W.find_output_dir(cfg)
    os.makedirs(out, exist_ok=True)
    list_path = os.path.expanduser(cfg.get("LIST_PATH") or os.path.join(out, W.LIST_NAME))
    if os.path.exists(list_path):
        keep = os.path.join(APP, "Groups to save - before find_jobs %s.txt" % time.strftime("%Y%m%d-%H%M%S"))
        shutil.copy2(list_path, keep)
        print("Old list kept on this Mac: %s" % keep)
    with open(list_path, "w", encoding="utf-8") as f:
        f.write(W.LIST_HEAD)
        f.write("# Suggested by find_jobs. JOB groups first, then MAYBE. Delete any that are not jobs.\n\n")
        f.write("\n".join(jobs) + "\n")
        if maybes:
            f.write("\n# MAYBE - check these\n" + "\n".join(maybes) + "\n")
    print("Wrote %d groups to %s" % (len(jobs) + len(maybes), list_path))
    os.system('open -e "%s"' % list_path.replace('"', '\\"'))
    print("Check it in TextEdit: delete anything that is not a job, then Cmd + S.")


if __name__ == "__main__":
    main()
