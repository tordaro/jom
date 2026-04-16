document.addEventListener('DOMContentLoaded', () => {
    fetchUsersSummary();
});

const formatterNOK = new Intl.NumberFormat('no-NO', { style: 'currency', currency: 'NOK' });
const formatterKWH = new Intl.NumberFormat('no-NO', { maximumFractionDigits: 2 });

const elements = {
    usersList: document.getElementById('users-list-container'),
    historyTbody: document.getElementById('history-tbody'),
    historyHeader: document.getElementById('history-header'),
    monthlyAggregates: document.getElementById('monthly-aggregates-container'),
    detailedStatsContainer: document.getElementById('detailed-stats-container'),
    yearFilter: document.getElementById('global-year-filter')
};

// Global State
let allUsersSummary = [];
let currentUserAggregates = null;
let currentRawHistory = [];
let currentMonthlyAggregates = [];
let currentSelectedMonth = null;

// Set up global year filter when DOM loads
document.addEventListener('DOMContentLoaded', () => {
    elements.yearFilter.addEventListener('change', () => {
        // Reset currently selected user view since data changed globally
        currentUserAggregates = null;
        currentSelectedMonth = null;
        elements.detailedStatsContainer.style.display = 'none';
        elements.historyHeader.innerHTML = `
            <h2>Charging History</h2>
            <p class="subtitle">Select a user from the leaderboard</p>
        `;
        elements.monthlyAggregates.innerHTML = '';
        elements.historyTbody.innerHTML = `
            <tr class="empty-state-row">
                <td colspan="8" class="empty-state">No user selected</td>
            </tr>
        `;
        fetchUsersSummary();
    });
});

function getYearQueryString() {
    const year = elements.yearFilter.value;
    return year ? `year=${year}` : '';
}

async function fetchUsersSummary() {
    try {
        const query = getYearQueryString();
        const url = `/charging/api/costs/summary${query ? '?' + query : ''}`;
        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch summary');
        allUsersSummary = await response.json();
        renderUsers(allUsersSummary);
    } catch (error) {
        console.error('Error fetching users:', error);
        elements.usersList.innerHTML = `<div class="loading-state" style="color: #ef4444;">Error loading data</div>`;
    }
}

function renderUsers(users) {
    if (users.length === 0) {
        elements.usersList.innerHTML = `<div class="loading-state">No users found.</div>`;
        return;
    }
    
    // Sort by total cost descending
    users.sort((a, b) => b.total_cost - a.total_cost);

    elements.usersList.innerHTML = '';
    
    users.forEach(user => {
        const card = document.createElement('div');
        card.className = 'user-card';
        card.dataset.userId = user.user_id;
        
        const userName = user.user ? user.user.trim() : 'Unknown User';
        const sessions = user.charging_sessions || 0;
        const total = parseFloat(user.total_cost || 0);
        const kwh = parseFloat(user.energy || 0);
        
        card.innerHTML = `
            <div class="user-info">
                <div class="name">${userName}</div>
                <div class="sessions">${sessions} session${sessions !== 1 ? 's' : ''}</div>
            </div>
            <div class="user-stats">
                <div class="total">${formatterNOK.format(total)}</div>
                <div class="kwh">${formatterKWH.format(kwh)} kWh</div>
            </div>
        `;
        
        card.addEventListener('click', () => {
            document.querySelectorAll('.user-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            
            currentUserAggregates = user;
            currentSelectedMonth = null;
            
            elements.historyHeader.innerHTML = `
                <h2>${userName}'s History</h2>
                <p class="subtitle">All-time overview</p>
            `;
            
            renderDetailedStats(currentUserAggregates);
            fetchUserHistory(user.user_id);
        });
        
        elements.usersList.appendChild(card);
    });
}

function renderDetailedStats(aggParams) {
    elements.detailedStatsContainer.style.display = 'grid';
    elements.detailedStatsContainer.innerHTML = `
        <div class="stat-box"><span class="label">Total Energy</span><span class="value active">${formatterKWH.format(parseFloat(aggParams.energy || 0))} kWh</span></div>
        <div class="stat-box"><span class="label">Total Cost</span><span class="value highlight">${formatterNOK.format(parseFloat(aggParams.total_cost || 0))}</span></div>
        <div class="stat-box"><span class="label">Grid Cost</span><span class="value grid">${formatterNOK.format(parseFloat(aggParams.grid_cost || 0))}</span></div>
        <div class="stat-box"><span class="label">Spot Cost</span><span class="value spot">${formatterNOK.format(parseFloat(aggParams.spot_cost || 0))}</span></div>
        <div class="stat-box"><span class="label">Usage Cost</span><span class="value usage">${formatterNOK.format(parseFloat(aggParams.usage_cost || 0))}</span></div>
        <div class="stat-box"><span class="label">Fund Cost</span><span class="value">${formatterNOK.format(parseFloat(aggParams.fund_cost || 0))}</span></div>
        <div class="stat-box"><span class="label">Refund</span><span class="value refund">${formatterNOK.format(parseFloat(aggParams.refund || 0))}</span></div>
        <div class="stat-box"><span class="label">Sessions</span><span class="value">${aggParams.charging_sessions || aggParams.sessions || 0}</span></div>
    `;
}

async function fetchUserHistory(userId) {
    elements.historyTbody.innerHTML = `
        <tr>
            <td colspan="8" style="text-align: center; padding: 3rem; color: #94A3B8;">Loading history <span class="pulse" style="display:inline-block; margin-left: 10px;"></span></td>
        </tr>
    `;
    elements.monthlyAggregates.innerHTML = ``;
    
    try {
        const yearParam = getYearQueryString();
        const queryStr = yearParam ? `&${yearParam}` : '';
        const [rawResponse, monthResponse] = await Promise.all([
            fetch(`/charging/api/costs/history?user_id=${userId}${queryStr}`),
            fetch(`/charging/api/costs/monthly_history?user_id=${userId}${queryStr}`)
        ]);
        
        if (!rawResponse.ok || !monthResponse.ok) throw new Error('Failed to fetch history');
        
        currentRawHistory = await rawResponse.json();
        currentMonthlyAggregates = await monthResponse.json();
        
        renderMonthlyAggregates();
        renderHistory();
    } catch (error) {
        console.error('Error fetching history:', error);
        elements.historyTbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 3rem; color: #ef4444;">Error loading history</td>
            </tr>
        `;
    }
}

function renderMonthlyAggregates() {
    elements.monthlyAggregates.innerHTML = '';
    
    if (!currentMonthlyAggregates || currentMonthlyAggregates.length === 0) return;

    currentMonthlyAggregates.forEach((m, idx) => {
        const dateObj = new Date(m.month);
        const monthName = dateObj.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        const isSelected = currentSelectedMonth === m.month;
        
        const card = document.createElement('div');
        card.className = 'monthly-card';
        card.dataset.month = m.month;
        if (isSelected) card.style.borderColor = 'var(--clr-accent)';
        
        card.style.opacity = '0';
        card.style.animation = `fadeIn 0.3s forwards ${idx * 0.05}s`;
        card.style.cursor = 'pointer';
        
        const total = parseFloat(m.total_cost || 0);
        const energy = parseFloat(m.energy || 0);
        const sessions = m.charging_sessions || 0;
        
        card.innerHTML = `
            <div class="month-label" style="${isSelected ? 'color: var(--clr-accent);' : 'color: var(--clr-text-muted);'}">${monthName}</div>
            <div class="month-cost">${formatterNOK.format(total)}</div>
            <div class="month-stats">
                <span>${formatterKWH.format(energy)} kWh</span>
                <span>${sessions} session${sessions !== 1 ? 's' : ''}</span>
            </div>
        `;
        
        card.addEventListener('click', () => {
            if (currentSelectedMonth === m.month) {
                // Deselect
                currentSelectedMonth = null;
                elements.historyHeader.querySelector('.subtitle').textContent = "All-time overview";
                renderDetailedStats(currentUserAggregates);
            } else {
                // Select
                currentSelectedMonth = m.month;
                elements.historyHeader.querySelector('.subtitle').textContent = `Overview for ${monthName}`;
                renderDetailedStats(m);
            }
            
            // Update node visuals directly without rerendering
            document.querySelectorAll('.monthly-card').forEach(c => {
                const label = c.querySelector('.month-label');
                if (c.dataset.month === currentSelectedMonth) {
                    c.style.borderColor = 'var(--clr-accent)';
                    if(label) label.style.color = 'var(--clr-accent)';
                } else {
                    c.style.borderColor = ''; // falls back to CSS default hover/normal
                    if(label) label.style.color = 'var(--clr-text-muted)';
                }
            });
            
            renderHistory(); // filter history list
        });
        
        elements.monthlyAggregates.appendChild(card);
    });
}

function renderHistory() {
    let sessionsToRender = currentRawHistory;
    
    if (currentSelectedMonth) {
        sessionsToRender = currentRawHistory.filter(session => {
            const sessionDate = new Date(session.timestamp);
            const targetDate = new Date(currentSelectedMonth);
            return sessionDate.getFullYear() === targetDate.getFullYear() && 
                   sessionDate.getMonth() === targetDate.getMonth();
        });
    }

    if (sessionsToRender.length === 0) {
        elements.historyTbody.innerHTML = `
            <tr class="empty-state-row">
                <td colspan="8" class="empty-state">No charging sessions found in this view.</td>
            </tr>
        `;
        return;
    }
    
    elements.historyTbody.innerHTML = '';
    
    sessionsToRender.forEach(session => {
        const tr = document.createElement('tr');
        
        const ts = new Date(session.timestamp);
        const dateStr = ts.toLocaleDateString('no-NO') + ' ' + ts.toLocaleTimeString('no-NO', { hour: '2-digit', minute: '2-digit' });
        
        const energy = parseFloat(session.energy || 0);
        const total = parseFloat(session.total_cost || 0);
        const spot = parseFloat(session.spot_cost || 0);
        const grid = parseFloat(session.grid_cost || 0);
        const usage = parseFloat(session.usage_cost || 0);
        const fund = parseFloat(session.fund_cost || 0);
        const refund = parseFloat(session.refund || 0);
        
        tr.innerHTML = `
            <td>${dateStr}</td>
            <td>${formatterKWH.format(energy)}</td>
            <td class="highlight-cost">${formatterNOK.format(total)}</td>
            <td>${formatterNOK.format(spot)}</td>
            <td>${formatterNOK.format(grid)}</td>
            <td>${formatterNOK.format(usage)}</td>
            <td>${formatterNOK.format(fund)}</td>
            <td>${formatterNOK.format(refund)}</td>
        `;
        
        tr.style.opacity = '0';
        tr.style.animation = 'fadeIn 0.3s forwards';
        elements.historyTbody.appendChild(tr);
    });
}

const style = document.createElement('style');
style.innerHTML = `
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(5px); }
    to { opacity: 1; transform: translateY(0); }
}
`;
document.head.appendChild(style);
