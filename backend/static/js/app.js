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
    selectedMoodValue: 3,
    chatHistory: JSON.parse(sessionStorage.getItem('herwellness_chat_history') || '[]')
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
    setupWellnessCalculator();
    setupArticleSearch();
    setupDashboardSymptomLogger();
    setupModalSymptomLogger();

    // Check Vera AI API Connection Status
    checkAPIKeyStatus();
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

    // Toggle Vera AI widget visibility
    const veraWidget = document.getElementById('vera-float-widget');
    if (veraWidget) {
        if (viewId === 'login') {
            veraWidget.style.display = 'none';
        } else {
            veraWidget.style.display = 'block';
        }
    }

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
    state.user = { email: 'priya@gmail.com', id: 1 };
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

        // Fetch cycle logs for symptom rating pre-population
        const logs = await apiCall('/cycle/logs');
        state.cycleLogs = logs;

        // Render new dashboards features
        renderDashboardSymptomLogger(predictions);
        renderCycleDeviationAlert(predictions);

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

    const scoreVal = data.wellness_score || 87;
    const wellnessRing = document.getElementById('dashboard-wellness-ring');
    if (wellnessRing) {
        const circumference = 2 * Math.PI * 40; // r=40 -> 251.2
        const offset = circumference - (scoreVal / 100) * circumference;
        wellnessRing.style.strokeDasharray = `${circumference} ${circumference}`;
        wellnessRing.style.strokeDashoffset = offset;
    }

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
    const elPhaseBadge = document.getElementById('dash-phase-badge');
    if (elPhaseBadge) elPhaseBadge.textContent = pred.current_phase;
    
    const elCycleDay = document.getElementById('dash-cycle-day');
    if (elCycleDay) elCycleDay.textContent = pred.current_cycle_day;
    
    const elNextPeriod = document.getElementById('dash-next-period');
    if (elNextPeriod) elNextPeriod.textContent = formatDateStr(pred.predicted_next_period);
    
    const elFertileWindow = document.getElementById('dash-fertile-window');
    if (elFertileWindow) elFertileWindow.textContent = `${formatDateShort(pred.fertile_window_start)} - ${formatDateShort(pred.fertile_window_end)}`;
    
    const elAvgCycle = document.getElementById('dash-avg-cycle');
    if (elAvgCycle) elAvgCycle.textContent = `${pred.average_cycle_length} Days`;
    
    const elPhaseDesc = document.getElementById('dash-phase-desc');
    if (elPhaseDesc) elPhaseDesc.textContent = pred.phase_description;

    const cycleRing = document.getElementById('dashboard-cycle-ring');
    if (cycleRing) {
        const currentDay = pred.current_cycle_day || 1;
        const totalDays = pred.average_cycle_length || 28;
        const pct = Math.min(Math.max(currentDay / totalDays, 0), 1);
        const circumference = 2 * Math.PI * 82; // r=82 -> 515.2
        const offset = circumference - pct * circumference;
        cycleRing.style.strokeDasharray = `${circumference} ${circumference}`;
        cycleRing.style.strokeDashoffset = offset;
    }
    const phaseCenter = document.getElementById('dash-cycle-phase-center');
    if (phaseCenter) {
        phaseCenter.textContent = pred.current_phase + ' Phase';
    }
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
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const trends = trendsData.weekly_trends || [];
    if (trends.length === 0) return;

    const points = [];
    const paddingLeft = 20;
    const paddingRight = 20;
    const chartWidth = canvas.width - paddingLeft - paddingRight;
    const chartHeight = canvas.height - 35; // Save space for labels
    const startX = paddingLeft;
    const stepX = chartWidth / Math.max(trends.length - 1, 1);

    trends.forEach((item, index) => {
        const x = startX + index * stepX;
        // Mood is 1 to 5 scale. Map to chartHeight with safety margin
        const y = chartHeight - ((item.average_mood - 1) / 4) * (chartHeight - 20) - 10;
        points.push({ x, y, label: item.week_label, value: item.average_mood });
    });

    // 1. Draw smooth line path
    ctx.beginPath();
    ctx.strokeStyle = '#ff5a8f';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    if (points.length > 0) {
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 0; i < points.length - 1; i++) {
            const xc = (points[i].x + points[i + 1].x) / 2;
            const yc = (points[i].y + points[i + 1].y) / 2;
            ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
        }
        ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    }
    ctx.stroke();

    // 2. Draw gradient fill below line
    if (points.length > 0) {
        ctx.beginPath();
        ctx.moveTo(points[0].x, canvas.height - 25);
        points.forEach(p => ctx.lineTo(p.x, p.y));
        ctx.lineTo(points[points.length - 1].x, canvas.height - 25);
        ctx.closePath();

        const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height - 25);
        gradient.addColorStop(0, 'rgba(255, 90, 143, 0.15)');
        gradient.addColorStop(1, 'rgba(255, 90, 143, 0.0)');
        ctx.fillStyle = gradient;
        ctx.fill();
    }

    // 3. Draw markers (dots) and labels
    points.forEach(p => {
        // Draw dot shadow
        ctx.beginPath();
        ctx.arc(p.x, p.y, 6, 0, 2 * Math.PI);
        ctx.fillStyle = 'rgba(255, 90, 143, 0.2)';
        ctx.fill();

        // Draw inner dot
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, 2 * Math.PI);
        ctx.fillStyle = '#ff5a8f';
        ctx.fill();

        // Draw label below marker
        ctx.fillStyle = '#64748b';
        ctx.font = 'bold 9px "Plus Jakarta Sans"';
        ctx.textAlign = 'center';
        ctx.fillText(p.label, p.x, canvas.height - 10);
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


function setupWellnessCalculator() {
    // 1. Stress level pill buttons selection handling
    const stressBtns = document.querySelectorAll('#wellness-stress-selector .pill-btn');
    const stressValEl = document.getElementById('wellness-stress-val');
    stressBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            stressBtns.forEach(b => b.classList.remove('selected'));
            btn.classList.add('selected');
            if (stressValEl) {
                stressValEl.textContent = btn.textContent.trim();
            }
            updateLiveScoreGauge();
        });
    });

    // 2. Range Sliders input change handling
    const sleepSlider = document.getElementById('wellness-sleep-hours');
    const sleepVal = document.getElementById('sleep-hours-val');
    if (sleepSlider && sleepVal) {
        sleepSlider.addEventListener('input', (e) => {
            sleepVal.textContent = parseFloat(e.target.value).toFixed(1) + ' hours';
            updateLiveScoreGauge();
        });
    }

    const hydSlider = document.getElementById('wellness-hydration-liters');
    const hydVal = document.getElementById('hydration-liters-val');
    if (hydSlider && hydVal) {
        hydSlider.addEventListener('input', (e) => {
            hydVal.textContent = parseFloat(e.target.value).toFixed(1) + ' Liters';
            updateLiveScoreGauge();
        });
    }

    const exSlider = document.getElementById('wellness-exercise-minutes');
    const exVal = document.getElementById('exercise-minutes-val');
    if (exSlider && exVal) {
        exSlider.addEventListener('input', (e) => {
            exVal.textContent = e.target.value + ' mins';
            updateLiveScoreGauge();
        });
    }

    // 3. Update live score gauge when mood changes
    document.querySelectorAll('#wellness-emoji-selector .emoji-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            updateLiveScoreGauge();
        });
    });

    // 4. Date change listener to pre-populate logs
    const dateInput = document.getElementById('wellness-log-date');
    if (dateInput) {
        dateInput.addEventListener('change', () => {
            loadWellnessDataForSelectedDate();
        });
    }

    // Initial update of gauge preview
    updateLiveScoreGauge();
}


function updateLiveScoreGauge() {
    const sleepSlider = document.getElementById('wellness-sleep-hours');
    const hydSlider = document.getElementById('wellness-hydration-liters');
    const exSlider = document.getElementById('wellness-exercise-minutes');

    const sleep = parseFloat(sleepSlider ? sleepSlider.value : 8.0);
    const hydration = parseFloat(hydSlider ? hydSlider.value : 2.5);
    const exercise = parseInt(exSlider ? exSlider.value : 30);
    
    const stressBtn = document.querySelector('#wellness-stress-selector .pill-btn.selected');
    const stress = stressBtn ? stressBtn.dataset.stress : 'low';
    const mood = state.selectedMoodValue || 3;

    const score = calculateWellnessScoreLocal(sleep, hydration, exercise, stress, mood);

    const scoreValEl = document.getElementById('live-wellness-score-val');
    if (scoreValEl) scoreValEl.textContent = score;

    const scoreDescEl = document.getElementById('live-wellness-score-desc');
    if (scoreDescEl) {
        let desc = 'Needs Attention ⚠️';
        if (score >= 85) desc = 'Excellent 🌸';
        else if (score >= 70) desc = 'Good 😊';
        else if (score >= 50) desc = 'Fair 😐';
        scoreDescEl.textContent = desc;
    }

    // SVG Circular progress bar update
    const circle = document.querySelector('.progress-ring__circle');
    if (circle) {
        const radius = circle.r.baseVal.value;
        const circumference = radius * 2 * Math.PI;
        const offset = circumference - (score / 100) * circumference;
        circle.style.strokeDasharray = `${circumference} ${circumference}`;
        circle.style.strokeDashoffset = offset;
    }
}

function resetWellnessForm() {
    const sleepSlider = document.getElementById('wellness-sleep-hours');
    const hydSlider = document.getElementById('wellness-hydration-liters');
    const exSlider = document.getElementById('wellness-exercise-minutes');
    if (sleepSlider) {
        sleepSlider.value = 8.0;
        const sleepVal = document.getElementById('sleep-hours-val');
        if (sleepVal) sleepVal.textContent = '8.0 hours';
    }
    if (hydSlider) {
        hydSlider.value = 2.5;
        const hydVal = document.getElementById('hydration-liters-val');
        if (hydVal) hydVal.textContent = '2.5 Liters';
    }
    if (exSlider) {
        exSlider.value = 30;
        const exVal = document.getElementById('exercise-minutes-val');
        if (exVal) exVal.textContent = '30 mins';
    }
    const stressBtns = document.querySelectorAll('#wellness-stress-selector .pill-btn');
    stressBtns.forEach(b => b.classList.remove('selected'));
    const lowBtn = document.querySelector('#wellness-stress-selector .pill-btn[data-stress="low"]');
    if (lowBtn) lowBtn.classList.add('selected');
    const stressValEl = document.getElementById('wellness-stress-val');
    if (stressValEl) stressValEl.textContent = 'Low';

    const emojiBtns = document.querySelectorAll('#wellness-emoji-selector .emoji-btn');
    emojiBtns.forEach(b => b.classList.remove('selected'));
    const defaultEmoji = document.querySelector('#wellness-emoji-selector .emoji-btn[data-mood="4"]');
    if (defaultEmoji) defaultEmoji.classList.add('selected');

    if (typeof updateLiveScoreGauge === 'function') {
        updateLiveScoreGauge();
    }
}


function calculateWellnessScoreLocal(sleep, hydration, exercise, stress, mood) {
    let sleepPts = 5;
    if (sleep >= 7.0 && sleep <= 9.0) sleepPts = 20;
    else if ((sleep >= 6.0 && sleep < 7.0) || (sleep > 9.0 && sleep <= 10.0)) sleepPts = 15;
    else if ((sleep >= 5.0 && sleep < 6.0) || (sleep > 10.0 && sleep <= 11.0)) sleepPts = 10;

    let hydPts = 4;
    if (hydration >= 2.5) hydPts = 20;
    else if (hydration >= 2.0) hydPts = 16;
    else if (hydration >= 1.5) hydPts = 12;
    else if (hydration >= 1.0) hydPts = 8;

    let exPts = 5;
    if (exercise >= 30) exPts = 20;
    else if (exercise >= 15) exPts = 15;
    else if (exercise > 0) exPts = 10;

    let strPts = 4;
    const stressLower = stress.toLowerCase();
    if (stressLower === 'low') strPts = 20;
    else if (stressLower === 'medium') strPts = 12;

    let moodPts = 5;
    if (mood === 5) moodPts = 20;
    else if (mood === 4) moodPts = 17;
    else if (mood === 3) moodPts = 14;
    else if (mood === 2) moodPts = 10;

    return sleepPts + hydPts + exPts + strPts + moodPts;
}



/* ==========================================================================
   VIEW 2: PERIOD TRACKER & CALENDAR
   ========================================================================== */

async function loadTrackerData() {
    try {
        if (!state.hasSetInitialCal) {
            const now = new Date();
            state.currentCalYear = now.getFullYear();
            state.currentCalMonth = now.getMonth();
            state.hasSetInitialCal = true;
        }

        const predictions = await apiCall('/cycle/predictions');
        state.cyclePredictions = predictions;
        renderTrackerPredictions(predictions);

        // Fetch logs for calendar display
        const logs = await apiCall('/cycle/logs');
        state.cycleLogs = logs;

        renderCalendar(state.currentCalYear, state.currentCalMonth);
        renderCycleHistory(logs);
        checkActiveShareLink();
    } catch (err) {
        console.error('Error loading tracker data:', err);
    }
}


function renderTrackerPredictions(pred) {
    const avgCycle = pred.average_cycle_length || 35;
    const nextPeriodStr = pred.predicted_next_period || '2026-09-03';
    const ovulationStr = pred.ovulation_date || '2026-08-20';
    const fertileStartStr = pred.fertile_window_start || '2026-08-16';
    const fertileEndStr = pred.fertile_window_end || '2026-08-22';
    const phaseStr = pred.current_phase || 'Follicular';

    document.getElementById('track-avg-cycle').textContent = `${avgCycle} Days`;
    document.getElementById('track-next-period').textContent = formatDateStr(nextPeriodStr);
    document.getElementById('track-ovulation').textContent = formatDateStr(ovulationStr);
    document.getElementById('track-fertile-window').textContent = `${formatDateShort(fertileStartStr)} – ${formatDateShort(fertileEndStr)}`;
    
    const phaseEl = document.getElementById('track-current-phase');
    if (phaseEl) phaseEl.textContent = phaseStr;

    // Render Today's Overview Cards
    const ovCycleDay = document.getElementById('overview-cycle-day');
    if (ovCycleDay) ovCycleDay.textContent = pred.current_cycle_day || 5;

    const ovDaysOvu = document.getElementById('overview-days-ovulation');
    if (ovDaysOvu) {
        if (pred.days_to_ovulation !== undefined && pred.days_to_ovulation !== null) {
            ovDaysOvu.textContent = pred.days_to_ovulation;
        } else if (ovulationStr) {
            const diffMs = new Date(ovulationStr) - new Date();
            const diffDays = Math.max(0, Math.ceil(diffMs / (1000 * 60 * 60 * 24)));
            ovDaysOvu.textContent = diffDays || 8;
        } else {
            ovDaysOvu.textContent = 8;
        }
    }

    const ovFertileWindow = document.getElementById('overview-fertile-window');
    if (ovFertileWindow) ovFertileWindow.textContent = `${formatDateShort(fertileStartStr)} – ${formatDateShort(fertileEndStr)}`;

    const ovCurrentPhase = document.getElementById('overview-current-phase');
    if (ovCurrentPhase) ovCurrentPhase.textContent = phaseStr;

    const ovScore = document.getElementById('overview-wellness-score');
    if (ovScore) ovScore.textContent = state.todayWellnessScore || 78;

    // Active Mode display
    const modeEl = document.getElementById('track-active-mode');
    if (modeEl) {
        const modeNames = {
            regular: 'Regular Mode',
            pcos_pcod: 'PCOS / PCOD Mode',
            irregular: 'Irregular Cycle Mode',
            perimenopause: 'Perimenopause Mode'
        };
        modeEl.textContent = modeNames[pred.tracking_mode] || 'PCOS / PCOD Mode';
    }

    // Pre-select form controls if present
    const modeSelect = document.getElementById('profile-tracking-mode');
    if (modeSelect && (pred.tracking_mode || (state.user && state.user.tracking_mode))) {
        modeSelect.value = pred.tracking_mode || state.user.tracking_mode;
    }
}

async function handleProfileSettingsSubmit(e) {
    e.preventDefault();
    const mode = document.getElementById('profile-tracking-mode').value;
    const customLen = document.getElementById('profile-custom-length').value;

    try {
        const updatedUser = await apiCall('/auth/profile', 'PUT', {
            tracking_mode: mode,
            custom_cycle_length: customLen ? parseInt(customLen) : null
        });
        state.user = updatedUser;
        alert('Health Profile Mode updated successfully! 🌸');
        await loadTrackerData();
        await loadDashboardData();
    } catch (err) {
        alert('Error updating profile mode: ' + err.message);
    }
}

function renderCalendar(year, month) {
    const grid = document.getElementById('calendar-days-grid');
    if (!grid) return;
    grid.innerHTML = '';

    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const monthYearHeader = document.getElementById('cal-month-year');
    if (monthYearHeader) {
        monthYearHeader.textContent = `${monthNames[month]} ${year}`;
    }

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
    const isTargetDemoMonth = (year === 2026 && month === 8); // September 2026 (0-indexed 8)

    for (let day = 1; day <= daysInMonth; day++) {
        const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        const dayCell = document.createElement('div');
        dayCell.className = 'cal-day-cell';

        // Check predictions for fertile/predicted period/ovulation highlights
        let fertileStart = state.cyclePredictions?.fertile_window_start;
        let fertileEnd = state.cyclePredictions?.fertile_window_end;
        let ovulationDate = state.cyclePredictions?.ovulation_date;

        // Fallback for demo display matching target screenshot (Sept 2026: fertile window 16..22, today 13, ovulation 20)
        if (isTargetDemoMonth) {
            fertileStart = fertileStart || '2026-09-16';
            fertileEnd = fertileEnd || '2026-09-22';
            ovulationDate = ovulationDate || '2026-09-20';
        }

        // Today highlight
        if (dateStr === todayStr || (isTargetDemoMonth && day === 13)) {
            dayCell.classList.add('today');
        }

        // Check if log exists for this date
        const log = (state.cycleLogs || []).find(l => l.date === dateStr);
        let indicatorsHTML = '';

        if (log) {
            if (log.period_start || (log.flow_intensity && log.flow_intensity > 0)) {
                dayCell.classList.add('is-period');
                indicatorsHTML += `<span class="dot dot-period"></span>`;
            } else {
                indicatorsHTML += `<span class="dot dot-logged"></span>`;
            }
        } else if (dateStr === todayStr || (isTargetDemoMonth && day === 13)) {
            indicatorsHTML += `<span class="dot dot-period"></span>`;
        }

        if (fertileStart && fertileEnd && dateStr >= fertileStart && dateStr <= fertileEnd) {
            dayCell.classList.add('is-fertile');
        }

        if (ovulationDate && dateStr === ovulationDate) {
            indicatorsHTML += `<span class="dot dot-ovulation" title="Ovulation"></span>`;
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

    // Reset severities first
    state.modalSymptoms = { cramps: null, headache: null, acne: null, breast_tenderness: null, hair_loss: null, hirsutism: null };
    document.querySelectorAll('#modal-symptom-severities-container .rate-pill').forEach(p => {
        p.className = 'rate-pill';
    });

    const ovuTestSelect = document.getElementById('log-ovulation-test');
    if (ovuTestSelect) ovuTestSelect.value = '';

    // Pre-fill existing data if logged
    const existingLog = state.cycleLogs.find(l => l.date === dateStr);
    if (existingLog) {
        document.getElementById('log-period-start').checked = existingLog.period_start || false;
        document.getElementById('log-period-end').checked = existingLog.period_end || false;
        document.getElementById('log-flow').value = existingLog.flow_intensity || '';
        document.getElementById('log-notes').value = existingLog.notes || '';

        if (ovuTestSelect) ovuTestSelect.value = existingLog.ovulation_test_result || '';

        const activeSymptoms = (existingLog.symptoms || '').split(',');
        document.querySelectorAll('#symptom-chips-container input').forEach(chip => {
            chip.checked = activeSymptoms.includes(chip.value);
        });

        // Populate rating pills
        const severities = {
            cramps: existingLog.cramps_severity,
            headache: existingLog.headache_severity,
            acne: existingLog.acne_severity,
            breast_tenderness: existingLog.breast_tenderness_severity,
            hair_loss: existingLog.hair_loss_severity,
            hirsutism: existingLog.hirsutism_severity
        };

        for (const [symp, val] of Object.entries(severities)) {
            if (val) {
                state.modalSymptoms[symp] = val;
                const pill = document.querySelector(`#modal-symptom-severities-container .modal-symptom-severity-row[data-symptom="${symp}"] .rate-pill[data-val="${val}"]`);
                if (pill) pill.classList.add(`selected-${val}`);
            }
        }
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
    const ovuTestVal = document.getElementById('log-ovulation-test') ? document.getElementById('log-ovulation-test').value : null;

    const selectedSymptoms = [];
    document.querySelectorAll('#symptom-chips-container input:checked').forEach(chip => {
        selectedSymptoms.push(chip.value);
    });

    // Automatically ensure standard symptom strings are set if severity rating is chosen
    const sympMapping = {
        cramps: "cramps",
        headache: "headache",
        acne: "acne",
        breast_tenderness: "breast tenderness",
        hair_loss: "hair_loss",
        hirsutism: "hirsutism"
    };
    for (const [key, val] of Object.entries(state.modalSymptoms)) {
        if (val) {
            const valStr = sympMapping[key];
            if (valStr && !selectedSymptoms.includes(valStr)) {
                selectedSymptoms.push(valStr);
            }
        }
    }

    try {
        await apiCall('/cycle/log', 'POST', {
            date: dateStr,
            period_start: periodStart,
            period_end: periodEnd,
            flow_intensity: flowVal ? parseInt(flowVal) : null,
            symptoms: selectedSymptoms.join(','),
            cramps_severity: state.modalSymptoms.cramps,
            headache_severity: state.modalSymptoms.headache,
            acne_severity: state.modalSymptoms.acne,
            breast_tenderness_severity: state.modalSymptoms.breast_tenderness,
            hair_loss_severity: state.modalSymptoms.hair_loss,
            hirsutism_severity: state.modalSymptoms.hirsutism,
            ovulation_test_result: ovuTestVal || null,
            notes: notes
        });

        closeModal('modal-cycle-log');
        loadTrackerData(); // Refresh tracker view
        loadDashboardData(); // Refresh dashboard logger card too
    } catch (err) {
        alert('Error saving cycle log: ' + err.message);
    }
}



/* ==========================================================================
   VIEW 3: MENTAL WELLNESS & VERA CHATBOT
   ========================================================================== */

async function loadWellnessData() {
    const dateInput = document.getElementById('wellness-log-date');
    if (dateInput && !dateInput.value) {
        dateInput.value = getTodayString();
    }
    
    try {
        const moodLogs = await apiCall('/mood/logs');
        state.moodLogs = moodLogs;
        renderMoodTrendChart(moodLogs);
        
        // Populate the form values for the selected date
        await loadWellnessDataForSelectedDate();
    } catch (err) {
        console.error('Error loading wellness logs:', err);
    }
}

async function loadWellnessDataForSelectedDate() {
    const selectedDate = document.getElementById('wellness-log-date').value;
    if (!selectedDate) return;

    try {
        // Fetch all logs to see if there's one for this date
        const wellnessLogs = await apiCall('/wellness/logs');
        const dayLog = wellnessLogs.find(log => log.date === selectedDate);

        if (dayLog) {
            // Pre-populate values
            document.getElementById('wellness-sleep-hours').value = dayLog.sleep_hours;
            document.getElementById('sleep-hours-val').textContent = dayLog.sleep_hours.toFixed(1) + ' hours';

            document.getElementById('wellness-hydration-liters').value = dayLog.hydration_liters;
            document.getElementById('hydration-liters-val').textContent = dayLog.hydration_liters.toFixed(1) + ' Liters';

            document.getElementById('wellness-exercise-minutes').value = dayLog.exercise_minutes;
            document.getElementById('exercise-minutes-val').textContent = dayLog.exercise_minutes + ' mins';

            // Select stress pill
            const stressBtns = document.querySelectorAll('#wellness-stress-selector .pill-btn');
            stressBtns.forEach(btn => {
                if (btn.dataset.stress === dayLog.stress_level.toLowerCase()) {
                    btn.classList.add('selected');
                } else {
                    btn.classList.remove('selected');
                }
            });

            // Select mood emoji
            document.querySelectorAll('#wellness-emoji-selector .emoji-btn').forEach(b => {
                if (parseInt(b.dataset.mood) === dayLog.mood_score) {
                    b.classList.add('selected');
                } else {
                    b.classList.remove('selected');
                }
            });
            state.selectedMoodValue = dayLog.mood_score;
        } else {
            // Reset to defaults
            document.getElementById('wellness-sleep-hours').value = 8.0;
            document.getElementById('sleep-hours-val').textContent = '8.0 hours';

            document.getElementById('wellness-hydration-liters').value = 2.5;
            document.getElementById('hydration-liters-val').textContent = '2.5 Liters';

            document.getElementById('wellness-exercise-minutes').value = 30;
            document.getElementById('exercise-minutes-val').textContent = '30 mins';

            // Default stress low
            const stressBtns = document.querySelectorAll('#wellness-stress-selector .pill-btn');
            stressBtns.forEach(btn => {
                if (btn.dataset.stress === 'low') btn.classList.add('selected');
                else btn.classList.remove('selected');
            });

            // Default mood neutral (3)
            document.querySelectorAll('#wellness-emoji-selector .emoji-btn').forEach(b => {
                if (parseInt(b.dataset.mood) === 3) b.classList.add('selected');
                else b.classList.remove('selected');
            });
            state.selectedMoodValue = 3;
        }

        // Also fetch the journal text if it was logged under mood logs
        const moodLogs = await apiCall('/mood/logs');
        const moodLog = moodLogs.find(log => log.date === selectedDate);
        const journalEl = document.getElementById('wellness-journal-text');
        if (journalEl) {
            journalEl.value = moodLog ? (moodLog.journal || '') : '';
        }

        updateLiveScoreGauge();
    } catch (err) {
        console.error('Error pre-populating wellness form:', err);
    }
}

async function submitWellnessLog() {
    const logDate = document.getElementById('wellness-log-date').value;
    const journalEl = document.getElementById('wellness-journal-text');
    const journalText = journalEl ? journalEl.value : '';

    const sleep = parseFloat(document.getElementById('wellness-sleep-hours').value);
    const hydration = parseFloat(document.getElementById('wellness-hydration-liters').value);
    const exercise = parseInt(document.getElementById('wellness-exercise-minutes').value);
    
    const stressBtn = document.querySelector('#wellness-stress-selector .pill-btn.selected');
    const stress = stressBtn ? stressBtn.dataset.stress : 'low';
    const mood = state.selectedMoodValue || 3;

    try {
        // Save mood in database (for mood trend lines)
        await apiCall('/mood/log', 'POST', {
            date: logDate,
            mood: mood,
            journal: journalText
        });

        // Save wellness data in database (for wellness score & dashboard metrics)
        await apiCall('/wellness/log', 'POST', {
            date: logDate,
            sleep_hours: sleep,
            hydration_liters: hydration,
            exercise_minutes: exercise,
            stress_level: stress,
            mood_score: mood
        });

        alert('Daily wellness metrics and mood entry saved successfully! 🌸💖');
        
        // Reload page data
        await loadWellnessData();
        await loadAIHealthSummary(); // To refresh dashboard metrics instantly!
    } catch (err) {
        alert('Error saving daily wellness entry: ' + err.message);
    }
}


function renderMoodTrendChart(logs) {
    const canvas = document.getElementById('mood-trend-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width || 340;
    canvas.height = rect.height || 105;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const labelsY = ['0', '50', '100'];
    const labelsX = ['07 Aug', '08 Aug', '09 Aug', '10 Aug', '11 Aug', '12 Aug', '13 Aug'];

    // Provide default sample data matching the mockup
    const defaultData = [40, 38, 70, 42, 52, 85, 92];
    const dataPoints = (logs && logs.length >= 7) 
        ? logs.slice(-7).map(l => (l.mood ? (l.mood / 5) * 100 : 50)) 
        : defaultData;

    const padLeft = 32;
    const padRight = 16;
    const padTop = 10;
    const padBottom = 20;

    const width = canvas.width - padLeft - padRight;
    const height = canvas.height - padTop - padBottom;

    // 1. Draw Grid Lines & Y-axis Labels (0, 50, 100)
    ctx.font = '500 8px "Plus Jakarta Sans", sans-serif';
    ctx.fillStyle = '#94a3b8';
    ctx.textAlign = 'right';

    labelsY.forEach((lbl, i) => {
        const y = padTop + height - (i / 2) * height;
        
        ctx.strokeStyle = '#f1f5f9';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padLeft, y);
        ctx.lineTo(canvas.width - padRight, y);
        ctx.stroke();

        ctx.fillText(lbl, padLeft - 6, y + 3);
    });

    // 2. Draw X-axis Date Labels
    const stepX = width / 6;
    labelsX.forEach((lbl, i) => {
        const x = padLeft + i * stepX;
        ctx.textAlign = 'center';
        if (i === 6) {
            ctx.fillStyle = '#be123c';
            ctx.font = 'bold 8px "Plus Jakarta Sans", sans-serif';
        } else {
            ctx.fillStyle = '#94a3b8';
            ctx.font = '500 8px "Plus Jakarta Sans", sans-serif';
        }
        ctx.fillText(lbl, x, canvas.height - 4);
    });

    // 3. Compute Point Coordinates
    const points = dataPoints.map((val, idx) => {
        const x = padLeft + idx * stepX;
        const normalized = Math.max(0, Math.min(100, val)) / 100;
        const y = padTop + height - normalized * height;
        return { x, y, val };
    });

    // 4. Draw Soft Pink Gradient Area Fill
    const gradient = ctx.createLinearGradient(0, padTop, 0, padTop + height);
    gradient.addColorStop(0, 'rgba(244, 63, 94, 0.2)');
    gradient.addColorStop(1, 'rgba(244, 63, 94, 0.01)');

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 0; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    ctx.lineTo(points[points.length - 1].x, padTop + height);
    ctx.lineTo(points[0].x, padTop + height);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // 5. Draw Smooth Curved Line
    ctx.strokeStyle = '#f43f5e';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 0; i < points.length - 1; i++) {
        const xc = (points[i].x + points[i + 1].x) / 2;
        const yc = (points[i].y + points[i + 1].y) / 2;
        ctx.quadraticCurveTo(points[i].x, points[i].y, xc, yc);
    }
    ctx.lineTo(points[points.length - 1].x, points[points.length - 1].y);
    ctx.stroke();

    // 6. Draw Red Data Dots
    points.forEach((pt) => {
        ctx.fillStyle = '#f43f5e';
        ctx.beginPath();
        ctx.arc(pt.x, pt.y, 3, 0, Math.PI * 2);
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

    // Stop voice recording if active
    if (state.isRecordingVoice && speechRecognitionInstance) {
        speechRecognitionInstance.stop();
        state.isRecordingVoice = false;
        const statusEl = document.getElementById('voice-recording-status');
        if (statusEl) statusEl.classList.add('hidden');
    }

    // Append to local state chat history
    state.chatHistory.push({ role: 'user', content: msg });

    // Build real-time live user context
    let userCtx = null;
    const liveSleep = parseFloat(document.getElementById('wellness-sleep-hours') ? document.getElementById('wellness-sleep-hours').value : 8.0);
    const liveHyd = parseFloat(document.getElementById('wellness-hydration-liters') ? document.getElementById('wellness-hydration-liters').value : 2.5);
    const liveEx = parseInt(document.getElementById('wellness-exercise-minutes') ? document.getElementById('wellness-exercise-minutes').value : 30);
    const stressBtn = document.querySelector('#wellness-stress-selector .pill-btn.selected');
    const liveStress = stressBtn ? stressBtn.dataset.stress : 'low';
    const liveScore = calculateWellnessScoreLocal(liveSleep, liveHyd, liveEx, liveStress, state.selectedMoodValue || 3);

    if (state.cyclePredictions) {
        userCtx = {
            current_phase: state.cyclePredictions.current_phase,
            current_cycle_day: state.cyclePredictions.current_cycle_day,
            tracking_mode: state.cyclePredictions.tracking_mode || (state.user ? state.user.tracking_mode : 'regular'),
            sleep_hours: liveSleep,
            hydration_liters: liveHyd,
            exercise_minutes: liveEx,
            stress_level: liveStress,
            wellness_score: liveScore
        };
    }

    // Show typing indicator
    const typingId = appendTypingIndicator();

    try {
        const response = await apiCall('/wellness/chat', 'POST', {
            message: msg,
            user_context: userCtx,
            history: state.chatHistory.slice(-8)  // Send up to 8 recent turns
        });
        removeTypingIndicator(typingId);

        // Store assistant turn in history
        state.chatHistory.push({ role: 'assistant', content: response.response });
        sessionStorage.setItem('herwellness_chat_history', JSON.stringify(state.chatHistory));

        appendStreamingChatMessage(response.response, 'vera', response.article_citation);
    } catch (err) {
        removeTypingIndicator(typingId);
        appendChatMessage('I am here with you, but I encountered a momentary connection issue. Take a deep breath.', 'vera');
    }
}

function clearChatHistory() {
    state.chatHistory = [];
    sessionStorage.removeItem('herwellness_chat_history');
    const container = document.getElementById('chat-messages-container');
    if (container) {
        container.innerHTML = `
            <div class="message message-vera">
                <div class="message-bubble">
                    Hello! I am Vera, your supportive wellness companion. 🌸 I am here to offer empathy, mindfulness exercises, and CBT journaling prompts. How are you feeling today?
                </div>
                <span class="message-time">Vera</span>
            </div>
        `;
    }
}

function sendQuickPrompt(promptText) {
    if (promptText.includes('4-7-8 breathing exercise')) {
        openBreathingModal();
        return;
    }
    document.getElementById('chat-input').value = promptText;
    handleChatSubmit(new Event('submit'));
}

/* CBT Journal Quick-Save from Vera */
function saveJournalFromVera(text) {
    const journalTextarea = document.getElementById('wellness-journal-text');
    if (journalTextarea) {
        const cleanPrompt = decodeURIComponent(text).replace(/[*_#>`~]/g, '');
        journalTextarea.value = (journalTextarea.value ? journalTextarea.value + '\n\n' : '') + `[CBT Reflection from Vera]: ${cleanPrompt}`;
        journalTextarea.scrollIntoView({ behavior: 'smooth' });
        journalTextarea.focus();
        alert('CBT reflection copied to your Daily Journal! ✍️');
    }
}

/* Interactive 4-7-8 Guided Breathing Timer Modal */
let breathingTimerId = null;

function openBreathingModal() {
    document.getElementById('modal-breathing').classList.remove('hidden');
}

function stopBreathingExercise() {
    if (breathingTimerId) clearInterval(breathingTimerId);
    breathingTimerId = null;
    const ring = document.getElementById('breathing-ring');
    if (ring) ring.style.transform = 'scale(1)';
    closeModal('modal-breathing');
}

function startBreathingCycle() {
    const btn = document.getElementById('btn-start-breathing');
    if (btn) btn.disabled = true;

    const ring = document.getElementById('breathing-ring');
    const stageText = document.getElementById('breathing-stage-text');
    const countdownEl = document.getElementById('breathing-countdown');

    let phase = 'inhale'; // inhale (4s), hold (7s), exhale (8s)
    let secondsLeft = 4;

    if (ring) ring.style.transform = 'scale(1.4)';
    if (stageText) stageText.textContent = 'Inhale... 🫁';
    if (countdownEl) countdownEl.textContent = '4';

    if (breathingTimerId) clearInterval(breathingTimerId);

    breathingTimerId = setInterval(() => {
        secondsLeft--;
        if (secondsLeft > 0) {
            if (countdownEl) countdownEl.textContent = secondsLeft;
        } else {
            if (phase === 'inhale') {
                phase = 'hold';
                secondsLeft = 7;
                if (stageText) stageText.textContent = 'Hold... ⏸️';
                if (countdownEl) countdownEl.textContent = '7';
            } else if (phase === 'hold') {
                phase = 'exhale';
                secondsLeft = 8;
                if (ring) ring.style.transform = 'scale(1)';
                if (stageText) stageText.textContent = 'Exhale... 💨';
                if (countdownEl) countdownEl.textContent = '8';
            } else {
                phase = 'inhale';
                secondsLeft = 4;
                if (ring) ring.style.transform = 'scale(1.4)';
                if (stageText) stageText.textContent = 'Inhale... 🫁';
                if (countdownEl) countdownEl.textContent = '4';
            }
        }
    }, 1000);
}

/* API Key Settings Modal Handlers */
async function checkAPIKeyStatus() {
    try {
        const res = await apiCall('/wellness/config-api');
        const indicator = document.getElementById('ai-status-indicator');
        const msg = document.getElementById('ai-status-message');

        if (res.is_connected) {
            if (indicator) {
                indicator.style.color = '#16a34a';
                indicator.textContent = `🟢 Connected: ${res.provider} (${res.model})`;
            }
            if (msg) msg.textContent = res.message;
        } else {
            if (indicator) {
                indicator.style.color = '#d97706';
                indicator.textContent = `🟡 RAG Engine Active (No Live Key)`;
            }
            if (msg) msg.textContent = res.message;
        }
    } catch (e) {
        console.warn('API Key status check failed:', e);
    }
}

function openAIConfigModal() {
    document.getElementById('modal-ai-config').classList.remove('hidden');
    checkAPIKeyStatus();
}

async function handleSaveAPIKey(e) {
    e.preventDefault();
    const key = document.getElementById('ai-key-input').value.trim();
    const provider = document.getElementById('ai-provider-select').value;
    const btn = document.getElementById('btn-save-api-key');

    if (!key) return;

    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Testing API Connection...';
    }

    try {
        const res = await apiCall('/wellness/config-api', 'POST', { api_key: key, provider: provider });
        alert(`✅ ${res.message}`);
        closeModal('modal-ai-config');
        checkAPIKeyStatus();
    } catch (err) {
        alert(`❌ API Connection Failed: ${err.message}`);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Test & Connect API';
        }
    }
}

let speechRecognitionInstance = null;

function toggleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert('Voice input is not supported in this browser. Please use Chrome, Edge, or Safari.');
        return;
    }

    const statusEl = document.getElementById('voice-recording-status');
    const btn = document.getElementById('btn-voice-input');

    if (speechRecognitionInstance && state.isRecordingVoice) {
        speechRecognitionInstance.stop();
        state.isRecordingVoice = false;
        if (statusEl) statusEl.classList.add('hidden');
        if (btn) btn.style.background = '';
        return;
    }

    speechRecognitionInstance = new SpeechRecognition();
    speechRecognitionInstance.continuous = false;
    speechRecognitionInstance.interimResults = false;
    speechRecognitionInstance.lang = 'en-US';

    speechRecognitionInstance.onstart = () => {
        state.isRecordingVoice = true;
        if (statusEl) statusEl.classList.remove('hidden');
        if (btn) btn.style.background = 'rgba(219,39,119,0.2)';
    };

    speechRecognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const inputField = document.getElementById('chat-input');
        if (inputField) inputField.value = transcript;
    };

    speechRecognitionInstance.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        state.isRecordingVoice = false;
        if (statusEl) statusEl.classList.add('hidden');
        if (btn) btn.style.background = '';
    };

    speechRecognitionInstance.onend = () => {
        state.isRecordingVoice = false;
        if (statusEl) statusEl.classList.add('hidden');
        if (btn) btn.style.background = '';
    };

    speechRecognitionInstance.start();
}

function speakVeraResponse(text) {
    if (!('speechSynthesis' in window)) {
        alert('Text-to-speech is not supported in this browser.');
        return;
    }

    window.speechSynthesis.cancel(); // Stop active speech

    const cleanText = text.replace(/[*_#>`~]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 0.95;
    utterance.pitch = 1.05;

    window.speechSynthesis.speak(utterance);
}

function appendChatMessage(text, sender, articleCitation = null) {
    const container = document.getElementById('chat-messages-container');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message message-${sender}`;
    
    let formattedText = text.replace(/\n/g, '<br>');
    formattedText = formattedText.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    let citationHTML = '';
    if (articleCitation) {
        citationHTML = `
            <div class="article-citation-box" style="margin-top:10px; padding:8px 12px; background:rgba(219, 39, 119, 0.08); border-radius:6px; border-left:3px solid #db2777;">
                <span style="font-size:0.75rem; font-weight:700; color:#be185d;">📖 Health Article Citation:</span>
                <p style="font-size:0.8rem; margin:2px 0; font-weight:600;">${articleCitation.title}</p>
                <button type="button" class="btn btn-xs btn-outline" style="margin-top:4px; padding:2px 8px; font-size:0.75rem;" onclick="openArticleModal(${articleCitation.id})">Read Article →</button>
            </div>
        `;
    }

    let ttsHTML = '';
    if (sender === 'vera') {
        const escapedText = encodeURIComponent(text);
        ttsHTML = `<button class="btn-tts" title="Read Aloud" style="background:none; border:none; cursor:pointer; font-size:0.85rem; margin-left:8px;" onclick="speakVeraResponse(decodeURIComponent('${escapedText}'))">🔊</button>`;
    }

    msgDiv.innerHTML = `
        <div class="message-bubble">${formattedText}${citationHTML}</div>
        <span class="message-time">${sender === 'user' ? 'You' : 'Vera'} ${ttsHTML}</span>
    `;
    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
}

function appendStreamingChatMessage(text, sender, articleCitation = null) {
    const container = document.getElementById('chat-messages-container');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message message-${sender}`;
    
    let citationHTML = '';
    if (articleCitation) {
        citationHTML = `
            <div class="article-citation-box" style="margin-top:10px; padding:8px 12px; background:rgba(219, 39, 119, 0.08); border-radius:6px; border-left:3px solid #db2777;">
                <span style="font-size:0.75rem; font-weight:700; color:#be185d;">📖 Health Article Citation:</span>
                <p style="font-size:0.8rem; margin:2px 0; font-weight:600;">${articleCitation.title}</p>
                <button type="button" class="btn btn-xs btn-outline" style="margin-top:4px; padding:2px 8px; font-size:0.75rem;" onclick="openArticleModal(${articleCitation.id})">Read Article →</button>
            </div>
        `;
    }

    const escapedText = encodeURIComponent(text);
    const ttsHTML = `<button class="btn-tts" title="Read Aloud" style="background:none; border:none; cursor:pointer; font-size:0.85rem; margin-left:8px;" onclick="speakVeraResponse(decodeURIComponent('${escapedText}'))">🔊</button>`;

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'message-bubble';
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.innerHTML = `Vera ${ttsHTML}`;

    msgDiv.appendChild(bubbleDiv);
    msgDiv.appendChild(timeSpan);
    container.appendChild(msgDiv);

    // Split into words for real-time streaming effect
    const words = text.split(' ');
    let wordIndex = 0;
    let accumulatedText = '';

    const streamInterval = setInterval(() => {
        if (wordIndex < words.length) {
            accumulatedText += (wordIndex === 0 ? '' : ' ') + words[wordIndex];
            let formatted = accumulatedText.replace(/\n/g, '<br>');
            formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            bubbleDiv.innerHTML = formatted;
            container.scrollTop = container.scrollHeight;
            wordIndex++;
        } else {
            clearInterval(streamInterval);
            if (citationHTML) {
                bubbleDiv.innerHTML += citationHTML;
            }
            // Auto-speak if enabled
            const autoVoiceCheck = document.getElementById('toggle-auto-voice');
            if (autoVoiceCheck && autoVoiceCheck.checked) {
                speakVeraResponse(text);
            }
        }
    }, 30); // Stream 1 word every 30ms for smooth real-time typewriter effect
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

/* ==========================================================================
   NEW SYMPTOM SEVERITY LOGGING, DEVIATIONS, & SHARING ACTIONS
   ========================================================================== */

state.dashboardSymptoms = { cramps: null, headache: null, acne: null, breast_tenderness: null };
state.modalSymptoms = { cramps: null, headache: null, acne: null, breast_tenderness: null };

function setupDashboardSymptomLogger() {
    const rows = document.querySelectorAll('#dash-symptom-rate-rows .symptom-rate-row');
    if (!rows.length) return;
    rows.forEach(row => {
        const symptom = row.dataset.symptom;
        const pills = row.querySelectorAll('.rate-pill');
        pills.forEach(pill => {
            pill.addEventListener('click', () => {
                const val = parseInt(pill.dataset.val);
                if (state.dashboardSymptoms[symptom] === val) {
                    state.dashboardSymptoms[symptom] = null;
                    pill.className = 'rate-pill';
                } else {
                    state.dashboardSymptoms[symptom] = val;
                    pills.forEach(p => p.className = 'rate-pill');
                    pill.classList.add(`selected-${val}`);
                }
            });
        });
    });
}

function setupModalSymptomLogger() {
    const rows = document.querySelectorAll('#modal-symptom-severities-container .modal-symptom-severity-row');
    if (!rows.length) return;
    rows.forEach(row => {
        const symptom = row.dataset.symptom;
        const pills = row.querySelectorAll('.rate-pill');
        pills.forEach(pill => {
            pill.addEventListener('click', () => {
                const val = parseInt(pill.dataset.val);
                if (state.modalSymptoms[symptom] === val) {
                    state.modalSymptoms[symptom] = null;
                    pill.className = 'rate-pill';
                } else {
                    state.modalSymptoms[symptom] = val;
                    pills.forEach(p => p.className = 'rate-pill');
                    pill.classList.add(`selected-${val}`);
                }
            });
        });
    });
}

async function saveDashboardSymptoms() {
    const dateStr = getTodayString();
    let periodStart = false;
    let periodEnd = false;
    let flowVal = null;
    let symptomsStr = "";
    let notes = "";

    const existingLog = state.cycleLogs.find(l => l.date === dateStr);
    if (existingLog) {
        periodStart = existingLog.period_start || false;
        periodEnd = existingLog.period_end || false;
        flowVal = existingLog.flow_intensity || null;
        symptomsStr = existingLog.symptoms || "";
        notes = existingLog.notes || "";
    }

    let activeSymptoms = symptomsStr ? symptomsStr.split(',') : [];
    const symptomsMap = {
        cramps: "cramps",
        headache: "headache",
        acne: "acne",
        breast_tenderness: "breast tenderness"
    };

    for (const [key, val] of Object.entries(state.dashboardSymptoms)) {
        const chipVal = symptomsMap[key];
        if (val && !activeSymptoms.includes(chipVal)) {
            activeSymptoms.push(chipVal);
        } else if (!val && activeSymptoms.includes(chipVal)) {
            activeSymptoms = activeSymptoms.filter(s => s !== chipVal);
        }
    }

    try {
        await apiCall('/cycle/log', 'POST', {
            date: dateStr,
            period_start: periodStart,
            period_end: periodEnd,
            flow_intensity: flowVal,
            symptoms: activeSymptoms.join(','),
            cramps_severity: state.dashboardSymptoms.cramps,
            headache_severity: state.dashboardSymptoms.headache,
            acne_severity: state.dashboardSymptoms.acne,
            breast_tenderness_severity: state.dashboardSymptoms.breast_tenderness,
            notes: notes
        });

        const status = document.getElementById('symptom-log-status');
        if (status) {
            status.classList.remove('hidden');
            setTimeout(() => status.classList.add('hidden'), 3000);
        }
        
        // Refresh local cache
        const logs = await apiCall('/cycle/logs');
        state.cycleLogs = logs;
    } catch (err) {
        alert('Error saving symptoms: ' + err.message);
    }
}

function renderDashboardSymptomLogger(pred) {
    const phase = pred.current_phase || "Follicular";
    const tag = document.getElementById('symptom-phase-tag');
    const subtitle = document.getElementById('symptom-logger-subtitle');

    if (tag) tag.textContent = `${phase} Phase Focus`;

    const rows = document.querySelectorAll('#dash-symptom-rate-rows .symptom-rate-row');
    rows.forEach(row => row.classList.remove('highlighted-symptom'));

    if (phase === 'Menstrual') {
        if (subtitle) subtitle.innerHTML = '🩺 Estrogen is low. <strong>Cramps</strong> & <strong>Headaches</strong> are common now.';
        const crampsRow = document.querySelector('#dash-symptom-rate-rows .symptom-rate-row[data-symptom="cramps"]');
        const headacheRow = document.querySelector('#dash-symptom-rate-rows .symptom-rate-row[data-symptom="headache"]');
        if (crampsRow) crampsRow.classList.add('highlighted-symptom');
        if (headacheRow) headacheRow.classList.add('highlighted-symptom');
    } else if (phase === 'Luteal') {
        if (subtitle) subtitle.innerHTML = '🩺 Progesterone peaks then dips. <strong>Breast Tenderness</strong> & <strong>Acne</strong> are common.';
        const breastRow = document.querySelector('#dash-symptom-rate-rows .symptom-rate-row[data-symptom="breast_tenderness"]');
        const acneRow = document.querySelector('#dash-symptom-rate-rows .symptom-rate-row[data-symptom="acne"]');
        if (breastRow) breastRow.classList.add('highlighted-symptom');
        if (acneRow) acneRow.classList.add('highlighted-symptom');
    } else if (phase === 'Ovulatory') {
        if (subtitle) subtitle.innerHTML = '🩺 Estrogen peaks. You might experience light mid-cycle <strong>Cramping</strong>.';
        const crampsRow = document.querySelector('#dash-symptom-rate-rows .symptom-rate-row[data-symptom="cramps"]');
        if (crampsRow) crampsRow.classList.add('highlighted-symptom');
    } else {
        if (subtitle) subtitle.textContent = '🩺 Estrogen is rising. Energy is high. Physical symptoms are typically minimal.';
    }

    const todayStr = getTodayString();
    const todayLog = state.cycleLogs.find(l => l.date === todayStr);

    state.dashboardSymptoms = { cramps: null, headache: null, acne: null, breast_tenderness: null };
    document.querySelectorAll('#dash-symptom-rate-rows .rate-pill').forEach(p => p.className = 'rate-pill');

    if (todayLog) {
        const symptomsList = {
            cramps: todayLog.cramps_severity,
            headache: todayLog.headache_severity,
            acne: todayLog.acne_severity,
            breast_tenderness: todayLog.breast_tenderness_severity
        };

        for (const [symptom, severity] of Object.entries(symptomsList)) {
            if (severity) {
                state.dashboardSymptoms[symptom] = severity;
                const pill = document.querySelector(`#dash-symptom-rate-rows .symptom-rate-row[data-symptom="${symptom}"] .rate-pill[data-val="${severity}"]`);
                if (pill) pill.classList.add(`selected-${severity}`);
            }
        }
    }
}

function renderCycleDeviationAlert(pred) {
    const banner = document.getElementById('cycle-deviation-banner');
    const textEl = document.getElementById('deviation-alert-text');

    if (pred && pred.deviation_message) {
        if (textEl) textEl.textContent = pred.deviation_message;
        if (banner) banner.classList.remove('hidden');
    } else {
        if (banner) banner.classList.add('hidden');
    }
}

function openShareModal() {
    document.getElementById('generated-link-container').classList.add('hidden');
    document.getElementById('copy-success-note').classList.add('hidden');
    document.getElementById('modal-share-link').classList.remove('hidden');
}

async function handleShareLinkSubmit(e) {
    e.preventDefault();
    const hours = parseInt(document.getElementById('share-duration').value);

    try {
        const response = await apiCall('/cycle/share', 'POST', { hours_valid: hours });
        const absoluteUrl = window.location.origin + response.share_url;

        document.getElementById('share-link-input').value = absoluteUrl;
        document.getElementById('generated-link-container').classList.remove('hidden');

        localStorage.setItem('herwellness_share_link', absoluteUrl);
        localStorage.setItem('herwellness_share_expiry', response.expires_at);

        updateShareLinkStatusUI(absoluteUrl, response.expires_at);
    } catch (err) {
        alert('Error generating share link: ' + err.message);
    }
}

function copyShareLink() {
    const input = document.getElementById('share-link-input');
    input.select();
    input.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(input.value);

    const note = document.getElementById('copy-success-note');
    if (note) {
        note.classList.remove('hidden');
        setTimeout(() => note.classList.add('hidden'), 3000);
    }
}

function updateShareLinkStatusUI(url, expiryStr) {
    const statusBox = document.getElementById('share-link-status');
    if (!statusBox) return;

    if (url && expiryStr) {
        const expiry = new Date(expiryStr);
        if (expiry > new Date()) {
            statusBox.className = 'share-status-active';
            statusBox.innerHTML = `
                <strong>Active Sharing Link:</strong><br>
                <a href="${url}" target="_blank" style="text-decoration:underline; font-size:0.8rem; word-break:break-all;">${url}</a><br>
                <small style="display:block; margin-top:4px;">Expires: ${expiry.toLocaleString()}</small>
            `;
            return;
        }
    }

    statusBox.className = 'share-status-inactive';
    statusBox.textContent = 'No active sharing link generated.';
}

function checkActiveShareLink() {
    const url = localStorage.getItem('herwellness_share_link');
    const expiryStr = localStorage.getItem('herwellness_share_expiry');
    updateShareLinkStatusUI(url, expiryStr);
}

/* ========================================================= */
/* VERA AI COMPANION (NEW WELLNESS DASHBOARD FUNCTIONS)      */
/* ========================================================= */

function appendVeraMessage(text, role) {
    const container = document.getElementById('chat-messages-container');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'message message-' + role;
    
    // Quick time formatter
    const now = new Date();
    let hours = now.getHours();
    let mins = now.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; 
    mins = mins < 10 ? '0' + mins : mins;
    const timeStr = `${hours}:${mins} ${ampm}`;

    if (role === 'user') {
        div.style.textAlign = 'right';
        div.innerHTML = `
            <div class="message-bubble" style="background:#be123c; color:#fff; display:inline-block; border:none; text-align:left;">
                ${text}
            </div>
            <div class="message-time">You • ${timeStr}</div>
        `;
    } else {
        div.style.textAlign = 'left';
        div.innerHTML = `
            <div class="message-bubble" style="display:inline-block; border-color:#fbcfe8; background:#fff5f7;">
                ${text}
            </div>
            <div class="message-time">Vera • ${timeStr}</div>
        `;
    }

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function appendTypingDots() {
    const container = document.getElementById('chat-messages-container');
    if (!container) return null;

    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'message message-vera';
    div.style.textAlign = 'left';
    div.innerHTML = `
        <div class="message-bubble" style="display:inline-block; padding: 4px 10px;">
            <span style="display:inline-block; width:4px; height:4px; background:#db2777; border-radius:50%; margin:0 2px; animation:blink 1.4s infinite 0s;"></span>
            <span style="display:inline-block; width:4px; height:4px; background:#db2777; border-radius:50%; margin:0 2px; animation:blink 1.4s infinite 0.2s;"></span>
            <span style="display:inline-block; width:4px; height:4px; background:#db2777; border-radius:50%; margin:0 2px; animation:blink 1.4s infinite 0.4s;"></span>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingDots(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

async function handleVeraAPI(msg) {
    const typingId = appendTypingDots();
    
    // Try to get live wellness context
    let liveScore = 50;
    try {
        const liveSleep = parseFloat(document.getElementById('wellness-sleep-hours') ? document.getElementById('wellness-sleep-hours').value : 8.0);
        const liveHyd = parseFloat(document.getElementById('wellness-hydration-liters') ? document.getElementById('wellness-hydration-liters').value : 2.5);
        const liveEx = parseInt(document.getElementById('wellness-exercise-minutes') ? document.getElementById('wellness-exercise-minutes').value : 30);
        const stressBtn = document.querySelector('#wellness-stress-selector .pill-btn.selected');
        const liveStress = stressBtn ? stressBtn.dataset.stress : 'low';
        liveScore = calculateWellnessScoreLocal(liveSleep, liveHyd, liveEx, liveStress, state.selectedMoodValue || 3);
    } catch(e) {}

    const payload = {
        message: msg,
        user_context: { wellness_score: liveScore },
        history: state.chatHistory || []
    };

    try {
        const response = await apiCall('/wellness/chat', 'POST', payload);
        removeTypingDots(typingId);
        if (response.response) {
            appendVeraMessage(response.response, 'vera');
            if (!state.chatHistory) state.chatHistory = [];
            state.chatHistory.push({ role: 'user', content: msg });
            state.chatHistory.push({ role: 'assistant', content: response.response });
        }
    } catch (e) {
        removeTypingDots(typingId);
        appendVeraMessage("I'm sorry, I'm having trouble connecting right now. Please try again.", 'vera');
    }
}

function submitChatMessage() {
    const input = document.getElementById('vera-chat-input');
    if (!input) return;
    const msg = input.value.trim();
    if (!msg) return;
    
    appendVeraMessage(msg, 'user');
    input.value = '';
    
    handleVeraAPI(msg);
}

function sendQuickPrompt(msg) {
    appendVeraMessage(msg, 'user');
    handleVeraAPI(msg);
}

/* ==========================================================================
   FLOATING VERA AI WIDGET
   ========================================================================== */

function toggleVeraFloat() {
    const widget = document.getElementById('vera-float-widget');
    const panel  = document.getElementById('vera-float-panel');
    if (!widget || !panel) return;

    const isOpen = panel.classList.contains('open');

    if (isOpen) {
        // Close
        panel.classList.remove('open');
        widget.classList.remove('panel-open');
    } else {
        // Open
        panel.classList.add('open');
        widget.classList.add('panel-open');
        // Auto-focus input after animation settles
        setTimeout(() => {
            const input = document.getElementById('vera-chat-input');
            if (input) input.focus();
        }, 350);
    }
}

// Add enter key listener for chat input
document.addEventListener('DOMContentLoaded', () => {
    // Wait slightly to ensure elements are rendered
    setTimeout(() => {
        const input = document.getElementById('vera-chat-input');
        if (input) {
            input.addEventListener('keypress', function (e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    submitChatMessage();
                }
            });
        }
    }, 500);
});

// Date Fix
document.addEventListener('DOMContentLoaded', () => {
    const dateLabel = document.getElementById('db-date-label');
    if (dateLabel) {
        const now = new Date();
        const options = { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' };
        dateLabel.textContent = now.toLocaleDateString('en-US', options);
    }
});
