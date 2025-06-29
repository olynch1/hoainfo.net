let emailGlobal = "";
let passwordGlobal = "";

// DOM sanitization helper
function sanitize(input) {
  return DOMPurify.sanitize(input);
}

document.getElementById("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = sanitize(document.getElementById("email").value);
  const password = sanitize(document.getElementById("password").value);

  emailGlobal = email;
  passwordGlobal = password;

  const response = await fetch("http://127.0.0.1:8000/resend-otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });

  if (response.ok) {
    document.getElementById("otp-section").style.display = "block";
    alert("OTP sent. Now enter it to finish login.");
  } else {
    const data = await response.json();
    alert("Failed to send OTP: " + sanitize(data.detail || "Unknown error"));
  }
});

document.getElementById("verify-otp").addEventListener("click", async () => {
  const otp = sanitize(document.getElementById("otp").value);

  const response = await fetch("http://127.0.0.1:8000/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: emailGlobal, password: passwordGlobal, otp })
  });

  const data = await response.json();

  if (response.ok) {
    localStorage.setItem("jwt_token", data.access_token);
    alert("✅ Login successful!");
    window.location.href = "dashboard.html";
  } else {
    alert("❌ Login failed: " + sanitize(data.detail || "Invalid credentials or OTP"));
  }
});

