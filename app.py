#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💬 女神對話模擬器（WhatsApp 全真版）
真 AI 對答 + thinking 延遲 + typing 中… + 動心度 + 表白 endgame｜書面語・學生時期
"""
import os, re, json, time, random
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

st.set_page_config(page_title="💬 女神對話模擬器", page_icon="💬", layout="centered")

# ================= WhatsApp 風格 CSS =================
st.markdown("""
<style>
.wa-bg {background:#ECE5DD; background-image:radial-gradient(rgba(0,0,0,0.03) 1px, transparent 1px); background-size:18px 18px; padding:14px; border-radius:12px;}
.wa-header {background:#075E54; color:white; padding:10px 14px; border-radius:12px 12px 0 0; display:flex; align-items:center; gap:10px;}
.wa-name {font-size:18px; font-weight:bold;}
.wa-status {font-size:11px; opacity:0.85;}
.wa-row {display:flex; margin:6px 0;}
.wa-row.me {justify-content:flex-end;}
.wa-bubble {max-width:78%; padding:7px 11px 5px; border-radius:9px; font-size:15px; line-height:1.45; position:relative; box-shadow:0 1px 1px rgba(0,0,0,0.08);}
.wa-in {background:#FFFFFF; border-top-left-radius:2px;}
.wa-out {background:#DCF8C6; border-top-right-radius:2px;}
.wa-time {font-size:10px; color:#667; text-align:right; margin-top:2px;}
.wa-ticks {color:#53BDEB; font-size:12px; margin-left:4px;}
.wa-date {text-align:center; margin:10px 0;}
.wa-date span {background:#E1F2FA; color:#5B6B73; font-size:11px; padding:3px 12px; border-radius:8px;}
.wa-typing {color:#778; font-size:13px; font-style:italic; padding:4px 14px;}
.wa-input {background:#F0F0F0; padding:8px; border-radius:0 0 12px 12px;}
.wa-heart {background:#FFEFF3; border:2px solid #FF6B81; border-radius:12px; padding:8px 14px; margin-bottom:10px;}
</style>
""", unsafe_allow_html=True)

# ================= 狀態 =================
ss = st.session_state
ss.setdefault("msgs", [])          # [{who: me/her, text, time}]
ss.setdefault("heart", 20)          # 動心度 0-99
ss.setdefault("phase", "chat")      # chat / confession / gameover / success
ss.setdefault("streak", 0)

def now_time():
    return time.strftime("%p %I:%M", time.localtime()).replace("AM", "上午").replace("PM", "下午").lstrip("0")

# ================= AI 引擎 =================
def her_reply(history, user_text, phase):
    api_key = _get_api_key()
    persona = (
        "你係「女神」：一位中學女生（學生時期），溫柔有教養，說話用**書面語**（這、為、喜歡、認識），"
        "偶爾帶點矜持同害羞，唔會太熱情，但有禮貌。你會真正回應對方講嘅內容，唔會答非所問。"
    )
    convo = "\n".join(f"{'我' if m['who']=='me' else '女神'}：{m['text']}" for m in history[-10:])
    if phase == "confession":
        prompt = (persona + "\n\n對方啱啱向你表白！請以女神身份真誠回應（書面語），"
                  "同時俾出表白評分 heart_delta（-20 至 25：真誠/具體/尊重你嘅感受先高分）。\n"
                  f"對話記錄：\n{convo}\n\n只回傳 JSON：{{\"reply\":\"...\",\"heart_delta\":10,\"confession_score\":8,\"result\":\"success\" 或 \"gameover\"}}")
    else:
        prompt = (persona + f"\n\n動心程度現在是 {ss['heart']}/99。請真誠回應對方最新一句（書面語、30 字內），"
                  "並評估動心度變化 heart_delta（-5 至 +15：風趣、具體、關心、聆聽 → 加分；無禮、查戶口式連環追問、敷衍 → 減分）。\n"
                  f"對話記錄：\n{convo}\n\n對方最新：{user_text}\n\n只回傳 JSON：{{\"reply\":\"...\",\"heart_delta\":8}}")
    if not api_key:
        # 規則 fallback：至少會跟內容回應
        if "?" in user_text or "？" in user_text:
            return {"reply": "這個問題很有意思，讓我仔細想一想再告訴你。", "heart_delta": 2}
        return {"reply": "這件事聽起來很有趣，你可以再說多一些嗎？", "heart_delta": 3}
    import requests
    url = _sk("SILRA_API_URL", "https://api.silra.cn/v1/chat/completions")
    model = _sk("MODEL_NAME", "qwen3.8-flash")
    try:
        r = requests.post(url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                          json={"model": model, "messages": [{"role": "user", "content": prompt}],
                                "temperature": 0.9}, timeout=60)
        r.raise_for_status()
        content = r.json()["choices"][0]["message"]["content"]
        m = re.search(r"\{.*\}", content, re.S)
        return json.loads(m.group(0))
    except Exception:
        return {"reply": "嗯，我明白你的意思。", "heart_delta": 1}

# ================= 頂部：動心度 + WhatsApp Header =================
heart = min(ss["heart"], 99)
st.markdown(f"""
<div class="wa-heart">
  <div style="font-size:13px; color:#C0392B; font-weight:bold;">💗 動心程度</div>
  <div style="background:#FFD3DB; border-radius:8px; height:22px; width:100%;">
    <div style="background:linear-gradient(90deg,#FF6B81,#FF3E6C); height:22px; width:{heart}%; border-radius:8px; text-align:center; color:white; font-size:13px; line-height:22px;">{heart}%</div>
  </div>
</div>""", unsafe_allow_html=True)

st.markdown("""
<div class="wa-header">
  <div style="width:38px;height:38px;border-radius:50%;background:#25D366;display:flex;align-items:center;justify-content:center;font-size:20px;">👩</div>
  <div><div class="wa-name">女神</div><div class="wa-status">在線</div></div>
</div>
""", unsafe_allow_html=True)

# ================= 聊天記錄 =================
st.markdown('<div class="wa-bg">', unsafe_allow_html=True)
st.markdown('<div class="wa-date"><span>今天</span></div>', unsafe_allow_html=True)
if not ss["msgs"]:
    st.markdown('<div class="wa-row"><div class="wa-bubble wa-in">很高興認識你。聽說你是一位很有趣的人？<div class="wa-time">下午 3:20</div></div></div>', unsafe_allow_html=True)
for m in ss["msgs"]:
    side = "me" if m["who"] == "me" else ""
    cls = "wa-out" if m["who"] == "me" else "wa-in"
    ticks = '<span class="wa-ticks">✓✓</span>' if m["who"] == "me" else ""
    st.markdown(f'<div class="wa-row {side}"><div class="wa-bubble {cls}">{m["text"]}<div class="wa-time">{m["time"]}{ticks}</div></div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ================= 輸入 =================
if ss["phase"] == "confession":
    st.info("💗 動心程度已達 99%！是時候表白了 — 寫下你的真心話，讓她評分。")
    text = st.text_area("你的表白：", key="conf_input", height=100)
    if st.button("送出表白 💝", type="primary"):
        if text.strip():
            with st.spinner("女神正在輸入…"):
                time.sleep(random.uniform(2.0, 4.0))
                data = her_reply(ss["msgs"] + [{"who": "me", "text": text}], text, "confession")
            ss["msgs"].append({"who": "me", "text": text, "time": now_time()})
            ss["msgs"].append({"who": "her", "text": data.get("reply", "…"), "time": now_time()})
            score = data.get("confession_score", 5)
            if data.get("result") == "success" or score >= 7:
                ss["phase"] = "success"
                st.success(f"🎉 培養成功！表白評分 {score}/10")
            else:
                ss["phase"] = "gameover"
                st.error(f"💔 遊戲結束… 表白評分 {score}/10（提示：真誠、具體、尊重她的感受）")
            st.rerun()
elif ss["phase"] in ("success", "gameover"):
    if ss["phase"] == "success":
        st.balloons()
        st.success("🎉 培養成功！你已懂得真誠溝通的藝術。")
    st.button("重新開始 🔄", on_click=lambda: (ss.update({"msgs": [], "heart": 20, "phase": "chat"}), st.rerun()))
else:
    text = st.chat_input("訊息")
    if text:
        ss["msgs"].append({"who": "me", "text": text, "time": now_time()})
        with st.spinner("女神正在輸入…"):
            time.sleep(random.uniform(1.8, 3.8))   # 想一陣子再答
            data = her_reply(ss["msgs"], text, "chat")
        ss["msgs"].append({"who": "her", "text": data.get("reply", "…"), "time": now_time()})
        ss["heart"] = max(0, min(99, ss["heart"] + int(data.get("heart_delta", 2))))
        if ss["heart"] >= 99:
            ss["phase"] = "confession"
        st.rerun()
