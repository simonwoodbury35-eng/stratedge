from datetime import datetime, timezone

import streamlit as st

from agent import run_stratedge
from auth import generate_reset_token, hash_password, send_reset_email, verify_password
from database import (
    create_user,
    get_all_profiles,
    get_recent_strategies,
    get_reset_token,
    get_strategies_for_business,
    get_user_by_email,
    get_user_by_id,
    init_db,
    mark_token_used,
    save_profile,
    save_strategy,
    update_user_password,
)

init_db()

st.set_page_config(page_title="StratEdge", page_icon="📈", layout="wide")

# ── Password reset via URL token ──────────────────────────────────────────────

reset_token = st.query_params.get("reset_token")

if reset_token:
    st.title("📈 StratEdge — Reset Your Password")
    token_row = get_reset_token(reset_token)

    if token_row is None:
        st.error("This reset link is invalid or has already been used.")
    else:
        expires_at = datetime.fromisoformat(token_row["expires_at"])
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires_at:
            st.error("This reset link has expired. Please request a new one.")
        else:
            with st.form("reset_form"):
                new_password = st.text_input("New Password", type="password")
                confirm_password = st.text_input("Confirm New Password", type="password")
                submitted = st.form_submit_button("Set New Password", use_container_width=True)

            if submitted:
                if len(new_password) < 8:
                    st.error("Password must be at least 8 characters.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    update_user_password(token_row["user_id"], hash_password(new_password))
                    mark_token_used(reset_token)
                    st.success("Password updated! You can now log in.")
                    st.query_params.clear()
    st.stop()

# ── Auth gate ─────────────────────────────────────────────────────────────────

if not st.session_state.get("user_id"):
    st.title("📈 StratEdge: AI-Powered Marketing Strategist")
    st.markdown("*Built for small business owners who need a real marketing strategy, fast.*")
    st.divider()

    tab_login, tab_signup, tab_forgot = st.tabs(["Log In", "Sign Up", "Forgot Password"])

    with tab_login:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", use_container_width=True)

        if submitted:
            user = get_user_by_email(email)
            if user and verify_password(password, user["password_hash"]):
                st.session_state["user_id"] = user["id"]
                st.session_state["user_name"] = user["name"]
                st.rerun()
            else:
                st.error("Invalid email or password.")

    with tab_signup:
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            confirm = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            if not name or not email or not password:
                st.error("All fields are required.")
            elif len(password) < 8:
                st.error("Password must be at least 8 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif get_user_by_email(email):
                st.error("An account with that email already exists.")
            else:
                create_user(name, email, hash_password(password))
                user = get_user_by_email(email)
                st.session_state["user_id"] = user["id"]
                st.session_state["user_name"] = user["name"]
                st.rerun()

    with tab_forgot:
        with st.form("forgot_form"):
            email = st.text_input("Enter your account email")
            submitted = st.form_submit_button("Send Reset Link", use_container_width=True)

        if submitted:
            user = get_user_by_email(email)
            if user:
                token = generate_reset_token(user["id"])
                try:
                    send_reset_email(user["email"], token)
                except Exception:
                    st.error("Failed to send reset email. Please try again later.")
            # Always show the same message to prevent email enumeration
            st.success("If an account with that email exists, a reset link has been sent.")

    st.stop()

# ── Main app (authenticated) ──────────────────────────────────────────────────

# Sidebar
st.sidebar.title("Returning Business?")
all_profiles = get_all_profiles()
business_names = [p["business_name"] for p in all_profiles]
sidebar_options = ["-- New Business --"] + business_names

selected_business = st.sidebar.selectbox("Select a saved business", sidebar_options)

if selected_business != "-- New Business --":
    profile = next((p for p in all_profiles if p["business_name"] == selected_business), None)
    if profile:
        st.session_state["prefill_name"] = profile["business_name"]
        st.session_state["prefill_industry"] = profile["industry"]
        st.session_state["prefill_audience"] = profile["target_audience"]
else:
    for key in ["prefill_name", "prefill_industry", "prefill_audience"]:
        st.session_state.pop(key, None)

st.sidebar.divider()
user = get_user_by_id(st.session_state["user_id"])
if user:
    st.sidebar.markdown(f"Logged in as **{user['name']}**")
if st.sidebar.button("Log Out"):
    st.session_state.clear()
    st.rerun()

# Main
st.title("📈 StratEdge: AI-Powered Marketing Strategist")
st.markdown("*Built for small business owners who need a real marketing strategy, fast.*")
st.divider()

GOALS_OPTIONS = [
    "Grow social media following",
    "Increase website traffic",
    "Drive in-store foot traffic",
    "Launch a new product",
    "Build brand awareness",
    "Increase online sales",
]
BUDGET_OPTIONS = [
    "Under $500",
    "$500 - $1,000",
    "$1,000 - $2,500",
    "$2,500 - $5,000",
    "$5,000+",
]

tab_generate, tab_history = st.tabs(["Generate Strategy", "Strategy History"])

with tab_generate:
    with st.form("strategy_form"):
        col1, col2 = st.columns(2)

        with col1:
            business_name = st.text_input(
                "Business Name",
                value=st.session_state.get("prefill_name", ""),
                placeholder="e.g. Austin Organic Skincare",
            )
            industry = st.text_input(
                "Industry",
                value=st.session_state.get("prefill_industry", ""),
                placeholder="e.g. Organic Skincare, Food Truck, Fitness",
            )
            target_audience = st.text_input(
                "Target Audience",
                value=st.session_state.get("prefill_audience", ""),
                placeholder="e.g. Women 25-40 who care about sustainability",
            )

        with col2:
            goals = st.selectbox("Primary Goal", GOALS_OPTIONS)
            budget = st.selectbox("Monthly Marketing Budget", BUDGET_OPTIONS)

        submitted = st.form_submit_button("Generate My Strategy ⚡", use_container_width=True)

    if submitted:
        if not business_name or not industry or not target_audience:
            st.error("Please fill in all fields before generating your strategy.")
        else:
            with st.spinner("StratEdge is researching your market and building your strategy..."):
                strategy = run_stratedge(business_name, industry, target_audience, goals, budget)

            st.success("Your strategy is ready!")
            profile_id = save_profile(business_name, industry, target_audience)
            save_strategy(profile_id, goals, budget, strategy)
            st.caption("Strategy saved to history.")
            st.divider()
            st.markdown(strategy)
            st.divider()
            st.download_button(
                label="Download Strategy as Text File",
                data=strategy,
                file_name=f"{business_name}_marketing_strategy.txt",
                mime="text/plain",
            )

with tab_history:
    if selected_business != "-- New Business --":
        st.subheader(f"Strategies for {selected_business}")
        past = get_strategies_for_business(selected_business)
    else:
        st.subheader("Recent Strategies")
        st.caption("Select a business in the sidebar to filter by business.")
        past = get_recent_strategies()

    if not past:
        st.write("No strategies saved yet.")
    else:
        for row in past:
            label = f"{row['business_name']} — {row['created_at'][:16]}"
            with st.expander(label):
                st.markdown(f"**Industry:** {row['industry']}")
                st.markdown(f"**Goal:** {row['goals']}  |  **Budget:** {row['budget']}")
                st.divider()
                st.markdown(row['strategy_text'])
