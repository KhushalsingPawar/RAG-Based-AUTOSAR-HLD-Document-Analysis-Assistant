"""Login & Registration page rendered before the main app is shown."""
import streamlit as st
from frontend.components.api_client import APIClient, BACKEND_URL


def _make_client_with_token() -> APIClient:
    """Return an APIClient pre-loaded with the current session token."""
    return APIClient(base_url=BACKEND_URL, token=st.session_state.get("auth_token"))


def render_auth_page() -> bool:
    """
    Render the authentication gate.

    Returns True if the user is logged in (app should continue rendering).
    Returns False if the login/register form was shown and the user isn't authenticated yet.
    """
    # If already authenticated, skip the gate
    if st.session_state.get("auth_token") and st.session_state.get("auth_user"):
        return True

    # ── Auth UI ───────────────────────────────────────────────────────────────
    st.markdown(
        """
        <style>
        .auth-box {
            max-width: 420px;
            margin: 4rem auto;
            padding: 2.5rem 2rem;
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.07);
        }
        .auth-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #1E3A8A;
            text-align: center;
            margin-bottom: 0.2rem;
        }
        .auth-sub {
            font-size: 0.95rem;
            color: #6B7280;
            text-align: center;
            margin-bottom: 1.5rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="auth-title">🚗 AUTOSAR HLD Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="auth-sub">Sign in to access the platform</div>', unsafe_allow_html=True)
    st.divider()

    tab_login, tab_register = st.tabs(["🔑 Sign In", "📝 Create Account"])

    unauthenticated_client = APIClient(base_url=BACKEND_URL)

    # ── Login Tab ─────────────────────────────────────────────────────────────
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="your_username")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            if not username.strip() or not password:
                st.error("Please enter both username and password.")
            else:
                with st.spinner("Signing in…"):
                    result = unauthenticated_client.login(username.strip(), password)

                if "access_token" in result:
                    st.session_state["auth_token"] = result["access_token"]
                    st.session_state["auth_user"] = result.get("username", username)
                    st.session_state["auth_full_name"] = result.get("full_name", "")
                    st.success(f"Welcome back, **{result.get('full_name') or result.get('username')}**! 🎉")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('detail', 'Login failed. Check your credentials.')}")

    # ── Register Tab ──────────────────────────────────────────────────────────
    with tab_register:
        with st.form("register_form"):
            new_full_name = st.text_input("Full Name", placeholder="Jane Doe")
            new_username = st.text_input("Username", placeholder="jane_doe (min 3 chars)")
            new_password = st.text_input("Password", type="password", placeholder="Min 6 characters")
            new_password2 = st.text_input("Confirm Password", type="password", placeholder="Repeat password")
            reg_submitted = st.form_submit_button("Create Account", use_container_width=True, type="primary")

        if reg_submitted:
            errors = []
            if len(new_username.strip()) < 3:
                errors.append("Username must be at least 3 characters.")
            if len(new_password) < 6:
                errors.append("Password must be at least 6 characters.")
            if new_password != new_password2:
                errors.append("Passwords do not match.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
                with st.spinner("Creating your account…"):
                    result = unauthenticated_client.register(
                        username=new_username.strip(),
                        password=new_password,
                        full_name=new_full_name.strip(),
                    )

                if "access_token" in result:
                    st.session_state["auth_token"] = result["access_token"]
                    st.session_state["auth_user"] = result.get("username", new_username)
                    st.session_state["auth_full_name"] = result.get("full_name", new_full_name)
                    st.success(f"Account created! Welcome, **{result.get('full_name') or result.get('username')}**! 🎉")
                    st.rerun()
                else:
                    st.error(f"❌ {result.get('detail', 'Registration failed.')}")

    return False  # not logged in yet


def render_user_sidebar_widget():
    """Show logged-in user info and logout button in the sidebar."""
    user = st.session_state.get("auth_user", "")
    full_name = st.session_state.get("auth_full_name", "")
    display = full_name if full_name else user

    st.sidebar.divider()
    st.sidebar.markdown(f"👤 **{display}** (`{user}`)")
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        for key in ["auth_token", "auth_user", "auth_full_name"]:
            st.session_state.pop(key, None)
        st.rerun()
