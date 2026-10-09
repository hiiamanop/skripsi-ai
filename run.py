#!/usr/bin/env python3
"""Research partner interaktif. Percakapan dan memori tersimpan di data/<proyek>/memory.db.

Pakai:  python run.py [-p proyek] [--resume [id]] [--sesi]
Ketik /keluar untuk selesai (ringkasan sesi dibuat otomatis).
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)  # .env dan ./data dibaca relatif ke root repo
sys.path.insert(0, f"{ROOT}/tools")

import argparse  # noqa: E402

import agent  # noqa: E402
import config  # noqa: E402
import memory  # noqa: E402


def confirm(text):
    return input(f"\n? {text} [y/N] ").strip().lower() in ("y", "ya")


def main():
    a = argparse.ArgumentParser()
    config.add_project_arg(a)
    a.add_argument("--resume", nargs="?", const=0, type=int, metavar="ID",
                   help="lanjutkan sesi terakhir, atau sesi ID")
    a.add_argument("--sesi", action="store_true", help="daftar sesi lalu keluar")
    a = a.parse_args()
    proj = config.project_from(a).ensure()
    mem = memory.Memory(proj)

    if a.sesi:
        for s in mem.sessions():
            print(f"#{s['id']} {s['started'][:16]} ({s['n']} pesan) {s['title']}\n    {s['summary']}")
        return

    sid, history = None, []
    if a.resume is not None:
        sid = a.resume or mem.last_session()
        if sid and mem.db.execute("select 1 from sessions where id=?", (sid,)).fetchone():
            history = agent.trim_history(mem.history(sid))
        else:
            sys.exit(f"sesi {a.resume or '(terakhir)'} tidak ada. Lihat: python run.py -p {proj.name} --sesi")
    sid = sid or mem.new_session()

    wm = mem.working_memory()
    system = agent.SYSTEM + (f"\n\nMEMORI PROYEK '{proj.name}':\n{wm}" if wm else "")
    ag = agent.Agent(mem, sid, agent.build_tools(proj, mem, sid), system, confirm=confirm, history=history)
    print(f"Proyek '{proj.name}', sesi #{sid}" + (f" (dilanjutkan, {len(history)} pesan dimuat)" if history else "")
          + ". Ketik /keluar untuk selesai.")
    try:
        while True:
            try:
                line = input("\nanda> ").strip()
            except EOFError:
                break
            if not line:
                continue
            if line in ("/keluar", "/exit", "exit"):
                break
            try:
                reply = ag.turn(line)
            except KeyboardInterrupt:
                print("\n(dibatalkan)")
                continue
            except Exception as e:
                print(f"gagal: {e}")
                continue
            if reply:
                print(f"\n{reply}")
    except KeyboardInterrupt:
        print()
    finally:
        try:
            s = agent.summarize_session(mem, sid)
            print(f"\nRingkasan sesi tersimpan: {s}" if s else "")
        except Exception as e:
            print(f"\n(ringkasan sesi gagal: {str(e)[:80]}; percakapan tetap tersimpan)")
        mem.close()


if __name__ == "__main__":
    main()
