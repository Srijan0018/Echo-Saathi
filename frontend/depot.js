const aggregateResult = document.querySelector('#aggregate-result');
const recycleResult = document.querySelector('#recycle-result');

function showResult(element, html, error = false) {
  element.innerHTML = html;
  element.classList.toggle('error', error);
  element.classList.add('show');
}

document.querySelector('#aggregate').addEventListener('click', async () => {
  const button = document.querySelector('#aggregate');
  button.disabled = true;
  try {
    const response = await fetch('/api/v1/batches/aggregate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ aggregator_id: document.querySelector('#aggregator').value, material_code: document.querySelector('#material').value, pickup_ids: document.querySelector('#pickups').value.split(',').map(value => value.trim()).filter(Boolean) }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'batch creation failed');
    document.querySelector('#batch').value = result.batch_id;
    showResult(aggregateResult, `<strong>Batch manifest created</strong><small>Gross weight ${result.gross_weight_kg} kg · status ${result.status}</small><div class="token">${result.batch_hash.slice(0, 20)}...</div>`);
  } catch (error) {
    showResult(aggregateResult, `<strong>${error.message}</strong>`, true);
  } finally {
    button.disabled = false;
  }
});

document.querySelector('#recycle').addEventListener('click', async () => {
  const button = document.querySelector('#recycle');
  button.disabled = true;
  try {
    const response = await fetch(`/api/v1/batches/${document.querySelector('#batch').value}/recycle`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ moisture_deduction_pct: document.querySelector('#moisture').value, foreign_matter_deduction_pct: document.querySelector('#foreign').value }) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'recycling confirmation failed');
    showResult(recycleResult, `<strong>Processing verified</strong><small>Net weight ${result.net_weight_kg} kg · avoided ${result.co2e_avoided_kg} kg CO2e</small><div class="token">${result.cpcb_epr_token}</div><small>Digital EPR token issued</small>`);
  } catch (error) {
    showResult(recycleResult, `<strong>${error.message}</strong>`, true);
  } finally {
    button.disabled = false;
  }
});
