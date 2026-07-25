/**
 * HerWellness Hub - Single Page Application (SPA) Master Script
 * Plain ES6 JavaScript (No external frameworks)
 */

const API_BASE = '/api';

// Application State
const state = {
    user: null,
    token: localStorage.getItem('herwellness_token') || null,
    currentView: 'dashboard',
    currentDate: new Date(),
    currentCalYear: new Date().getFullYear(),
    currentCalMonth: new Date().getMonth(), // 0-indexed
    cyclePredictions: null,
    cycleLogs: [],
    moodLogs: [],
    fitnessLogs: [],
    articles: [],
    myths: [],
    selectedArticleCategory: 'All',
    selectedMoodValue: 3
};

// Initialize Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    updateDateBadge();
    
    // Check authentication or demo state
    if (state.token) {
        try {
            const user = await apiCall('/auth/me');
            state.user = user;
            updateUserUI();
            navigate('dashboard');
        } catch (e) {
            console.warn('Auth token invalid or demo fallback:', e);
            enableDemoMode();
        }
    } else {
        // Default to login view
        navigate('login');
    }

    // Attach Event Listeners
    setupMoodSelectors();
    setupArticleSearch();
}

/**
 * Central API Call Helper
 */
async function apiCall(endpoint, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json'
    };

    if (state.token) {
        headers['Authorization'] = `Bearer ${state.token}`;
    }

    const options = {
        method,
        headers
    };

    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Network request failed' }));
        throw new Error(errorData.detail || 'API request failed');
    }

    return await response.json();
}

/**
 * View Navigation Manager
 */
function navigate(viewId) {
    // If not logged in, restrict to login view
    if (!state.token && viewId !== 'login') {
        viewId = 'login';
    }

    // Hide all view sections
    document.querySelectorAll('.app-view').forEach(el => el.classList.add('hidden'));

    // Show selected view
    const targetView = document.getElementById(`view-${viewId}`);
    if (targetView) {
        targetView.classList.remove('hidden');
        state.currentView = viewId;
    }

    // Update Nav Active State
    document.querySelectorAll('.nav-btn').forEach(btn => {
        if (btn.dataset.view === viewId) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // View specific initializations
    if (viewId === 'dashboard') {
        loadDashboardData();
    } else if (viewId === 'tracker') {
        loadTrackerData();
    } else if (viewId === 'wellness') {
        loadWellnessData();
    } else if (viewId === 'fitness') {
        loadFitnessData();
    } else if (viewId === 'library') {
        loadLibraryData();
    }
}

/* ==========================================================================
   AUTHENTICATION & DEMO MODE LOGIC
   ========================================================================== */

function switchAuthTab(tab) {
    const formLogin = document.getElementById('form-login');
    const formSignup = document.getElementById('form-signup');
    const tabLogin = document.getElementById('tab-login-btn');
    const tabSignup = document.getElementById('tab-signup-btn');
    const alertBox = document.getElementById('auth-alert');

    alertBox.classList.add('hidden');

    if (tab === 'login') {
        formLogin.classList.remove('hidden');
        formSignup.classList.add('hidden');
        tabLogin.classList.add('active');
        tabSignup.classList.remove('active');
    } else {
        formLogin.classList.add('hidden');
        formSignup.classList.remove('hidden');
        tabLogin.classList.remove('active');
        tabSignup.classList.add('active');
    }
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const data = await apiCall('/auth/login', 'POST', { email, password });
        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('herwellness_token', state.token);
        updateUserUI();
        showAuthAlert('Login successful! Redirecting...', 'success');
        setTimeout(() => navigate('dashboard'), 600);
    } catch (err) {
        showAuthAlert(err.message, 'error');
    }
}

async function handleSignupSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;

    try {
        const data = await apiCall('/auth/signup', 'POST', { email, password });
        state.token = data.access_token;
        state.user = data.user;
        localStorage.setItem('herwellness_token', state.token);
        updateUserUI();
        showAuthAlert('Account created successfully!', 'success');
        setTimeout(() => navigate('dashboard'), 600);
    } catch (err) {
        showAuthAlert(err.message, 'error');
    }
}

function enableDemoMode() {
    state.token = 'demo-token';
    state.user = { email: 'demo@herwellness.hub', id: 1 };
    localStorage.setItem('herwellness_token', 'demo-token');
    updateUserUI();
    navigate('dashboard');
}

function handleAuthAction() {
    if (state.token) {
        // Logout
        state.token = null;
        state.user = null;
        localStorage.removeItem('herwellness_token');
        updateUserUI();
        navigate('login');
    } else {
        navigate('login');
    }
}

function updateUserUI() {
    const userDisplay = document.getElementById('user-email-display');
    const authBtn = document.getElementById('auth-action-btn');
    const dashEmail = document.getElementById('dash-user-email');

    if (state.token && state.user) {
        userDisplay.textContent = state.user.email;
        authBtn.textContent = 'Logout';
        if (dashEmail) dashEmail.textContent = state.user.email.split('@')[0];
    } else {
        userDisplay.textContent = 'Guest';
        authBtn.textContent = 'Login';
    }
}

function showAuthAlert(msg, type) {
    const alertBox = document.getElementById('auth-alert');
    alertBox.textContent = msg;
    alertBox.className = `alert-message ${type}`;
    alertBox.classList.remove('hidden');
}


/* ==========================================================================
   VIEW 1: DASHBOARD
   ========================================================================== */

async function loadDashboardData() {
    try {
        // Fetch AI Health Summary Header
        await loadAIHealthSummary();

        // Fetch cycle predictions
        const predictions = await apiCall('/cycle/predictions');
        state.cyclePredictions = predictions;
        renderDashboardCycle(predictions);

        // Fetch workout recommendation
        const fitRecs = await apiCall('/fitness/recommendations');
        renderDashboardWorkout(fitRecs);

        // Fetch mood trends
        const moodTrends = await apiCall('/mood/trends');
        renderMiniMoodChart(moodTrends);

        // Fetch Health Insight of the day
        const articles = await apiCall('/health/articles');
        if (articles.length > 0) {
            renderDashboardArticle(articles[0]);
        }
    } catch (err) {
        console.error('Error loading dashboard data:', err);
    }
}

async function loadAIHealthSummary() {
    try {
        const summary = await apiCall('/health/summary');
        renderAIHealthSummary(summary);
    } catch (err) {
        console.warn('Error fetching AI health summary:', err);
    }
}

function renderAIHealthSummary(data) {
    if (!data) return;

    const greetingEl = document.getElementById('ai-summary-greeting');
    if (greetingEl && data.greeting) greetingEl.textContent = data.greeting;

    const scoreEl = document.getElementById('ai-wellness-score');
    if (scoreEl) scoreEl.textContent = data.wellness_score || 87;

    const bulletsList = document.getElementById('ai-summary-bullets');
    if (bulletsList && data.bullets) {
        bulletsList.innerHTML = data.bullets.map(b => `<li>${b.startsWith('•') ? b : '• ' + b}</li>`).join('');
    }

    const recEl = document.getElementById('ai-recommendation-text');
    if (recEl && data.ai_recommendation) {
        recEl.textContent = `"${data.ai_recommendation}"`;
    }

    // 5 Health metrics
    const mWellness = document.getElementById('metric-wellness-score');
    if (mWellness) mWellness.textContent = `${data.wellness_score || 87}/100`;

    const mAi = document.getElementById('metric-ai-score');
    if (mAi) mAi.textContent = `${data.ai_health_score || 89}/100`;

    const mSleep = document.getElementById('metric-sleep-quality');
    if (mSleep) mSleep.textContent = data.sleep_quality || '8.2 hrs • Restorative';

    const mStress = document.getElementById('metric-stress-level');
    if (mStress) mStress.textContent = data.stress_level || 'Low (22%)';

    const mHydration = document.getElementById('metric-hydration');
    if (mHydration) mHydration.textContent = data.hydration || '2.4L Goal';
}


function renderDashboardCycle(pred) {
    document.getElementById('dash-phase-badge').textContent = pred.current_phase;
    document.getElementById('dash-cycle-day').textContent = pred.current_cycle_day;
    document.getElementById('dash-next-period').textContent = formatDateStr(pred.predicted_next_period);
    document.getElementById('dash-fertile-window').textContent = `${formatDateShort(pred.fertile_window_start)} - ${formatDateShort(pred.fertile_window_end)}`;
    document.getElementById('dash-avg-cycle').textContent = `${pred.average_cycle_length} Days`;
    document.getElementById('dash-phase-desc').textContent = pred.phase_description;
}

function renderDashboardWorkout(data) {
    document.getElementById('dash-rec-phase-tag').textContent = data.cycle_phase;
    if (data.recommendations && data.recommendations.length > 0) {
        const rec = data.recommendations[0];
        document.getElementById('dash-workout-title').textContent = rec.title;
        document.getElementById('dash-workout-desc').textContent = rec.description;
        document.getElementById('dash-workout-duration').textContent = rec.duration;
        document.getElementById('dash-workout-intensity').textContent = `${rec.intensity} Intensity`;
    }
}

function renderDashboardArticle(article) {
    document.getElementById('dash-art-category').textContent = article.category;
    document.getElementById('dash-art-title').textContent = article.title;
    document.getElementById('dash-art-summary').textContent = article.summary;
}

function renderMiniMoodChart(trendsData) {
    const canvas = document.getElementById('mini-mood-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const trends = trendsData.weekly_trends || [];
    if (trends.length === 0) return;

    const barWidth = 40;
    const gap = 25;
    const startX = 30;
    const maxHeight = 100;
    const chartBottom = 130;

    trends.forEach((item, index) => {
        const x = startX + index * (barWidth + gap);
        // Mood is 1 to 5 scale
        const height = (item.average_mood / 5) * maxHeight;
        const y = chartBottom - height;

        // Bar gradient
        const gradient = ctx.createLinearGradient(0, y, 0, chartBottom);
        gradient.addColorStop(0, '#db2777');
        gradient.addColorStop(1, '#fbcfe8');

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, height, [6, 6, 0, 0]);
        ctx.fill();

        // Mood text value on top of bar
        ctx.fillStyle = '#1e293b';
        ctx.font = 'bold 12px "Plus Jakarta Sans"';
        ctx.textAlign = 'center';
        ctx.fillText(item.average_mood.toFixed(1), x + barWidth / 2, y - 6);

        // Label below bar
        ctx.fillStyle = '#64748b';
        ctx.font = '10px "Plus Jakarta Sans"';
        ctx.fillText(item.week_label, x + barWidth / 2, chartBottom + 18);
    });
}

function setupMoodSelectors() {
    // Quick mood check-in on dashboard
    document.querySelectorAll('#dash-emoji-selector .emoji-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const moodVal = parseInt(btn.dataset.mood);
            document.querySelectorAll('#dash-emoji-selector .emoji-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            
            try {
                await apiCall('/mood/log', 'POST', {
                    date: getTodayString(),
                    mood: moodVal
                });
                const status = document.getElementById('dash-mood-status');
                status.classList.remove('hidden');
                setTimeout(() => status.classList.add('hidden'), 3000);
            } catch (err) {
                console.error('Error logging mood:', err);
            }
        });
    });

    // Detailed mood selector in Wellness section
    document.querySelectorAll('#wellness-emoji-selector .emoji-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('#wellness-emoji-selector .emoji-btn').forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            state.selectedMoodValue = parseInt(btn.dataset.mood);
        });
    });
}


/* ==========================================================================
   VIEW 2: PERIOD TRACKER & CALENDAR
   ========================================================================== */

async function loadTrackerData() {
    try {
        const predictions = await apiCall('/cycle/predictions');
        state.cyclePredictions = predictions;
        renderTrackerPredictions(predictions);

        // Fetch logs for calendar display
        const logs = await apiCall('/cycle/logs');
        state.cycleLogs = logs;

        renderCalendar(state.currentCalYear, state.currentCalMonth);
        renderCycleHistory(logs);
    } catch (err) {
        console.error('Error loading tracker data:', err);
    }
}

function renderTrackerPredictions(pred) {
    document.getElementById('track-avg-cycle').textContent = `${pred.average_cycle_length} Days`;
    document.getElementById('track-next-period').textContent = formatDateStr(pred.predicted_next_period);
    document.getElementById('track-ovulation').textContent = formatDateStr(pred.ovulation_date);
    document.getElementById('track-fertile-window').textContent = `${formatDateShort(pred.fertile_window_start)} - ${formatDateShort(pred.fertile_window_end)}`;
    document.getElementById('track-current-phase').textContent = pred.current_phase;
}

function renderCalendar(year, month) {
    const grid = document.getElementById('calendar-days-grid');
    grid.innerHTML = '';

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    document.getElementById('cal-month-year').textContent = `${monthNames[month]} ${year}`;

    const firstDayIndex = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const prevMonthDays = new Date(year, month, 0).getDate();

    // Previous month padding days
    for (let i = firstDayIndex; i > 0; i--) {
        const dayCell = document.createElement('div');
        dayCell.className = 'cal-day-cell other-month';
        dayCell.innerHTML = `<span class="day-number">${prevMonthDays - i + 1}</span>`;
        grid.appendChild(dayCell);
    }

    // Current month days
    const todayStr = getTodayString();

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayCell = document.createElement('div');
        dayCell.className = 'cal-day-cell';

        if (dateStr === todayStr) {
            dayCell.classList.add('today');
        }

        // Check if log exists for this date
        const log = state.cycleLogs.find(l => l.date === dateStr);
        let indicatorsHTML = '';

        if (log) {
            if (log.period_start || (log.flow_intensity && log.flow_intensity > 0)) {
                dayCell.classList.add('is-period');
                indicatorsHTML += `<span class="dot dot-period"></span>`;
                if (log.flow_intensity) {
                    indicatorsHTML += `<span class="day-flow-tag">F${log.flow_intensity}</span>`;
                }
            } else {
                indicatorsHTML += `<span class="dot dot-logged"></span>`;
            }
        }

        // Check predictions for fertile/predicted period highlights
        if (state.cyclePredictions) {
            const predNext = state.cyclePredictions.predicted_next_period;
            if (predNext && predNext.startsWith(dateStr)) {
                dayCell.classList.add('is-predicted');
                indicatorsHTML += `<span class="dot dot-predicted" title="Predicted Period"></span>`;
            }

            const fertStart = state.cyclePredictions.fertile_window_start;
            const fertEnd = state.cyclePredictions.fertile_window_end;
            if (fertStart && fertEnd && dateStr >= fertStart && dateStr <= fertEnd) {
                dayCell.classList.add('is-fertile');
            }
        }

        dayCell.innerHTML = `
            <span class="day-number">${day}</span>
            <div class="day-indicators">${indicatorsHTML}</div>
        `;

        dayCell.addEventListener('click', () => openLogModal(dateStr));
        grid.appendChild(dayCell);
    }
}

function changeMonth(delta) {
    state.currentCalMonth += delta;
    if (state.currentCalMonth < 0) {
        state.currentCalMonth = 11;
        state.currentCalYear--;
    } else if (state.currentCalMonth > 11) {
        state.currentCalMonth = 0;
        state.currentCalYear++;
    }
    renderCalendar(state.currentCalYear, state.currentCalMonth);
}

function renderCycleHistory(logs) {
    const listContainer = document.getElementById('cycle-history-list');
    const periodStarts = logs.filter(l => l.period_start).sort((a, b) => new Date(b.date) - new Date(a.date));

    if (periodStarts.length === 0) {
        listContainer.innerHTML = `<p class="empty-state">No cycle start entries logged yet. Click a calendar date to log!</p>`;
        return;
    }

    let html = '';
    periodStarts.forEach(item => {
        html += `
            <div class="history-item">
                <strong>🩸 Period Start: ${formatDateStr(item.date)}</strong>
                <p>Flow: ${getFlowName(item.flow_intensity)} ${item.symptoms ? '| Symptoms: ' + item.symptoms : ''}</p>
            </div>
        `;
    });
    listContainer.innerHTML = html;
}

function openLogModal(dateStr) {
    document.getElementById('modal-log-date-display').textContent = formatDateStr(dateStr);
    document.getElementById('log-date-input').value = dateStr;

    // Pre-fill existing data if logged
    const existingLog = state.cycleLogs.find(l => l.date === dateStr);
    if (existingLog) {
        document.getElementById('log-period-start').checked = existingLog.period_start || false;
        document.getElementById('log-period-end').checked = existingLog.period_end || false;
        document.getElementById('log-flow').value = existingLog.flow_intensity || '';
        document.getElementById('log-notes').value = existingLog.notes || '';

        const activeSymptoms = (existingLog.symptoms || '').split(',');
        document.querySelectorAll('#symptom-chips-container input').forEach(chip => {
            chip.checked = activeSymptoms.includes(chip.value);
        });
    } else {
        document.getElementById('form-cycle-log').reset();
    }

    document.getElementById('modal-cycle-log').classList.remove('hidden');
}

async function handleCycleLogSubmit(e) {
    e.preventDefault();
    const dateStr = document.getElementById('log-date-input').value;
    const periodStart = document.getElementById('log-period-start').checked;
    const periodEnd = document.getElementById('log-period-end').checked;
    const flowVal = document.getElementById('log-flow').value;
    const notes = document.getElementById('log-notes').value;

    const selectedSymptoms = [];
    document.querySelectorAll('#symptom-chips-container input:checked').forEach(chip => {
        selectedSymptoms.push(chip.value);
    });

    try {
        await apiCall('/cycle/log', 'POST', {
            date: dateStr,
            period_start: periodStart,
            period_end: periodEnd,
            flow_intensity: flowVal ? parseInt(flowVal) : null,
            symptoms: selectedSymptoms.join(','),
            notes: notes
        });

        closeModal('modal-cycle-log');
        loadTrackerData(); // Refresh tracker view
    } catch (err) {
        alert('Error saving cycle log: ' + err.message);
    }
}


/* ==========================================================================
   VIEW 3: MENTAL WELLNESS & VERA CHATBOT
   ========================================================================== */

async function loadWellnessData() {
    document.getElementById('wellness-log-date').value = getTodayString();
    
    try {
        const moodLogs = await apiCall('/mood/logs');
        state.moodLogs = moodLogs;
        renderMoodTrendChart(moodLogs);
    } catch (err) {
        console.error('Error loading wellness logs:', err);
    }
}

async function submitMoodLog() {
    const logDate = document.getElementById('wellness-log-date').value;
    const journalText = document.getElementById('wellness-journal-text').value;

    try {
        await apiCall('/mood/log', 'POST', {
            date: logDate,
            mood: state.selectedMoodValue,
            journal: journalText
        });
        alert('Mood and journal entry saved successfully! 💖');
        loadWellnessData();
    } catch (err) {
        alert('Error saving mood entry: ' + err.message);
    }
}

function renderMoodTrendChart(logs) {
    const canvas = document.getElementById('mood-trend-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!logs || logs.length === 0) {
        ctx.fillStyle = '#64748b';
        ctx.font = '14px "Plus Jakarta Sans"';
        ctx.textAlign = 'center';
        ctx.fillText('No mood history logged yet.', canvas.width / 2, canvas.height / 2);
        return;
    }

    // Sort logs by date ascending
    const sorted = [...logs].sort((a, b) => new Date(a.date) - new Date(b.date)).slice(-14);
    
    const padding = 40;
    const width = canvas.width - padding * 2;
    const height = canvas.height - padding * 2;
    const stepX = width / (Math.max(sorted.length - 1, 1));

    // Draw grid background lines
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    for (let i = 1; i <= 5; i++) {
        const y = canvas.height - padding - ((i / 5) * height);
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(canvas.width - padding, y);
        ctx.stroke();
    }

    // Draw mood trend line
    ctx.beginPath();
    ctx.strokeStyle = '#db2777';
    ctx.lineWidth = 3;

    sorted.forEach((item, index) => {
        const x = padding + index * stepX;
        const y = canvas.height - padding - ((item.mood / 5) * height);
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();

    // Draw mood data points
    sorted.forEach((item, index) => {
        const x = padding + index * stepX;
        const y = canvas.height - padding - ((item.mood / 5) * height);

        ctx.fillStyle = '#db2777';
        ctx.beginPath();
        ctx.arc(x, y, 6, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = '#ffffff';
        ctx.beginPath();
        ctx.arc(x, y, 3, 0, Math.PI * 2);
        ctx.fill();
    });
}

/* Chatbot Functions */
async function handleChatSubmit(e) {
    e.preventDefault();
    const inputField = document.getElementById('chat-input');
    const msg = inputField.value.trim();
    if (!msg) return;

    appendChatMessage(msg, 'user');
    inputField.value = '';

    // Show typing indicator
    const typingId = appendTypingIndicator();

    try {
        const response = await apiCall('/wellness/chat', 'POST', { message: msg });
        removeTypingIndicator(typingId);
        appendChatMessage(response.response, 'vera');
    } catch (err) {
        removeTypingIndicator(typingId);
        appendChatMessage('I am here with you, but I encountered a momentary connection issue. Take a deep breath.', 'vera');
    }
}

function sendQuickPrompt(promptText) {
    document.getElementById('chat-input').value = promptText;
    handleChatSubmit(new Event('submit'));
}

function appendChatMessage(text, sender) {
    const container = document.getElementById('chat-messages-container');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message message-${sender}`;
    
    const formattedText = text.replace(/\n/g, '<br>');
    msgDiv.innerHTML = `
        <div class="message-bubble">${formattedText}</div>
        <span class="message-time">${sender === 'user' ? 'You' : 'Vera'}</span>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function appendTypingIndicator() {
    const container = document.getElementById('chat-messages-container');
    const id = 'typing-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message message-vera';
    msgDiv.id = id;
    msgDiv.innerHTML = `
        <div class="message-bubble" style="font-style: italic; color: #64748b;">
            Vera is typing... 🌸
        </div>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}


/* ==========================================================================
   VIEW 4: FITNESS
   ========================================================================== */

async function loadFitnessData() {
    try {
        const recsData = await apiCall('/fitness/recommendations');
        renderFitnessRecommendations(recsData);

        const logs = await apiCall('/fitness/logs');
        state.fitnessLogs = logs;
        renderFitnessStatsAndHistory(logs);
    } catch (err) {
        console.error('Error loading fitness data:', err);
    }
}

function renderFitnessRecommendations(data) {
    document.getElementById('fitness-current-phase-title').textContent = `${data.cycle_phase} Phase Fitness Guide`;
    
    const grid = document.getElementById('fitness-recommendations-grid');
    grid.innerHTML = '';

    (data.recommendations || []).forEach(rec => {
        const card = document.createElement('div');
        card.className = 'workout-card';
        card.innerHTML = `
            <div class="rec-tags margin-top-5">
                <span class="category-pill">${rec.category}</span>
                <span class="badge badge-accent">${rec.duration}</span>
                <span class="badge">${rec.intensity} Intensity</span>
            </div>
            <h4 class="margin-top-10">${rec.title}</h4>
            <p>${rec.description}</p>
            <div class="workout-benefits">💡 <strong>Benefits:</strong> ${rec.benefits}</div>
            <button class="btn btn-sm btn-outline margin-top-auto" onclick="quickLogWorkout('${rec.title}', '${rec.duration}')">Log This Workout</button>
        `;
        grid.appendChild(card);
    });
}

function renderFitnessStatsAndHistory(logs) {
    // Stats calculation (last 7 days)
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);

    const recentLogs = logs.filter(l => new Date(l.date) >= sevenDaysAgo);
    const totalMinutes = recentLogs.reduce((acc, curr) => acc + curr.duration_minutes, 0);
    const uniqueDays = new Set(recentLogs.map(l => l.date)).size;

    document.getElementById('fit-stat-days').textContent = uniqueDays;
    document.getElementById('fit-stat-minutes').textContent = totalMinutes;

    // History rendering
    const listContainer = document.getElementById('fitness-history-list');
    if (logs.length === 0) {
        listContainer.innerHTML = `<p class="empty-state">No workouts logged yet.</p>`;
        return;
    }

    let html = '';
    logs.slice(0, 8).forEach(item => {
        html += `
            <div class="history-item">
                <strong>🏃‍♀️ ${item.workout_type} (${item.duration_minutes} mins)</strong>
                <p>Date: ${formatDateStr(item.date)} ${item.notes ? '| Notes: ' + item.notes : ''}</p>
            </div>
        `;
    });
    listContainer.innerHTML = html;
}

function openLogWorkoutModal() {
    document.getElementById('workout-date').value = getTodayString();
    document.getElementById('modal-workout-log').classList.remove('hidden');
}

function quickLogWorkout(type, durationStr) {
    const minutes = parseInt(durationStr) || 30;
    document.getElementById('workout-date').value = getTodayString();
    document.getElementById('workout-type').value = type;
    document.getElementById('workout-duration').value = minutes;
    document.getElementById('modal-workout-log').classList.remove('hidden');
}

async function handleWorkoutLogSubmit(e) {
    e.preventDefault();
    const dateStr = document.getElementById('workout-date').value;
    const type = document.getElementById('workout-type').value;
    const duration = parseInt(document.getElementById('workout-duration').value);
    const notes = document.getElementById('workout-notes').value;

    try {
        await apiCall('/fitness/log', 'POST', {
            date: dateStr,
            workout_type: type,
            duration_minutes: duration,
            notes: notes
        });

        closeModal('modal-workout-log');
        loadFitnessData();
    } catch (err) {
        alert('Error logging workout: ' + err.message);
    }
}


/* ==========================================================================
   VIEW 5: HEALTH LIBRARY & MYTH BUSTERS
   ========================================================================== */

async function loadLibraryData() {
    try {
        const articles = await apiCall('/health/articles');
        state.articles = articles;
        renderArticles(articles);

        const myths = await apiCall('/health/myths');
        state.myths = myths;
        renderMythCards(myths);
    } catch (err) {
        console.error('Error loading health library data:', err);
    }
}

function renderArticles(articlesList) {
    const grid = document.getElementById('articles-grid');
    grid.innerHTML = '';

    if (articlesList.length === 0) {
        grid.innerHTML = `<p class="empty-state span-full">No articles matching your search criteria.</p>`;
        return;
    }

    articlesList.forEach(art => {
        const card = document.createElement('div');
        card.className = 'article-card';
        card.innerHTML = `
            <span class="category-pill">${art.category}</span>
            <h4>${art.title}</h4>
            <p>${art.summary}</p>
            <button class="btn btn-sm btn-outline margin-top-auto" onclick="openArticleModal(${art.id})">Read Article →</button>
        `;
        grid.appendChild(card);
    });
}

function renderMythCards(mythsList) {
    const container = document.getElementById('myth-cards-container');
    container.innerHTML = '';

    mythsList.forEach(item => {
        const card = document.createElement('div');
        card.className = 'myth-card-3d';
        card.innerHTML = `
            <div class="myth-card-inner">
                <div class="myth-card-front">
                    <span class="myth-tag tag-myth">MYTH</span>
                    <p class="myth-text">"${item.myth}"</p>
                    <span class="flip-hint">Click card to reveal fact 🔄</span>
                </div>
                <div class="myth-card-back">
                    <span class="myth-tag tag-fact">MEDICAL FACT</span>
                    <p class="myth-text">${item.fact}</p>
                </div>
            </div>
        `;
        card.addEventListener('click', () => {
            card.classList.toggle('flipped');
        });
        container.appendChild(card);
    });
}

function selectCategoryFilter(category) {
    state.selectedArticleCategory = category;
    document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.dataset.category === category) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    filterArticles();
}

function setupArticleSearch() {
    const input = document.getElementById('library-search-input');
    if (input) {
        input.addEventListener('input', filterArticles);
    }
}

function filterArticles() {
    const query = (document.getElementById('library-search-input').value || '').toLowerCase();
    const cat = state.selectedArticleCategory;

    const filtered = state.articles.filter(art => {
        const matchesCat = (cat === 'All' || art.category === cat);
        const matchesQuery = art.title.toLowerCase().includes(query) || art.summary.toLowerCase().includes(query);
        return matchesCat && matchesQuery;
    });

    renderArticles(filtered);
}

function openArticleModal(articleId) {
    const article = state.articles.find(a => a.id === articleId);
    if (!article) return;

    document.getElementById('article-modal-category').textContent = article.category;
    document.getElementById('article-modal-title').textContent = article.title;

    // Convert simple markdown headings & lists to HTML
    let formattedContent = article.content
        .replace(/### (.*)/g, '<h3>$1</h3>')
        .replace(/#### (.*)/g, '<h4>$1</h4>')
        .replace(/- \*\*(.*)\*\*/g, '<ul><li><strong>$1</strong>')
        .replace(/1\. \*\*(.*)\*\*/g, '<ol><li><strong>$1</strong>')
        .replace(/\n\n/g, '<p></p>');

    if (article.myth && article.fact) {
        formattedContent += `
            <div class="myth-buster-box margin-top-20" style="background:#f8fafc; padding:16px; border-radius:8px; border-left:4px solid #db2777;">
                <p style="color:#dc2626; font-weight:bold;">❌ Common Myth: "${article.myth}"</p>
                <p style="color:#16a34a; font-weight:bold; margin-top:6px;">✅ Medical Fact: ${article.fact}</p>
            </div>
        `;
    }

    document.getElementById('article-modal-body').innerHTML = formattedContent;
    document.getElementById('modal-article').classList.remove('hidden');
}


/* ==========================================================================
   UTILITY & MODAL HELPERS
   ========================================================================== */

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

function openHelplineModal() {
    document.getElementById('modal-helpline').classList.remove('hidden');
}

function getTodayString() {
    const d = new Date();
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function updateDateBadge() {
    const badge = document.getElementById('current-date-badge');
    if (badge) {
        const options = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
        badge.textContent = new Date().toLocaleDateString('en-US', options);
    }
}

function formatDateStr(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateShort(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function getFlowName(intensity) {
    switch (intensity) {
        case 1: return '1 (Spotting)';
        case 2: return '2 (Light)';
        case 3: return '3 (Medium)';
        case 4: return '4 (Heavy)';
        default: return 'Not Logged';
    }
}
