const el = (id) => document.getElementById(id);

async function handleLoginSubmit(evt) {
  evt.preventDefault();
  const username = el("username").value;
  const password = el("password").value;

  if (!username || !password) {
    el("login-status").textContent = "Please enter username and password.";
    return;
  }

  el("login-status").textContent = "Logging in...";

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Login failed");
    }

    localStorage.setItem("jwt_token", data.token);
    window.location.href = "/app";
  } catch (err) {
    el("login-status").textContent = String(err);
  }
}

el("login-form").addEventListener("submit", handleLoginSubmit);
