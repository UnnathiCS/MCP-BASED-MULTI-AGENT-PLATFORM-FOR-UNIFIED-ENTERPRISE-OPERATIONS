const form = document.getElementById('query-form');
const textarea = document.getElementById('email-content');
const resultEl = document.getElementById('result');
const resultTextEl = document.getElementById('result-text');
const submitBtn = document.getElementById('submit-btn');
const processInboxBtn = document.getElementById('process-inbox-btn');
const refreshTicketsBtn = document.getElementById('refresh-tickets-btn');
const ticketsList = document.getElementById('tickets-list');
const ticketDetails = document.getElementById('ticket-details');
const conversationEl = document.getElementById('conversation');
const modeRadios = document.querySelectorAll('input[name="mode"]');
const autoControls = document.getElementById('auto-controls');
const startAutoBtn = document.getElementById('start-auto');
const stopAutoBtn = document.getElementById('stop-auto');
const autoIntervalInput = document.getElementById('auto-interval');
const autoStatus = document.getElementById('auto-status');
const loginStatus = document.getElementById('login-status');
const navLogin = document.getElementById('nav-login');
const navLogout = document.getElementById('nav-logout');
const ticketsLimitSelectMain = document.getElementById('tickets-limit-main');
const ticketsLimitSelectInbox = document.getElementById('tickets-limit-inbox');

// Initialize Google Sign-In
window.onload = function() {
  if (typeof google !== 'undefined' && google.accounts) {
    google.accounts.id.initialize({
      client_id: '614492370530-miidcn5ve6sdmc0ocpt25r1bgvschlc6.apps.googleusercontent.com',
      callback: handleGoogleSignIn
    });

    const googleBtn = document.getElementById('google-signin-button');
    if (googleBtn) {
      google.accounts.id.renderButton(
        googleBtn,
        { theme: 'outline', size: 'large', width: 280 }
      );
    }
  }

  // Check initial auth status
  refreshAuth().then((isAuthed) => {
    if (isAuthed) {
      loadTickets();
    }
  }).catch(() => {});
};

async function handleGoogleSignIn(response) {
  if (loginStatus) loginStatus.textContent = 'Signing in...';
  try {
    const res = await fetch('/auth/google/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ token: response.credential })
    });

    const data = await res.json();

    if (data.authenticated) {
      if (loginStatus) loginStatus.textContent = 'Login successful!';
      setAuthUI(true);
      await loadTickets();
      await refreshAutoStatus();
    } else {
      throw new Error('Authentication failed');
    }
  } catch (error) {
    console.error('Google sign-in error:', error);
    if (loginStatus) loginStatus.textContent = 'Sign-in failed. Please try again.';
  }
}

async function processEmail(content) {
  const response = await fetch('/agent/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({ content })
  });
  if (!response.ok) throw new Error('Request failed');
  const data = await response.json();
  return data.response || JSON.stringify(data, null, 2);
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const content = textarea.value.trim();
  if (!content) return;

  submitBtn.disabled = true;
  submitBtn.textContent = 'Processing...';
  resultEl.classList.remove('hidden');
  resultTextEl.textContent = 'Working...';

  try {
    const output = await processEmail(content);
    resultTextEl.textContent = output;
  } catch (err) {
    resultTextEl.textContent = 'Error: ' + err.message;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Process';
  }
});

processInboxBtn?.addEventListener('click', async () => {
  processInboxBtn.disabled = true;
  processInboxBtn.textContent = 'Processing...';
  try {
    const res = await fetch('/process-all', { method: 'POST', credentials: 'include' });
    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(errorText || `HTTP ${res.status}`);
    }
    const data = await res.json();
    await loadTickets();
    if (data.status) {
      alert('Inbox processed successfully!');
    }
  } catch (e) {
    console.error('Error processing inbox:', e);
    alert('Error processing inbox: ' + (e.message || 'Unknown error'));
  } finally {
    processInboxBtn.disabled = false;
    processInboxBtn.textContent = 'Process Inbox Now';
  }
});

refreshTicketsBtn?.addEventListener('click', loadTickets);

// Add pagination change handlers
ticketsLimitSelectMain?.addEventListener('change', loadTickets);
ticketsLimitSelectInbox?.addEventListener('change', loadTickets);

async function loadTickets() {
  if (!ticketsList) {
    console.error('ticketsList element not found');
    return;
  }
  
  // Check which limit selector exists (main page or inbox processing)
  const limit = ticketsLimitSelectInbox 
    ? parseInt(ticketsLimitSelectInbox.value) || 50 
    : (ticketsLimitSelectMain ? parseInt(ticketsLimitSelectMain.value) || 50 : 50);
  
  ticketsList.innerHTML = '<li class="muted">Loading...</li>';
  try {
    const res = await fetch(`/tickets?limit=${limit}`, { credentials: 'include' });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    console.log('Received data:', data); // Debug log
    
    // Handle both array format and object format
    let tickets = [];
    if (Array.isArray(data.tickets)) {
      tickets = data.tickets;
    } else if (Array.isArray(data)) {
      tickets = data;
    } else if (data && typeof data === 'object') {
      tickets = data.tickets || [];
    }
    
    // Ensure tickets is an array
    if (!Array.isArray(tickets)) {
      console.error('Tickets is not an array:', tickets);
      tickets = [];
    }
    
    ticketsList.innerHTML = '';
    if (!tickets.length) {
      ticketsList.innerHTML = '<li class="muted">No tickets yet</li>';
      return;
    }
    
    // Safely iterate over tickets
    for (let i = 0; i < tickets.length; i++) {
      const t = tickets[i];
      
      // Skip if t is null or undefined
      if (t == null) {
        console.warn('Skipping null/undefined ticket at index', i);
        continue;
      }
      
      // Handle both array format and object format
      let ticketId, convId, subject, sender, body, date, assigned, intent, response;
      
      try {
        if (Array.isArray(t)) {
          // Array format: [ticket_id, conversation_id, message_id, subject, sender, body, date, assigned_agent, intent, response]
          [ticketId, convId, , subject, sender, body, date, assigned, intent, response] = t;
        } else if (typeof t === 'object' && t !== null) {
          // Object format
          ticketId = t.ticket_id || t.id || '';
          convId = t.conversation_id || t.conv_id || '';
          subject = t.subject || '';
          sender = t.sender || t.from || '';
          body = t.body || '';
          date = t.date || '';
          assigned = t.assigned_agent || t.assigned || '';
          intent = t.intent || '';
          response = t.response || '';
        } else {
          console.warn('Skipping invalid ticket format at index', i, t);
          continue; // Skip invalid entries
        }
        
        const li = document.createElement('li');
        li.textContent = `${ticketId || 'N/A'} — ${subject || 'No subject'} — ${sender || 'Unknown'}`;
        li.addEventListener('click', () => selectTicket(ticketId, convId, { subject, sender, body, date, assigned, intent, response }));
        ticketsList.appendChild(li);
      } catch (err) {
        console.error('Error processing ticket at index', i, ':', err, t);
        continue; // Skip this ticket and continue
      }
    }
  } catch (error) {
    console.error('Error loading tickets:', error);
    ticketsList.innerHTML = `<li class="muted">Error loading tickets: ${error.message}</li>`;
  }
}

async function selectTicket(ticketId, convId, meta) {
  ticketDetails.innerHTML = `
    <div><strong>ID:</strong> ${ticketId}</div>
    <div><strong>Subject:</strong> ${meta.subject}</div>
    <div><strong>From:</strong> ${meta.sender}</div>
    <div><strong>Date:</strong> ${meta.date}</div>
    <div><strong>Agent:</strong> ${meta.assigned || '-'} | <strong>Intent:</strong> ${meta.intent || '-'}</div>
  `;
  
  try {
    const res = await fetch(`/tickets/conversation/${encodeURIComponent(convId)}`, { credentials: 'include' });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    
    // Format conversation to show incoming email and reply clearly
    let conversationHtml = '';
    
    if (data.history) {
      // Parse the conversation history
      const history = data.history;
      
      // Show incoming email
      conversationHtml += `<div style="margin-bottom: 20px; padding: 16px; background: #f8f9fa; border-left: 4px solid #0066cc; border-radius: 4px;">
        <h4 style="margin: 0 0 12px 0; color: #0066cc; font-size: 16px;">Incoming Email</h4>
        <div style="white-space: pre-wrap; font-family: inherit; line-height: 1.6;">${escapeHtml(meta.body || 'No content')}</div>
      </div>`;
      
      // Show reply if available
      if (meta.response && meta.response.trim() && meta.response !== 'SPAM') {
        conversationHtml += `<div style="margin-bottom: 20px; padding: 16px; background: #e8f5e9; border-left: 4px solid #28a745; border-radius: 4px;">
          <h4 style="margin: 0 0 12px 0; color: #28a745; font-size: 16px;">Reply Sent</h4>
          <div style="white-space: pre-wrap; font-family: inherit; line-height: 1.6;">${escapeHtml(meta.response)}</div>
        </div>`;
      } else if (meta.intent === 'SPAM') {
        conversationHtml += `<div style="margin-bottom: 20px; padding: 16px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
          <h4 style="margin: 0 0 12px 0; color: #856404; font-size: 16px;">Status</h4>
          <div>This email was classified as SPAM. No reply was sent.</div>
        </div>`;
      } else {
        conversationHtml += `<div style="margin-bottom: 20px; padding: 16px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
          <h4 style="margin: 0 0 12px 0; color: #856404; font-size: 16px;">Status</h4>
          <div>No reply has been sent yet. This ticket is pending processing.</div>
        </div>`;
      }
      
      // Show full conversation history if available
      if (history && history.trim() && history !== meta.body) {
        conversationHtml += `<div style="margin-top: 20px; padding: 16px; background: #f8f9fa; border-radius: 4px;">
          <h4 style="margin: 0 0 12px 0; color: #495057; font-size: 16px;">Full Conversation History</h4>
          <pre style="white-space: pre-wrap; font-family: inherit; line-height: 1.6; margin: 0;">${escapeHtml(history)}</pre>
        </div>`;
      }
    } else {
      // Fallback if no history
      conversationHtml += `<div style="padding: 16px; background: #f8f9fa; border-left: 4px solid #0066cc; border-radius: 4px;">
        <h4 style="margin: 0 0 12px 0; color: #0066cc; font-size: 16px;">Incoming Email</h4>
        <div style="white-space: pre-wrap; font-family: inherit; line-height: 1.6;">${escapeHtml(meta.body || 'No content')}</div>
      </div>`;
      
      if (meta.response && meta.response.trim() && meta.response !== 'SPAM') {
        conversationHtml += `<div style="margin-top: 20px; padding: 16px; background: #e8f5e9; border-left: 4px solid #28a745; border-radius: 4px;">
          <h4 style="margin: 0 0 12px 0; color: #28a745; font-size: 16px;">Reply Sent</h4>
          <div style="white-space: pre-wrap; font-family: inherit; line-height: 1.6;">${escapeHtml(meta.response)}</div>
        </div>`;
      }
    }
    
    conversationEl.innerHTML = conversationHtml;
  } catch (error) {
    console.error('Error loading conversation:', error);
    conversationEl.innerHTML = `<div style="padding: 16px; background: #f8d7da; border-left: 4px solid #dc3545; border-radius: 4px; color: #721c24;">
      <strong>Error:</strong> Failed to load conversation: ${error.message || 'Unknown error'}
    </div>`;
  }
}

function escapeHtml(text) {
  if (!text) return '';
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ======== Auto / Manual Mode ========
modeRadios.forEach(r => r.addEventListener('change', () => {
  const mode = getMode();
  if (mode === 'auto') {
    autoControls.classList.remove('hidden');
    refreshAutoStatus();
  } else {
    autoControls.classList.add('hidden');
  }
}));

function getMode() {
  const checked = Array.from(modeRadios).find(r => r.checked);
  return checked ? checked.value : 'manual';
}

async function refreshAutoStatus() {
  try {
    const res = await fetch('/autoprocess/status', { credentials: 'include' });
    const data = await res.json();
    if (typeof data.interval === 'number') autoIntervalInput.value = data.interval;
    autoStatus.textContent = `Status: ${data.running ? 'running' : 'stopped'}`;
  } catch (e) {
    autoStatus.textContent = 'Status: unavailable';
  }
}

startAutoBtn?.addEventListener('click', async () => {
  const interval = parseInt(autoIntervalInput.value || '60', 10);
  try {
    const res = await fetch('/autoprocess/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ interval })
    });
    await res.json();
    await refreshAutoStatus();
  } catch (e) {
    alert('Failed to start auto-processing');
  }
});

stopAutoBtn?.addEventListener('click', async () => {
  try {
    const res = await fetch('/autoprocess/stop', { method: 'POST', credentials: 'include' });
    await res.json();
    await refreshAutoStatus();
  } catch (e) {
    alert('Failed to stop auto-processing');
  }
});

// Periodically refresh tickets if auto mode is active
setInterval(async () => {
  if (getMode() === 'auto') {
    try { await loadTickets(); } catch (_) {}
  }
}, 10000);

// ======== Auth (Admin) ========
async function refreshAuth() {
  try {
    const res = await fetch('/auth/status', { credentials: 'include' });
    const data = await res.json();
    const isAuthed = !!data.authenticated;
    setAuthUI(isAuthed);
    if (isAuthed) {
      await refreshAutoStatus();
    }
    return isAuthed;
  } catch (_) {
    setAuthUI(false);
    return false;
  }
}

function setAuthUI(isAuthed) {
  document.querySelectorAll('.gated').forEach(el => {
    el.classList.toggle('hidden', !isAuthed);
  });
  navLogin?.classList.toggle('hidden', isAuthed);
  navLogout?.classList.toggle('hidden', !isAuthed);
  const loginPanel = document.querySelector('.login-panel');
  if (loginPanel) loginPanel.classList.toggle('hidden', isAuthed);
}

navLogout?.addEventListener('click', async () => {
  try { await fetch('/auth/logout', { method: 'POST', credentials: 'include' }); } catch (_) {}
  setAuthUI(false);
  window.location.href = '/ui/admin-login.html';
});


