let citizenId = null;
let detectedItems = [];

const session = (() => {
  try {
    return JSON.parse(localStorage.getItem('kabadiwala_session') || 'null');
  } catch (_error) {
    return null;
  }
})();

if (session && (!session.user || session.user.role !== 'citizen')) {
  window.location.href = '/login/login.html';
}

const nameInput = document.querySelector('#name');
const phoneInput = document.querySelector('#phone');
if (nameInput && session && session.user) nameInput.value = session.user.full_name || nameInput.value;
if (phoneInput && session && session.user) phoneInput.value = session.user.phone || phoneInput.value;

const scanResult = document.querySelector('#scan-result');
const bookResult = document.querySelector('#book-result');
const scanButton = document.querySelector('#scan');
const bookButton = document.querySelector('#book');
const rwaDrive = document.querySelector('#rwa-drive');
const rwaNameField = document.querySelector('#rwa-name-field');
const logoutButton = document.querySelector('#logout');

if (logoutButton) {
  logoutButton.addEventListener('click', () => {
    localStorage.removeItem('kabadiwala_session');
    window.location.href = '/dashboard/';
  });
}

rwaDrive.addEventListener('change', () => {
  rwaNameField.hidden = !rwaDrive.checked;
});

function showResult(element, html, isError = false) {
  element.innerHTML = html;
  element.classList.toggle('error', isError);
  element.classList.add('show');
}

function materialLabel(code) {
  return code.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
}

scanButton.addEventListener('click', async () => {
  const photo = document.querySelector('#photo').files[0];
  if (!photo) {
    showResult(scanResult, '<strong>Add a photo first</strong><small>The deterministic demo classifier still expects an image file.</small>', true);
    return;
  }
  scanButton.disabled = true;
  scanButton.textContent = 'Scanning...';
  try {
    const form = new FormData();
    form.append('image', photo);
    const response = await fetch('/api/v1/ai/classify-waste', { method: 'POST', body: form });
    if (!response.ok) throw new Error('classification failed');
    const result = await response.json();
    detectedItems = result.detected_materials.map(item => ({ material_code: item.material_code, ai_estimated_kg: item.estimated_kg }));
    const totalEstimatedKg = result.detected_materials.reduce((total, item) => total + Number(item.estimated_kg), 0);
    const confidencePercent = Math.round(Number(result.confidence_score) * 100);
    const modeLabel = result.fallback_used ? 'Demo fallback · deterministic result' : 'Live model result';
    showResult(scanResult, `<strong>${result.contamination_detected ? 'Contamination detected' : 'AI scan complete · clean material mix'}</strong><div class="scan-summary"><div class="scan-stat"><strong>${totalEstimatedKg.toFixed(2)} kg</strong><small>estimated total</small></div><div class="scan-stat"><strong>${result.detected_materials.length}</strong><small>material types</small></div><div class="scan-stat"><strong>${confidencePercent}%</strong><small>confidence</small></div></div><div class="chip-row">${result.detected_materials.map(item => `<span class="chip">${materialLabel(item.material_code)} · ${Number(item.estimated_kg).toFixed(2)} kg · ${Math.round(Number(item.confidence) * 100)}%</span>`).join('')}</div><span class="scan-mode${result.fallback_used ? '' : ' live'}">${modeLabel}</span><small>AI estimate is carried into the pickup request for collector routing and OTP settlement.</small>`);
    bookButton.disabled = false;
  } catch (error) {
    showResult(scanResult, '<strong>Could not classify this image</strong><small>Check that the API is running and try again.</small>', true);
  } finally {
    scanButton.disabled = false;
    scanButton.textContent = 'Scan materials';
  }
});

bookButton.addEventListener('click', async () => {
  bookButton.disabled = true;
  bookButton.textContent = 'Booking...';
  try {
    const registration = await fetch('/api/v1/auth/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ phone: document.querySelector('#phone').value, full_name: document.querySelector('#name').value, role: 'citizen' }) });
    if (registration.status === 409) {
      throw new Error('This demo phone is already registered. Clear the server or use another number.');
    }
    if (!registration.ok) throw new Error('registration failed');
    citizenId = (await registration.json()).id;
    const response = await fetch('/api/v1/pickups/request', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ citizen_id: citizenId, latitude: document.querySelector('#latitude').value, longitude: document.querySelector('#longitude').value, items: detectedItems, is_rwa_drive: rwaDrive.checked, rwa_name: rwaDrive.checked ? document.querySelector('#rwa-name').value : null }) });
    if (!response.ok) throw new Error('pickup request failed');
    const pickup = await response.json();
    showResult(bookResult, `<strong>Pickup requested</strong><small>Keep this code ready for the collector.</small><div class="otp">${pickup.otp_code}</div><small>Request ${pickup.id.slice(0, 8)} · status ${pickup.status}</small><small>Offline sync token ${pickup.offline_sync_token.slice(0, 16)}...</small>`);
  } catch (error) {
    showResult(bookResult, `<strong>${error.message}</strong>`, true);
  } finally {
    bookButton.disabled = false;
    bookButton.textContent = 'Book collector pickup';
  }
});
