const formatKg = value => `${Number(value).toFixed(2)} kg`;

async function loadDashboard() {
  const [summaryResponse, materialsResponse] = await Promise.all([
    fetch('/api/v1/municipality/summary'),
    fetch('/api/v1/materials')
  ]);
  if (!summaryResponse.ok || !materialsResponse.ok) throw new Error('Dashboard API unavailable');
  const summary = await summaryResponse.json();
  const materials = await materialsResponse.json();

  document.querySelector('#recovered-weight').textContent = formatKg(summary.recovered_weight_kg);
  document.querySelector('#batch-count').textContent = `${summary.processed_batches} batches`;
  document.querySelector('#pickup-count').textContent = summary.pickups_completed;
  document.querySelector('#collector-count').textContent = summary.active_collectors;
  document.querySelector('#audit-count').textContent = summary.fraud_audit_flags;
  document.querySelector('#audit-label').textContent = summary.fraud_audit_flags ? 'Review required' : 'Clear for now';
  document.querySelector('#activity-audit').textContent = summary.fraud_audit_flags ? `${summary.fraud_audit_flags} audit flag(s) require review` : 'No audit flags detected';

  document.querySelector('#materials-list').innerHTML = materials.map(material => `
    <div class="rate">
      <div><span class="rate-name">${material.display_name}</span><span class="rate-code">${material.material_code}</span></div>
      <div><span class="rate-price">₹${Number(material.aggregator_buy_rate).toFixed(2)}</span><span class="rate-margin">margin ₹${Number(material.collector_margin).toFixed(2)}</span></div>
    </div>`).join('');
}

loadDashboard().catch(() => {
  document.querySelector('#materials-list').innerHTML = '<div class="loading">Unable to reach the operations API.</div>';
  document.querySelector('.status').innerHTML = '<span class="pulse"></span>API unavailable';
});
