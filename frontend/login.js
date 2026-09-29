const result = document.querySelector('#result');

function redirectIfActiveSession() {
  try {
    const stored = JSON.parse(localStorage.getItem('kabadiwala_session') || 'null');
    if (stored && stored.user && stored.user.role) {
      window.location.href = stored.user.role === 'collector' ? '/collector/collector.html' : '/citizen/citizen.html';
    }
  } catch (_error) {
    localStorage.removeItem('kabadiwala_session');
  }
}

redirectIfActiveSession();

document.querySelector('#login').addEventListener('click', async () => {
  const button = document.querySelector('#login');
  button.disabled = true;
  try {
    const response = await fetch('/api/v1/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: document.querySelector('#phone').value, role: document.querySelector('#role').value }) });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Login failed');
    localStorage.setItem('kabadiwala_session', JSON.stringify(data));
    window.location.href = data.user.role === 'collector' ? '/collector/collector.html' : '/citizen/citizen.html';
  } catch (error) {
    result.textContent = error.message;
    result.classList.add('show');
  } finally {
    button.disabled = false;
  }
});
