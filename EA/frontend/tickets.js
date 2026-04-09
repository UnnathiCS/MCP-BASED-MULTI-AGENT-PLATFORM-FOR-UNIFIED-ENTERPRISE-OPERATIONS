const refreshBtn = document.getElementById('refresh-tickets-btn');
const tbody = document.getElementById('tickets-body');
const conversationEl = document.getElementById('conversation');
const mailboxEl = document.getElementById('mailbox');
const navLogin = document.getElementById('nav-login');
const navLogout = document.getElementById('nav-logout');
const ticketsLimitSelect = document.getElementById('tickets-limit');
const ticketsCountEl = document.getElementById('tickets-count');

async function refreshAuth() {
  try {
    const res = await fetch('/auth/status', { credentials: 'include' });
    const data = await res.json();
    const isAuthed = !!data.authenticated;
    document.querySelectorAll('.gated').forEach(el => el.classList.toggle('hidden', !isAuthed));
    navLogin?.classList.toggle('hidden', isAuthed);
    navLogout?.classList.toggle('hidden', !isAuthed);
    return isAuthed;
  } catch {
    return false;
  }
}

navLogout?.addEventListener('click', async () => {
  try { await fetch('/auth/logout', { method: 'POST', credentials: 'include' }); } catch {}
  location.href = '/ui/admin-login.html';
});

async function loadConfig() {
  try {
    const res = await fetch('/config', { credentials: 'include' });
    const data = await res.json();
    mailboxEl.textContent = data.mailbox || '-';
  } catch { mailboxEl.textContent = '-'; }
}

async function loadTickets() {
  if (!tbody) {
    console.error('tbody element not found');
    return;
  }
  
  const limit = ticketsLimitSelect ? parseInt(ticketsLimitSelect.value) || 50 : 50;
  
  tbody.innerHTML = '<tr><td colspan="8" class="muted">Loading…</td></tr>';
  try {
    const res = await fetch(`/tickets?limit=${limit}`, { credentials: 'include' });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    console.log('Received tickets data:', data); // Debug log
    
    // Update count display
    if (ticketsCountEl) {
      const totalCount = data.count || (data.tickets ? data.tickets.length : 0);
      ticketsCountEl.textContent = `(${totalCount} tickets)`;
    }
    
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
    
    if (!tickets.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="muted">No tickets</td></tr>';
      return;
    }
    
    tbody.innerHTML = '';
    // Use traditional for loop instead of for...of for better error handling
    for (let i = 0; i < tickets.length; i++) {
      const t = tickets[i];
      
      // Skip if t is null or undefined
      if (t == null) {
        console.warn('Skipping null/undefined ticket at index', i);
        continue;
      }
      
      try {
        // Handle both array format and object format
        let ticketId, convId, subject, sender, body, date, assigned, intent, response;
        
        if (Array.isArray(t)) {
          // Array format: [ticket_id, conversation_id, message_id, subject, sender, body, date, assigned_agent, intent, response]
          [ticketId, convId, , subject, sender, body, date, assigned, intent, response] = t;
        } else if (typeof t === 'object' && t !== null) {
          // Object format (dictionary)
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
        
        // Format agent name - replace email with "Mail Agent" if it's the default
        const displayAgent = (assigned === 'human_review_pool@example.com' || assigned === 'Mail Agent') 
          ? 'Mail Agent' 
          : assigned || '-';
        
        // Format date to be more readable
        let displayDate = date || '';
        if (displayDate && displayDate.includes('T')) {
          try {
            const dateObj = new Date(displayDate);
            displayDate = dateObj.toLocaleString();
          } catch (e) {
            // Keep original format if parsing fails
          }
        }
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${escapeHtml(ticketId || 'N/A')}</td>
          <td>${escapeHtml(sender || 'Unknown')}</td>
          <td>${escapeHtml(mailboxEl?.textContent || '')}</td>
          <td>${escapeHtml(subject || 'No subject')}</td>
          <td>${escapeHtml(displayDate)}</td>
          <td>${escapeHtml(displayAgent)}</td>
          <td>${escapeHtml(intent || '-')}</td>
          <td><button class="view-btn" data-conv-id="${escapeHtml(convId || '')}">View</button></td>
        `;
        
        // Add click handler to the button
        const viewBtn = tr.querySelector('.view-btn');
        if (viewBtn && convId) {
          viewBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            showConversation(convId);
          });
        }
        
        tbody.appendChild(tr);
      } catch (err) {
        console.error('Error processing ticket at index', i, ':', err, t);
        continue; // Skip this ticket and continue
      }
    }
  } catch (error) {
    console.error('Error loading tickets:', error);
    tbody.innerHTML = `<tr><td colspan="8" class="muted">Failed to load: ${error.message || 'Unknown error'}</td></tr>`;
  }
}

function escapeHtml(str) {
  return (str || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

async function showConversation(convId) {
  if (!convId) {
    console.error('No conversation ID provided');
    conversationEl.innerHTML = '<div style="padding: 16px; background: #f8d7da; border-left: 4px solid #dc3545; border-radius: 4px; color: #721c24;">Error: No conversation ID</div>';
    return;
  }
  
  conversationEl.innerHTML = '<div style="padding: 16px; text-align: center; color: #6c757d;">Loading…</div>';
  try {
    // Get conversation history
    const res = await fetch(`/tickets/conversation/${encodeURIComponent(convId)}`, { credentials: 'include' });
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    
    // Get ticket details to show incoming email and reply
    const ticketsRes = await fetch('/tickets', { credentials: 'include' });
    if (!ticketsRes.ok) {
      throw new Error('Failed to load tickets');
    }
    const ticketsData = await ticketsRes.json();
    const tickets = ticketsData.tickets || [];
    
    // Find the ticket for this conversation
    const ticket = tickets.find(t => {
      const ticketConvId = Array.isArray(t) ? t[1] : (t.conversation_id || t.conv_id);
      return ticketConvId === convId;
    });
    
    let conversationHtml = '';
    
    if (ticket) {
      // Extract ticket data
      let body, response, intent, subject, sender;
      if (Array.isArray(ticket)) {
        body = ticket[5] || '';
        response = ticket[9] || '';
        intent = ticket[8] || '';
        subject = ticket[3] || '';
        sender = ticket[4] || '';
      } else {
        body = ticket.body || '';
        response = ticket.response || '';
        intent = ticket.intent || '';
        subject = ticket.subject || '';
        sender = ticket.sender || ticket.from || '';
      }
      
      // Show incoming email
      conversationHtml += `<div style="margin-bottom: 20px; padding: 16px; background: #f8f9fa; border-left: 4px solid #0066cc; border-radius: 4px;">
        <h4 style="margin: 0 0 12px 0; color: #0066cc; font-size: 16px;">📧 Incoming Email</h4>
        <div style="margin-bottom: 8px; font-size: 14px; color: #6c757d;"><strong>From:</strong> ${escapeHtml(sender)}</div>
        <div style="margin-bottom: 8px; font-size: 14px; color: #6c757d;"><strong>Subject:</strong> ${escapeHtml(subject || 'No subject')}</div>
        <div style="white-space: pre-wrap; font-family: inherit; line-height: 1.6; margin-top: 12px;">${escapeHtml(body || 'No content')}</div>
      </div>`;
      
      // Show reply if available
      if (response && response.trim() && response !== 'SPAM' && intent !== 'SPAM') {
        conversationHtml += `<div style="margin-bottom: 20px; padding: 16px; background: #e8f5e9; border-left: 4px solid #28a745; border-radius: 4px;">
          <h4 style="margin: 0 0 12px 0; color: #28a745; font-size: 16px;">✉️ Reply Sent</h4>
          <div style="white-space: pre-wrap; font-family: inherit; line-height: 1.6;">${escapeHtml(response)}</div>
        </div>`;
      } else if (intent === 'SPAM') {
        conversationHtml += `<div style="margin-bottom: 20px; padding: 16px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
          <h4 style="margin: 0 0 12px 0; color: #856404; font-size: 16px;">⚠️ Status</h4>
          <div>This email was classified as SPAM. No reply was sent.</div>
        </div>`;
      } else {
        conversationHtml += `<div style="margin-bottom: 20px; padding: 16px; background: #fff3cd; border-left: 4px solid #ffc107; border-radius: 4px;">
          <h4 style="margin: 0 0 12px 0; color: #856404; font-size: 16px;">⏳ Status</h4>
          <div>No reply has been sent yet. This ticket is pending processing.</div>
        </div>`;
      }
      
      // Show full conversation history if available and different
      if (data.history && data.history.trim() && data.history !== body) {
        conversationHtml += `<div style="margin-top: 20px; padding: 16px; background: #f8f9fa; border-radius: 4px;">
          <h4 style="margin: 0 0 12px 0; color: #495057; font-size: 16px;">📋 Full Conversation History</h4>
          <pre style="white-space: pre-wrap; font-family: inherit; line-height: 1.6; margin: 0;">${escapeHtml(data.history)}</pre>
        </div>`;
      }
    } else {
      // Fallback to just showing history
      conversationHtml = `<div style="padding: 16px; background: #f8f9fa; border-radius: 4px;">
        <h4 style="margin: 0 0 12px 0; color: #495057; font-size: 16px;">📋 Conversation History</h4>
        <pre style="white-space: pre-wrap; font-family: inherit; line-height: 1.6; margin: 0;">${escapeHtml(data.history || 'No conversation history available')}</pre>
      </div>`;
    }
    
    conversationEl.innerHTML = conversationHtml;
  } catch (error) {
    console.error('Error loading conversation:', error);
    conversationEl.innerHTML = `<div style="padding: 16px; background: #f8d7da; border-left: 4px solid #dc3545; border-radius: 4px; color: #721c24;">
      <strong>Error:</strong> Failed to load conversation: ${error.message || 'Unknown error'}
    </div>`;
  }
}

refreshBtn?.addEventListener('click', loadTickets);

// Add pagination change handler
ticketsLimitSelect?.addEventListener('change', loadTickets);

(async function init() {
  await loadConfig();
  const ok = await refreshAuth();
  if (ok) {
    await loadTickets();
  } else {
    window.location.href = '/ui/admin-login.html';
  }
})();


