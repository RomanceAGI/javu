import streamlit as st
import json
import os

st.set_page_config(layout="wide")

st.title("🧠 AGI Agent Live Visual Tracer")

# Load current goal stack
with open("goal_stack.json", "r") as f:
    goals = json.load(f)

# Display goal stack
st.subheader("🎯 Goal Stack")
for goal in goals:
    st.code(goal, language="text")

# Load emotion state (assumes saved as JSON periodically)
emotion_file = "logs/emotion_state.json"
if os.path.exists(emotion_file):
    with open(emotion_file, "r") as f:
        emotions = json.load(f)
    st.subheader("💓 Emotion State")
    st.json(emotions)

# Reward trace
reward_log = "trace/reward_log.json"
if os.path.exists(reward_log):
    with open(reward_log, "r") as f:
        rewards = json.load(f)
    st.subheader("🏆 Reward History")
    st.line_chart([r["value"] for r in rewards[-50:]])

# Self upgrade logs
upgrade_log = "logs/upgrade_trace.log"
if os.path.exists(upgrade_log):
    st.subheader("📈 Self-Upgrade Logs")
    with open(upgrade_log, "r") as f:
        st.text(f.read())
