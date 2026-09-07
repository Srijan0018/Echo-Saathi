const query = document.querySelector('#query');
const answer = document.querySelector('#answer');
const askButton = document.querySelector('#ask');

function render(result) {
  if (!result.citations.length) {
    answer.innerHTML = '<p class="empty">No indexed rule matched this question. Consult the relevant CPCB notification before acting.</p>';
    answer.classList.add('show');
    return;
  }
  answer.innerHTML = `<h2>Indexed guidance</h2><p class="answer-copy">${result.answer}</p>${result.citations.map(citation => `<div class="citation"><strong>${citation.title}</strong><small>${citation.citation}</small><p>${citation.text}</p></div>`).join('')}`;
  answer.classList.add('show');
}

async function askQuestion() {
  const value = query.value.trim();
  if (!value) return;
  askButton.disabled = true;
  askButton.textContent = 'Searching...';
  try {
    const response = await fetch('/api/v1/rag/query', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ query: value }) });
    if (!response.ok) throw new Error('regulatory index unavailable');
    render(await response.json());
  } catch (error) {
    answer.innerHTML = `<p class="empty">${error.message}</p>`;
    answer.classList.add('show');
  } finally {
    askButton.disabled = false;
    askButton.textContent = 'Find citation';
  }
}

askButton.addEventListener('click', askQuestion);
query.addEventListener('keydown', event => { if (event.key === 'Enter') askQuestion(); });
document.querySelectorAll('.suggestion').forEach(button => button.addEventListener('click', () => { query.value = button.textContent; askQuestion(); }));
