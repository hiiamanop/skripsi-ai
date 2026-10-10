#!/usr/bin/env python3
"""Research partner interaktif. Percakapan dan memori tersimpan di data/<proyek>/memory.db,
di folder tempat perintah dijalankan.

Pakai:  skripsi-ai [-p proyek] [--resume [id]] [--sesi]
Ketik /keluar untuk selesai (ringkasan sesi dibuat otomatis).
"""
import argparse
import sys

from . import agent, config, memory, tui



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
            sys.exit(f"sesi {a.resume or '(terakhir)'} tidak ada. Lihat: skripsi-ai -p {proj.name} --sesi")
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
