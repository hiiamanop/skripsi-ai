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

try:
    import chromadb  # noqa: F401
    import pypdf  # noqa: F401
    import prompt_toolkit  # noqa: F401
    import rich  # noqa: F401
except ImportError as e:
    venv = f"{ROOT}/.venv/bin/python"
    if os.path.exists(venv) and os.path.realpath(sys.prefix) != os.path.realpath(f"{ROOT}/.venv"):
        os.execv(venv, [venv, *sys.argv])  # pakai venv proyek, bukan python yang kebetulan aktif
    sys.exit(f"Dependensi belum terpasang ({e.name}). Jalankan:\n"
             f"  python -m venv .venv && .venv/bin/pip install -r requirements.txt")

import argparse  # noqa: E402

import agent  # noqa: E402
import config  # noqa: E402
import memory  # noqa: E402
import tui  # noqa: E402


def main():
    a = argparse.ArgumentParser()
    config.add_project_arg(a)
    a.add_argument("--resume", nargs="?", const=0, type=int, metavar="ID",
                   help="lanjutkan sesi terakhir, atau sesi ID")
    a.add_argument("--sesi", action="store_true", help="daftar sesi lalu keluar")
    a = a.parse_args()
    proj = config.project_from(a).ensure()
    mem = memory.Memory(proj)
    ui = tui.UI()

    if a.sesi:
        ui.sesi(mem.sessions())
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
    tools = agent.build_tools(proj, mem, sid, out=ui.show_result)
    ag = agent.Agent(mem, sid, tools, system, confirm=ui.confirm, history=history, on_tool=ui.tool_call)
    by_name = {t.name: t for t in tools}
    ask = tui.make_prompt(f"{proj.dir}/.history")
    ui.banner(proj, sid, len(history))
    try:
        while True:
            try:
                line = ask().strip()
            except EOFError:
                break
            if not line:
                continue
            handled = tui.handle_command(line, ui, proj, mem, by_name)
            if handled == "keluar":
                break
            if handled:
                continue
            try:
                ui.start_thinking()
                try:
                    reply = ag.turn(line)
                finally:
                    ui.stop_thinking()
            except KeyboardInterrupt:
                ui.notice("(dibatalkan)")
                continue
            except Exception as e:
                ui.error(f"gagal: {e}")
                continue
            if reply:
                ui.reply(reply)
    except KeyboardInterrupt:
        print()
    finally:
        try:
            ui.start_thinking()
            try:
                s = agent.summarize_session(mem, sid)
            finally:
                ui.stop_thinking()
            if s:
                ui.summary(s)
        except Exception as e:
            ui.notice(f"(ringkasan sesi gagal: {str(e)[:80]}; percakapan tetap tersimpan)")
        mem.close()


if __name__ == "__main__":
    main()
