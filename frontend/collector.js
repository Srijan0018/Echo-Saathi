const session = (() => {
  try {
    return JSON.parse(localStorage.getItem('kabadiwala_session') || 'null');
  } catch (_error) {
    return null;
  }
})();

if (session && (!session.user || session.user.role !== 'collector')) {
  window.location.href = '/login/login.html';
}

const routeResult = document.querySelector('#route-result');
const settleResult = document.querySelector('#settle-result');
const assignResult = document.querySelector('#assign-result');
const inboxResult = document.querySelector('#inbox-result');
const collectorIdInput = document.querySelector('#collector-id');
const settleCollectorIdInput = document.querySelector('#settle-collector-id');
const kycCollectorIdInput = document.querySelector('#kyc-collector-id');
const kycResult = document.querySelector('#kyc-result');
const verifyKycButton = document.querySelector('#verify-kyc');
const logoutButton = document.querySelector('#logout');

if (collectorIdInput && session && session.user) collectorIdInput.value = session.user.id || collectorIdInput.value;
if (settleCollectorIdInput && session && session.user) settleCollectorIdInput.value = session.user.id || settleCollectorIdInput.value;
if (kycCollectorIdInput && session && session.user) kycCollectorIdInput.value = session.user.id || kycCollectorIdInput.value;

if (logoutButton) {
  logoutButton.addEventListener('click', () => {
    localStorage.removeItem('kabadiwala_session');
    window.location.href = '/dashboard/';
  });
}

function showResult(element, html, error = false) {
  element.innerHTML = html;
  element.classList.toggle('error', error);
  element.classList.add('show');
}

function parseStops(value) {
  return value.split(';').map(raw => {
    const [stop_id, weight_kg, volume_m3] = raw.split(',').map(item => item.trim());
    return { stop_id, weight_kg, volume_m3 };
  });
}

if (verifyKycButton) {
  verifyKycButton.addEventListener('click', async () => {
    verifyKycButton.disabled = true;
    try {
      const response = await fetch('/api/v1/dpi/verify-kyc', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ user_id: document.querySelector('#kyc-collector-id').value, reference_token: document.querySelector('#kyc-token').value }) });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'identity verification failed');
      showResult(kycResult, `<strong>Collector identity verified</strong><small>${result.kyc_id} · name match ${result.name_match ? 'confirmed' : 'review required'}</small><span class="verified-badge">Earnings history enabled · welfare referral eligible</span>`);
    } catch (error) {
      showResult(kycResult, `<strong>${error.message}</strong>`, true);
    } finally {
      verifyKycButton.disabled = false;
    }
  });
}

document.querySelector('#load-inbox').addEventListener('click', async () => {
  const button = document.querySelector('#load-inbox');
  button.disabled = true;
  try {
    const collectorId = document.querySelector('#collector-id').value;
    const response = await fetch(`/api/v1/collectors/${collectorId}/pickups`);
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'inbox unavailable');
    showResult(inboxResult, result.pickups.length ? result.pickups.map(pickup => `<div class="trip"><strong>${pickup.status}</strong><span>${pickup.id.slice(0, 8)}</span><span>${pickup.items.map(item => item.material_code).join(', ')}</span></div>`).join('') : '<strong>No open pickups</strong>');
  } catch (error) {
    showResult(inboxResult, `<strong>${error.message}</strong>`, true);
  } finally {
    button.disabled = false;
  }
});

document.querySelector('#optimize').addEventListener('click', async () => {
  const button = document.querySelector('#optimize');
  button.disabled = true;
  try {
    const response = await fetch('/api/v1/routing/optimize', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ collector_id: document.querySelector('#collector-id').value, max_payload_kg: document.querySelector('#payload').value, max_volume_m3: document.querySelector('#volume').value, stops: parseStops(document.querySelector('#stops').value) }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'route optimization failed');
    showResult(routeResult, result.map((trip, index) => `<div class="trip"><strong>Trip ${index + 1}</strong><span>${trip.stop_ids.join(' → ')}</span><span>${trip.weight_kg} kg / ${trip.volume_m3} m³</span></div>`).join(''));
  } catch (error) {
    showResult(routeResult, `<strong>${error.message}</strong>`, true);
  } finally {
    button.disabled = false;
  }
});

document.querySelector('#settle').addEventListener('click', async () => {
  const button = document.querySelector('#settle');
  button.disabled = true;
  try {
    const response = await fetch('/api/v1/pickups/verify-and-settle', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pickup_id: document.querySelector('#pickup-id').value, collector_id: document.querySelector('#settle-collector-id').value, otp_code: document.querySelector('#otp').value, items: [{ material_code: document.querySelector('#material').value, actual_weight_kg: document.querySelector('#weight').value, quality_deduction_pct: document.querySelector('#deduction').value }] }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'settlement failed');
    showResult(settleResult, `<strong>Settlement complete</strong><small>UPI reference ${result.upi_reference}</small><div class="otp">₹${result.payout_amount}</div><small>${result.audit_flagged ? 'Audit review required' : 'Trust check clear'} · Trust engine Z-score ${result.z_score}</small>`);
  } catch (error) {
    showResult(settleResult, `<strong>${error.message}</strong>`, true);
  } finally {
    button.disabled = false;
  }
});

document.querySelector('#assign').addEventListener('click', async () => {
  const button = document.querySelector('#assign');
  button.disabled = true;
  try {
    const response = await fetch('/api/v1/pickups/assign', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pickup_id: document.querySelector('#pickup-id').value, collector_id: document.querySelector('#settle-collector-id').value }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'assignment failed');
    showResult(assignResult, `<strong>Pickup assigned</strong><small>Ownership confirmed · status ${result.status}</small>`);
  } catch (error) {
    showResult(assignResult, `<strong>${error.message}</strong>`, true);
  } finally {
    button.disabled = false;
  }
});
