const el = (id) => document.getElementById(id);

async function handleSignupSubmit(evt) {
  evt.preventDefault();
  const username = el("username").value;
  const password = el("password").value;

  if (!username || !password) {
    el("signup-status").textContent = "Please enter username and password.";
    return;
  }

  el("signup-status").textContent = "Creating account...";

  try {
    const res = await fetch("/api/signup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.error || "Signup failed");
    }

    el("signup-status").textContent = "Account created! You can now log in.";
    setTimeout(() => {
      window.location.href = "/";
    }, 2000);
  } catch (err) {
    el("signup-status").textContent = String(err);
  }
}

el("signup-form").addEventListener("submit", handleSignupSubmit);
