#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💬 溝通達人訓練營（Sample）
模擬聊天 + 評分 + 技巧教學 | 進度 1% → 100% | Streamlit + Silra AI
"""
import os, re, json
import streamlit as st

def _sk(key, default=""):
    try:
        v = st.secrets.get(key)
        return v if v not in (None, "") else default
    except Exception:
        return default

def _get_api_key():
    for name in ("OPENAI_API_KEY", "SILRA_API_KEY", "API_KEY", "AI", "KEY"):
        v = _sk(name, "")
        if v:
            return v
    return ""

st.set_page_config(page_title="💬 溝通達人訓練營", page_icon="💬", layout="wide")

LEVELS = [
    {"id": 1, "title": "破冰問好", "scenario": "你喺學校活動第一次見到一位同學（阿晴），想同佢傾偈。",
     "skill": "禮貌開場＋自然問好，唔好太刻意"},
    {"id": 2, "title": "開放式問題", "scenario": "阿晴話佢中意睇電影，你想傾落去。",
     "skill": "問「點解/邊套/覺得點」呢類開放式問題，唔好問到冇得答"},
    {"id": 3, "title": "聆聽與回應", "scenario": "阿晴講緊佢隻貓嘅趣事。",
     "skill": "回應佢講過嘅內容＋問跟進問題，表示你有留心聽"},
    {"id": 4, "title": "真誠稱讚", "scenario": "阿晴啱啱贏咗校際朗誦比賽。",
     "skill": "稱讚要具體（讚努力/表現），唔好太浮誇"},
    {"id": 5, "title": "溫和幽默", "scenario": "落雨，你哋一齊被困喺小食部門口。",
     "skill": "輕鬆自嘲或情境幽默，唔好講笑話取笑人"},
    {"id": 6, "title": "分享自己", "scenario": "阿晴問你平時中意做乜。",
     "skill": "適量分享＋反問，保持對話雙向"},
    {"id": 7, "title": "禮貌收尾", "scenario": "要走喇，想下次再傾。",
     "skill": "自然結束＋留個下次見面嘅引子，唔好太急"},
]

st.title("💬 溝通達人訓練營")
st.caption("學習禮貌・聆聽・問問題・真誠表達｜每次模擬對話都有評分同建議")

with st.sidebar:
    st.header("📈 學習進度")
    done = st.session_state.setdefault("done_levels", set())
    pct = int(len(done) / len(LEVELS) * 100)
    st.progress(pct / 100, text=f"進度：{max(pct, 1)}%")
    st.caption("每完成一個關卡 +14% 左右，全部完成 = 100% 🏆")
    st.divider()
    api_ok = bool(_get_api_key())
    st.write("AI 對戰：" + ("✅ 已啟用" if api_ok else "⚠️ 未設 API Key（用練習模式）"))
    st.caption("💡 小提醒：好溝通 = 尊重＋聆聽＋真誠")

level = st.selectbox("揀關卡", LEVELS, format_func=lambda l: f"第 {l['id']} 關｜{l['title']}")
st.info(f"**情境**：{level['scenario']}\n\n**今關技巧**：{level['skill']}")

if "chat" not in st.session_state or st.session_state.get("chat_level") != level["id"]:
    st.session_state["chat"] = [{"role": "ai", "text": f"（{level['title']}）{level['scenario']} 你好呀 👋"}]
    st.session_state["chat_level"] = level["id"]

def ai_turn(history, skill):
    api_key = _get_api_key()
    if not api_key:
        return ("（練習模式）呢個係你練習嘅機會：試吓用今關技巧寫一句回覆，"
                "然後自我檢查：有冇禮貌？有冇問返對方？內容係咪具體？"), None
    import requests
    url = _sk("SILRA_API_URL", "https://api.silra.cn/v1/chat/completions")
    model = _sk("MODEL_NAME", "qwen3.8-flash")
    convo = "\n".join(f"{'對方' if m['role']=='ai' else '你'}：{m['text']}" for m in history[-8:])
    prompt = (
        "你係「溝通達人訓練營」教練兼對話角色（一位友善嘅同學）。用粵語口語。\n"
        f"今關訓練技巧：{skill}\n"
        f"對話記錄：\n{convo}\n\n"
        "請做三件事（嚴格 JSON）：\n"
        "1. 以同學身份自然回應一句（role_reply，30 字內，保持友善輕鬆）\n"
        "2. 給用戶剛才嘅說話評分 0-10（score）＋一句評語（comment）\n"
        "3. 給一個更好嘅示範回覆（better，40 字內）＋一個要點（tip）\n"
        "只回傳 JSON：{\"role_reply\":\"...\",\"score\":8,\"comment\":\"...\",\"better\":\"...\",\"tip\":\"...\"}\n"
        "評分標準：禮貌、內容具體、有問返對方、貼合今關技巧。"
    )
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                          json={"model": model, "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.8}, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", content, re.S)
        return None, json.loads(m.group(0))
    except Exception as e:
        return f"AI 連線問題：{e}", None

for m in st.session_state["chat"]:
    if m["role"] == "ai":
        st.chat_message("assistant", avatar="🧑").write(m["text"])
    else:
        st.chat_message("user", avatar="🙂").write(m["text"])
    if "score" in m:
        st.chat_message("assistant", avatar="📊").markdown(
            f"**評分：{m['score']}/10** — {m['comment']}\n\n"
            f"💡 **更好示範**：{m['better']}\n\n📌 **要點**：{m['tip']}")

user_input = st.chat_input("寫你嘅回覆…")
if user_input:
    st.session_state["chat"].append({"role": "user", "text": user_input})
    err, data = ai_turn(st.session_state["chat"], level["skill"])
    if data:
        st.session_state["chat"].append({
            "role": "ai", "text": data.get("role_reply", "…"),
            "score": data.get("score", 0), "comment": data.get("comment", ""),
            "better": data.get("better", ""), "tip": data.get("tip", "")})
    else:
        st.session_state["chat"].append({"role": "ai", "text": err or "（練習模式）試吓自我評分！"})
    if len([m for m in st.session_state["chat"] if m["role"] == "user"]) >= 3:
        st.session_state.setdefault("done_levels", set()).add(level["id"])
    st.rerun()
