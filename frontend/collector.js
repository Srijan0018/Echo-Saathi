const routeResult = document.querySelector('#route-result');
const settleResult = document.querySelector('#settle-result');

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
    showResult(settleResult, `<strong>Settlement complete</strong><small>UPI reference ${result.upi_reference}</small><div class="otp">₹${result.payout_amount}</div><small>${result.audit_flagged ? 'Audit review required' : 'Trust check clear'}</small>`);
  } catch (error) {
    showResult(settleResult, `<strong>${error.message}</strong>`, true);
  } finally {
    button.disabled = false;
  }
});
