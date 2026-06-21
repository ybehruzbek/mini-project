const tg = window.Telegram.WebApp;
tg.expand(); tg.ready();

const SUPABASE_URL = 'https://rvrehsjveyvlnpxnmjqh.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ2cmVoc2p2ZXl2bG5weG5tanFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1MjkwMzgsImV4cCI6MjA5NzEwNTAzOH0.oJne7OxGW_6I1H37YpcOLKQ-_PPRi029VRrBVPlndf8';
const db = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

let userId = tg.initDataUnsafe?.user?.id || 1277687464;
let currentDhikr = null;
let currentCount = 0;
let hapticsOn = localStorage.getItem('haptics') !== 'false';
let themeMode = localStorage.getItem('theme') || 'auto';

// Helpers
const isoDate = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().split('T')[0];
const today = () => isoDate(new Date());
const fmt = (n) => (n || 0).toLocaleString('uz-UZ');
const $ = (id) => document.getElementById(id);
const haptic = (t) => { if (hapticsOn) tg.HapticFeedback.impactOccurred(t); };

// ===== THEME =====
function applyTheme() {
    const dark = themeMode === 'dark' || (themeMode === 'auto' && tg.colorScheme === 'dark');
    document.body.classList.toggle('dark-theme', dark);
    [$('t-auto'), $('t-light'), $('t-dark')].forEach(b => { b.classList.remove('active'); });
    $(`t-${themeMode}`).classList.add('active');
}
tg.onEvent('themeChanged', applyTheme);
['auto', 'light', 'dark'].forEach(m => {
    $(`t-${m}`)?.addEventListener('click', () => { themeMode = m; localStorage.setItem('theme', m); applyTheme(); });
});
applyTheme();

$('haptic-toggle').checked = hapticsOn;
$('haptic-toggle').addEventListener('change', e => {
    hapticsOn = e.target.checked;
    localStorage.setItem('haptics', hapticsOn);
    if (hapticsOn) haptic('light');
});

// ===== NAV =====
const navBtns = document.querySelectorAll('.nav-btn');
const views = document.querySelectorAll('.view');
navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        navBtns.forEach(b => b.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        btn.classList.add('active');
        const v = $(btn.dataset.view);
        v.classList.add('active');
        v.scrollTop = 0;
        tg.HapticFeedback.selectionChanged();
        if (btn.dataset.view === 'v-zikrlar') fetchDhikrs();
        if (btn.dataset.view === 'v-stats') fetchStats();
        if (btn.dataset.view === 'v-profile') { fetchReminders(); fetchPrayerTimes(); fetchDuas(); }
    });
});

// ===== INIT =====
async function initApp() {
    $('dhikr-title').innerHTML = '<div class="skel h-7 w-48 mx-auto"></div>';
    $('counter').innerHTML = '<div class="skel h-14 w-14 mx-auto mt-1"></div>';
    $('profile-name').innerHTML = '<div class="skel h-5 w-28"></div>';
    $('profile-habit').innerHTML = '<div class="skel h-3 w-16 mt-1"></div>';

    const { data: user } = await db.from('users').select('*').eq('user_id', userId).maybeSingle();
    if (user) {
        $('profile-name').textContent = user.full_name || 'Foydalanuvchi';
        const habits = { beginner: '🌱 Yangi boshlayapman', medium: '🌿 Vaqt topganda', advanced: '🌳 Doimiy odat' };
        $('profile-habit').textContent = habits[user.habit_level] || '';
        $('chip-city-text').textContent = user.city || 'Toshkent';
        $('city-select').value = user.city || 'Toshkent';
        if (user.prayer_notifications) {
            $('chip-prayer-text').textContent = 'Namoz ✓';
        } else {
            $('chip-prayer-text').textContent = 'Namoz ✗';
            $('chip-prayer').style.background = 'rgba(239,68,68,0.1)';
            $('chip-prayer').style.color = '#ef4444';
        }
    }
    await fetchDhikrs();
    fetchReminders();
    if (!currentDhikr) {
        $('dhikr-title').textContent = "Zikr qo'shing";
        $('target-count').textContent = "0";
        $('counter').textContent = "0";
    }
}

// ===== DHIKRS =====
let allDhikrs = [];
let allProgress = {};
let currentFilter = 'all';

// Filter buttons
document.querySelectorAll('[data-filter]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentFilter = btn.dataset.filter;
        renderDhikrList();
    });
});

async function fetchDhikrs() {
    const list = $('dhikr-list');
    list.innerHTML = '<div class="card p-4 h-20 skel"></div><div class="card p-4 h-20 skel"></div>';

    const [{ data: dhikrs }, { data: prog }] = await Promise.all([
        db.from('dhikrs').select('*').eq('user_id', userId).order('id'),
        db.from('daily_progress').select('dhikr_id, count').eq('user_id', userId).eq('date', today())
    ]);

    allDhikrs = dhikrs || [];
    allProgress = {};
    if (prog) prog.forEach(p => { allProgress[p.dhikr_id] = p.count || 0; });

    $('dhikr-badge').textContent = `${allDhikrs.length} ta`;

    if (!currentDhikr && allDhikrs.length > 0) await selectDhikr(allDhikrs[0]);

    // Daily summary ring
    if (allDhikrs.length > 0) {
        let totalDone = 0, totalTarget = 0;
        allDhikrs.forEach(d => {
            totalDone += allProgress[d.id] || 0;
            totalTarget += d.daily_target || 0;
        });
        const pct = totalTarget > 0 ? Math.min(100, Math.round(totalDone / totalTarget * 100)) : 0;
        $('daily-summary').classList.remove('hidden');
        $('daily-pct').textContent = `${pct}%`;
        $('daily-done-text').textContent = fmt(totalDone);
        $('daily-total-text').textContent = fmt(totalTarget);
        const circ = 2 * Math.PI * 20;
        $('daily-ring').style.strokeDashoffset = circ - (pct / 100 * circ);
    }

    renderDhikrList();
}

function renderDhikrList() {
    const list = $('dhikr-list');
    let filtered = allDhikrs;
    if (currentFilter === 'done') filtered = allDhikrs.filter(d => (allProgress[d.id] || 0) >= d.daily_target && d.daily_target > 0);
    if (currentFilter === 'pending') filtered = allDhikrs.filter(d => (allProgress[d.id] || 0) < d.daily_target || d.daily_target === 0);

    if (filtered.length === 0) {
        list.innerHTML = `<div class="flex flex-col items-center py-12 text-center">
            <div class="w-14 h-14 rounded-full flex items-center justify-center mb-3 opacity-15" style="background:var(--border)"><i class="ph ph-book-open text-2xl"></i></div>
            <p class="text-sm opacity-30 font-medium">${currentFilter === 'all' ? "Hali zikr qo'shilmagan" : 'Topilmadi'}</p></div>`;
        return;
    }

    list.innerHTML = '';
    filtered.forEach(d => {
        const isSel = currentDhikr?.id === d.id;
        const done = allProgress[d.id] || 0;
        const pct = d.daily_target > 0 ? Math.min(100, Math.round(done / d.daily_target * 100)) : 0;
        const isDone = done >= d.daily_target && d.daily_target > 0;

        const el = document.createElement('div');
        el.className = `card card-press p-3 cursor-pointer flex items-center gap-3 ${isSel ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/15' : ''} ${isDone ? 'glow-gold' : ''}`;
        el.onclick = async () => { await selectDhikr(d); navBtns[0].click(); };

        // Mini SVG ring
        const ringCirc = 2 * Math.PI * 16;
        const ringOffset = ringCirc - (pct / 100 * ringCirc);
        const ringColor = isDone ? 'var(--warning)' : 'var(--accent)';

        el.innerHTML = `
            <div class="relative w-11 h-11 flex-shrink-0">
                <svg class="w-11 h-11" viewBox="0 0 40 40">
                    <circle cx="20" cy="20" r="16" fill="none" stroke="var(--border)" stroke-width="3" opacity="0.25"/>
                    <circle class="ring-circle" cx="20" cy="20" r="16" fill="none" stroke="${ringColor}" stroke-width="3.5" stroke-linecap="round" stroke-dasharray="${ringCirc}" stroke-dashoffset="${ringOffset}"/>
                </svg>
                <span class="absolute inset-0 flex items-center justify-center text-[9px] font-extrabold tabular" style="color:${ringColor}">${pct}%</span>
            </div>
            <div class="flex-1 min-w-0">
                <div class="flex items-center justify-between mb-0.5">
                    <h3 class="font-bold text-sm truncate">${d.title}</h3>
                    ${isSel ? '<i class="ph-fill ph-check-circle text-emerald-500 text-base flex-shrink-0"></i>' : ''}
                </div>
                <div class="flex gap-3 text-[10px] font-medium opacity-40 mb-1.5">
                    <span>${fmt(done)}/${fmt(d.daily_target)} bugun</span>
                    <span>${fmt(d.global_count || 0)} jami</span>
                    ${isDone ? '<span class="text-amber-500 font-bold">✓ Bajarildi</span>' : ''}
                </div>
                <div class="progress-track"><div class="progress-fill" style="width:${pct}%;${isDone ? 'background:#fbbf24' : ''}"></div></div>
            </div>
            <i class="ph ph-caret-right opacity-15 flex-shrink-0"></i>`;
        list.appendChild(el);
    });
}

// ===== TASBEH =====
const circumference = 2 * Math.PI * 44;
$('progress-ring').style.strokeDasharray = `${circumference} ${circumference}`;
$('progress-ring').style.strokeDashoffset = circumference;
let goalNotified = false;
let sessionStart = null;
let sessionInterval = null;
let tapTimestamps = [];

async function selectDhikr(d) {
    currentDhikr = d;
    goalNotified = false;
    try {
        const { data: prog } = await db.from('daily_progress').select('count').eq('user_id', userId).eq('dhikr_id', d.id).eq('date', today()).maybeSingle();
        currentCount = prog ? (prog.count || 0) : 0;
    } catch { currentCount = 0; }
    currentDhikr._todayCount = currentCount;
    $('dhikr-title').textContent = d.title;
    $('target-count').textContent = fmt(d.daily_target);
    $('dhikr-title-badge').textContent = d.title.length > 20 ? d.title.slice(0, 18) + '…' : d.title;

    if (d.global_target > 0) {
        $('global-bar').classList.remove('hidden');
        const gp = Math.min(100, ((d.global_count || 0) / d.global_target) * 100);
        $('global-fill').style.width = `${gp}%`;
        $('global-text').textContent = `${fmt(d.global_count || 0)} / ${fmt(d.global_target)}`;
    } else { $('global-bar').classList.add('hidden'); }

    if (currentCount >= d.daily_target && d.daily_target > 0) goalNotified = true;
    // Reset session
    sessionStart = null;
    tapTimestamps = [];
    $('session-timer').classList.add('hidden');
    $('rpm-label').classList.add('hidden');
    if (sessionInterval) { clearInterval(sessionInterval); sessionInterval = null; }
    updateUI();
}

function updateUI() {
    $('counter').textContent = fmt(currentCount);
    if (!currentDhikr) return;
    let pct = Math.min(1, currentCount / currentDhikr.daily_target);
    $('progress-ring').style.strokeDashoffset = circumference - pct * circumference;

    if (currentCount >= currentDhikr.daily_target && currentDhikr.daily_target > 0) {
        $('progress-ring').style.stroke = '#f59e0b';
        $('counter-label').classList.remove('hidden');
        if (!goalNotified) {
            goalNotified = true;
            tg.HapticFeedback.notificationOccurred('success');
            $('tap-area').classList.add('goal-pulse');
            setTimeout(() => $('tap-area').classList.remove('goal-pulse'), 1000);
            const b = document.createElement('div'); b.className = 'burst-ring';
            $('tap-area').appendChild(b); setTimeout(() => b.remove(), 700);
        }
    } else {
        $('progress-ring').style.stroke = 'var(--accent)';
        $('counter-label').classList.add('hidden');
    }
}

$('tap-area').addEventListener('click', () => {
    currentCount++;
    updateUI();
    haptic('light');
    // Session timer
    if (!sessionStart) {
        sessionStart = Date.now();
        $('session-timer').classList.remove('hidden');
        sessionInterval = setInterval(() => {
            const s = Math.floor((Date.now() - sessionStart) / 1000);
            $('session-time').textContent = `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
        }, 1000);
    }
    // RPM
    const now = Date.now();
    tapTimestamps.push(now);
    tapTimestamps = tapTimestamps.filter(t => now - t < 60000);
    if (tapTimestamps.length > 2) {
        $('rpm-label').classList.remove('hidden');
        $('rpm-label').textContent = `${tapTimestamps.length} z/m`;
    }
});

$('reset-btn').addEventListener('click', () => {
    if (currentCount === 0) return;
    tg.showConfirm("Hisoblagichni qayta boshlaysizmi?", (ok) => {
        if (ok) {
            currentCount = currentDhikr?._todayCount || 0;
            goalNotified = currentCount >= (currentDhikr?.daily_target || 0);
            updateUI();
            haptic('rigid');
            sessionStart = null; tapTimestamps = [];
            $('session-timer').classList.add('hidden');
            $('rpm-label').classList.add('hidden');
            if (sessionInterval) { clearInterval(sessionInterval); sessionInterval = null; }
        }
    });
});

// Quick switch
$('quick-switch-btn').addEventListener('click', () => {
    $('sheet-overlay').classList.add('open');
    $('sheet-panel').classList.add('open');
    haptic('light');
    const sl = $('sheet-list');
    sl.innerHTML = '';
    allDhikrs.forEach(d => {
        const isSel = currentDhikr?.id === d.id;
        const done = allProgress[d.id] || 0;
        const pct = d.daily_target > 0 ? Math.min(100, Math.round(done / d.daily_target * 100)) : 0;
        const btn = document.createElement('button');
        btn.className = `card card-press p-3 flex items-center gap-3 w-full text-left ${isSel ? 'border-emerald-500' : ''}`;
        btn.innerHTML = `<span class="text-sm font-bold tabular flex-shrink-0" style="color:var(--accent)">${pct}%</span>
            <span class="font-semibold text-sm flex-1 truncate">${d.title}</span>
            ${isSel ? '<i class="ph-fill ph-check-circle text-emerald-500"></i>' : '<i class="ph ph-caret-right opacity-15"></i>'}`;
        btn.onclick = async () => {
            closeSheet();
            await selectDhikr(d);
            haptic('medium');
        };
        sl.appendChild(btn);
    });
});
function closeSheet() { $('sheet-overlay').classList.remove('open'); $('sheet-panel').classList.remove('open'); }
$('sheet-overlay').addEventListener('click', closeSheet);

// ===== SAVE =====
$('save-btn').addEventListener('click', async () => {
    if (!currentDhikr) return;
    haptic('medium');
    const btn = $('save-btn');
    const orig = btn.innerHTML;
    btn.innerHTML = '<i class="ph ph-spinner-gap animate-spin text-xl"></i> Saqlanmoqda...';

    try {
        const t = today();
        const { data: ep } = await db.from('daily_progress').select('id, count').eq('user_id', userId).eq('dhikr_id', currentDhikr.id).eq('date', t).maybeSingle();
        const prev = ep ? (ep.count || 0) : 0;
        const saved = currentDhikr._todayCount || 0;
        const newTaps = currentCount - saved;

        if (newTaps <= 0) {
            tg.HapticFeedback.notificationOccurred('warning');
            btn.innerHTML = '<i class="ph ph-info text-xl"></i> O\'zgarish yo\'q';
            setTimeout(() => { btn.innerHTML = orig; }, 2000); return;
        }

        const newDaily = prev + newTaps;
        if (ep) await db.from('daily_progress').update({ count: newDaily }).eq('id', ep.id);
        else await db.from('daily_progress').insert({ user_id: userId, dhikr_id: currentDhikr.id, date: t, count: newDaily });

        const { data: fd } = await db.from('dhikrs').select('global_count').eq('id', currentDhikr.id).single();
        const newGlobal = (fd?.global_count || 0) + newTaps;
        await db.from('dhikrs').update({ global_count: newGlobal }).eq('id', currentDhikr.id);

        currentDhikr.global_count = newGlobal;
        currentDhikr._todayCount = newDaily;
        currentCount = newDaily;
        updateUI();

        if (currentDhikr.global_target > 0) {
            $('global-fill').style.width = `${Math.min(100, newGlobal / currentDhikr.global_target * 100)}%`;
            $('global-text').textContent = `${fmt(newGlobal)} / ${fmt(currentDhikr.global_target)}`;
        }

        tg.HapticFeedback.notificationOccurred('success');
        btn.innerHTML = `<i class="ph ph-check text-xl"></i> +${fmt(newTaps)} saqlandi!`;
        tg.sendData(JSON.stringify({ action: 'save_dhikr', title: currentDhikr.title, count: newDaily, target: currentDhikr.daily_target }));
    } catch (err) {
        console.error(err);
        tg.HapticFeedback.notificationOccurred('error');
        btn.innerHTML = '<i class="ph ph-warning text-xl"></i> Xatolik';
    }
    setTimeout(() => { btn.innerHTML = orig; }, 2500);
});

$('hard-reset').addEventListener('click', async () => {
    tg.showConfirm("Barcha ma'lumotlarni o'chirasizmi? Ortga qaytarib bo'lmaydi!", async (ok) => {
        if (ok) {
            await db.from('dhikrs').delete().eq('user_id', userId);
            await db.from('daily_progress').delete().eq('user_id', userId);
            tg.close();
        }
    });
});

// ===== STATS =====
let chartRange = 7;
let allDailyTotals = {};

document.querySelectorAll('[data-range]').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('[data-range]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        chartRange = parseInt(btn.dataset.range);
        renderChart();
    });
});

async function fetchStats() {
    $('stat-daily').innerHTML = '<div class="skel h-5 w-10 mx-auto mt-0.5"></div>';
    $('stat-global').innerHTML = '<div class="skel h-5 w-14 mx-auto mt-0.5"></div>';

    const [{ data: dhikrs }, { data: tp }, { data: progress }] = await Promise.all([
        db.from('dhikrs').select('id, title, global_count, daily_target').eq('user_id', userId),
        db.from('daily_progress').select('count').eq('user_id', userId).eq('date', today()),
        db.from('daily_progress').select('date, count, dhikr_id').eq('user_id', userId).order('date', { ascending: false }).limit(500)
    ]);

    let totalDaily = 0, totalGlobal = 0, topD = { title: "Yo'q", c: -1 };
    if (tp) tp.forEach(p => { totalDaily += p.count || 0; });
    if (dhikrs) dhikrs.forEach(d => {
        totalGlobal += d.global_count || 0;
        if ((d.global_count || 0) > topD.c) topD = { title: d.title, c: d.global_count || 0 };
    });

    animNum('stat-daily', totalDaily);
    animNum('stat-global', totalGlobal);
    $('stat-top').textContent = topD.c > 0 ? topD.title : "Hali yo'q";

    // Build daily totals map
    allDailyTotals = {};
    const perDhikrToday = {};
    if (progress) progress.forEach(p => {
        allDailyTotals[p.date] = (allDailyTotals[p.date] || 0) + p.count;
        if (p.date === today()) {
            const did = p.dhikr_id;
            perDhikrToday[did] = (perDhikrToday[did] || 0) + p.count;
        }
    });

    // Streak
    let streak = 0, cd = new Date(), cs = isoDate(cd);
    if (!allDailyTotals[cs]) { cd.setDate(cd.getDate() - 1); cs = isoDate(cd); }
    while (allDailyTotals[cs] > 0) { streak++; cd.setDate(cd.getDate() - 1); cs = isoDate(cd); }
    $('stat-streak').textContent = `${streak} kun`;

    // Best day
    let bestDay = 0;
    Object.values(allDailyTotals).forEach(v => { if (v > bestDay) bestDay = v; });
    $('stat-best-day').textContent = fmt(bestDay);

    // Motivation
    if (streak > 0) {
        $('motivation-banner').classList.remove('hidden');
        const msgs = [
            `🔥 ${streak} kunlik seriya! Davom eting!`,
            `💪 ${streak} kun ketma-ket! Ajoyib!`,
            `🌟 ${streak} kundan beri to'xtamagansiz!`
        ];
        $('motivation-text').textContent = msgs[streak % msgs.length];
    } else { $('motivation-banner').classList.add('hidden'); }

    renderChart();

    // Per-dhikr breakdown
    const pd = $('per-dhikr');
    if (dhikrs && dhikrs.length > 0) {
        const colors = ['#10b981', '#6366f1', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6', '#f97316'];
        pd.innerHTML = '';
        dhikrs.forEach((d, i) => {
            const done = perDhikrToday[d.id] || 0;
            const pct = d.daily_target > 0 ? Math.min(100, Math.round(done / d.daily_target * 100)) : 0;
            const color = colors[i % colors.length];
            const row = document.createElement('div');
            row.className = 'p-3 border-b border-[var(--border)] last:border-0';
            row.innerHTML = `
                <div class="flex items-center justify-between mb-1.5">
                    <span class="text-xs font-semibold truncate flex-1">${d.title}</span>
                    <span class="text-[10px] font-bold tabular opacity-50">${fmt(d.global_count || 0)} jami</span>
                </div>
                <div class="progress-track"><div class="progress-fill" style="width:${pct}%;background:${color}"></div></div>`;
            pd.appendChild(row);
        });
    }

    // Heat map (7 weeks)
    renderHeatMap();
}

function renderChart() {
    const bars = $('chart-bars');
    const labels = $('chart-labels');
    bars.innerHTML = ''; labels.innerHTML = '';
    const dayNames = ['Yak', 'Du', 'Se', 'Cho', 'Pay', 'Ju', 'Sha'];
    const data = [];
    for (let i = chartRange - 1; i >= 0; i--) {
        const d = new Date(); d.setDate(d.getDate() - i);
        const ds = isoDate(d);
        data.push({ date: ds, day: dayNames[d.getDay()], count: allDailyTotals[ds] || 0, isToday: i === 0 });
    }
    const max = Math.max(...data.map(d => d.count), 1);

    data.forEach((day, idx) => {
        const h = day.count > 0 ? Math.max(12, (day.count / max) * 100) : 4;
        const bar = document.createElement('div');
        bar.className = 'flex-1 rounded-t-md chart-bar relative';
        bar.style.height = '0%';
        bar.style.background = day.isToday ? 'var(--accent)' : day.count > 0 ? 'var(--accent-dim)' : 'var(--border)';
        bar.style.opacity = day.isToday ? '1' : day.count > 0 ? '0.6' : '0.25';

        if (day.count > 0) {
            const lbl = document.createElement('span');
            lbl.className = 'absolute -top-4 left-1/2 -translate-x-1/2 text-[8px] font-bold tabular';
            lbl.style.color = 'var(--muted)';
            lbl.textContent = fmt(day.count);
            bar.appendChild(lbl);
        }
        bars.appendChild(bar);
        setTimeout(() => { bar.style.height = `${h}%`; }, 50 + idx * 50);

        const le = document.createElement('span');
        le.className = `flex-1 text-center ${day.isToday ? 'font-extrabold' : ''}`;
        le.style.color = day.isToday ? 'var(--accent)' : '';
        le.textContent = day.isToday ? 'Bugun' : day.day;
        labels.appendChild(le);
    });
}

function renderHeatMap() {
    const hm = $('heat-map');
    hm.innerHTML = '';
    const cells = [];
    for (let i = 48; i >= 0; i--) {
        const d = new Date(); d.setDate(d.getDate() - i);
        const ds = isoDate(d);
        cells.push({ date: ds, count: allDailyTotals[ds] || 0 });
    }
    const max = Math.max(...cells.map(c => c.count), 1);
    cells.forEach(c => {
        const el = document.createElement('div');
        el.className = 'heat-cell';
        if (c.count === 0) {
            el.style.background = 'var(--border)';
            el.style.opacity = '0.3';
        } else {
            const intensity = Math.min(1, c.count / max);
            const alpha = 0.15 + intensity * 0.85;
            el.style.background = `rgba(16, 185, 129, ${alpha})`;
        }
        el.title = `${c.date}: ${c.count}`;
        el.addEventListener('click', () => {
            tg.showAlert(`📅 ${c.date}\n📿 ${fmt(c.count)} marta zikr`);
        });
        hm.appendChild(el);
    });
}

function animNum(id, target) {
    const el = $(id);
    if (!el) return;
    const dur = 500, start = performance.now();
    function u(now) {
        const p = Math.min((now - start) / dur, 1);
        const e = 1 - Math.pow(1 - p, 3);
        el.textContent = fmt(Math.round(target * e));
        if (p < 1) requestAnimationFrame(u);
    }
    requestAnimationFrame(u);
}

// ===== REMINDERS =====
async function fetchReminders() {
    const list = $('rem-list');
    $('rem-loading').classList.remove('hidden');
    try {
        const { data: rems } = await db.from('user_reminders').select('*').eq('user_id', userId).order('time', { ascending: true });
        list.innerHTML = '';
        if (rems?.length > 0) {
            rems.forEach(r => {
                list.innerHTML += `<div class="p-3.5 flex items-center justify-between border-b border-[var(--border)]">
                    <div class="flex items-center gap-2.5">
                        <div class="w-8 h-8 rounded-full flex items-center justify-center" style="background:var(--secondary-dim);color:var(--secondary)"><i class="ph ph-clock text-lg"></i></div>
                        <span class="font-bold text-base tabular">${r.time}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <label class="toggle"><input type="checkbox" ${r.is_active ? 'checked' : ''} onchange="toggleRem(${r.id},this.checked)"><div class="toggle-track"></div><div class="toggle-thumb"></div></label>
                        <button onclick="deleteRem(${r.id})" class="text-red-400 p-1 rounded-lg active:bg-red-50 dark:active:bg-red-900/20"><i class="ph ph-trash text-sm"></i></button>
                    </div></div>`;
            });
        } else {
            list.innerHTML = '<div class="p-5 text-center text-xs opacity-30">Hali eslatma qo\'shilmagan</div>';
        }
    } catch (e) { console.error(e); list.innerHTML = '<div class="p-4 text-center text-xs text-red-500">Xatolik</div>'; }
    finally { $('rem-loading').classList.add('hidden'); }
}

window.toggleRem = async (id, on) => { haptic('light'); await db.from('user_reminders').update({ is_active: on }).eq('id', id); };
window.deleteRem = (id) => {
    tg.showConfirm("Eslatmani o'chirasizmi?", async (ok) => {
        if (ok) { haptic('medium'); await db.from('user_reminders').delete().eq('id', id); fetchReminders(); }
    });
};
$('rem-time')?.addEventListener('change', async (e) => {
    if (e.target.value) {
        haptic('light');
        $('rem-loading').classList.remove('hidden');
        await db.from('user_reminders').insert({ user_id: userId, time: e.target.value, is_active: true });
        e.target.value = '';
        fetchReminders();
    }
});

// ===== PRAYER TIMES =====
const PRAYER_NAMES = { fajr: { n: 'Bomdod', e: '🌅' }, dhuhr: { n: 'Peshin', e: '☀️' }, asr: { n: 'Asr', e: '🌤' }, maghrib: { n: 'Shom', e: '🌆' }, isha: { n: 'Xufton', e: '🌙' } };
let prayerCountdownInterval = null;

async function fetchPrayerTimes() {
    $('prayer-loading')?.classList.remove('hidden');
    const list = $('prayer-list');
    try {
        const { data: user } = await db.from('users').select('city, prayer_notifications').eq('user_id', userId).single();
        const city = user?.city || 'Toshkent';
        $('prayer-toggle').checked = user?.prayer_notifications ?? true;
        $('prayer-city').textContent = `📍 ${city}`;

        const t = today();
        const { data: cached } = await db.from('prayer_cache').select('*').eq('city', city).eq('date', t).maybeSingle();
        let times;
        if (cached) {
            times = { fajr: cached.fajr, dhuhr: cached.dhuhr, asr: cached.asr, maghrib: cached.maghrib, isha: cached.isha };
        } else {
            const CITIES = { "Toshkent":[41.2995,69.2401],"Samarqand":[39.6542,66.9597],"Buxoro":[39.7681,64.4556],"Andijon":[40.7821,72.3442],"Namangan":[40.9983,71.6726],"Farg'ona":[40.3834,71.787],"Nukus":[42.4628,59.6003],"Qarshi":[38.861,65.8004],"Jizzax":[40.1158,67.8422],"Urganch":[41.5533,60.6236],"Navoiy":[40.1034,65.3792],"Termiz":[37.2241,67.2783],"Chirchiq":[41.4689,69.5828],"Kokand":[40.5286,70.9425] };
            const c = CITIES[city] || CITIES["Toshkent"];
            const d = new Date();
            const ds = `${String(d.getDate()).padStart(2,'0')}-${String(d.getMonth()+1).padStart(2,'0')}-${d.getFullYear()}`;
            const r = await fetch(`https://api.aladhan.com/v1/timings/${ds}?latitude=${c[0]}&longitude=${c[1]}&method=3`);
            const data = await r.json();
            const tm = data.data.timings;
            times = { fajr: tm.Fajr.slice(0,5), dhuhr: tm.Dhuhr.slice(0,5), asr: tm.Asr.slice(0,5), maghrib: tm.Maghrib.slice(0,5), isha: tm.Isha.slice(0,5) };
        }

        list.innerHTML = '';
        const now = new Date();
        const curMin = now.getHours() * 60 + now.getMinutes();
        let nextFound = false, nextPrayerMin = null, nextPrayerName = '';

        for (const [key, info] of Object.entries(PRAYER_NAMES)) {
            const time = times[key] || '--:--';
            const [h, m] = time.split(':').map(Number);
            const pm = h * 60 + m;
            const past = pm <= curMin;
            const isNext = !past && !nextFound;
            if (isNext) { nextFound = true; nextPrayerMin = pm; nextPrayerName = info.n; }

            const div = document.createElement('div');
            div.className = `p-3 flex items-center justify-between border-b border-[var(--border)] ${isNext ? 'next-prayer' : past ? 'opacity-35' : ''}`;
            let remaining = '';
            if (isNext) { const diff = pm - curMin; remaining = diff >= 60 ? `${Math.floor(diff/60)}s ${diff%60}m` : `${diff} min`; }
            div.innerHTML = `<div class="flex items-center gap-2.5"><span class="text-lg">${info.e}</span><div><span class="font-medium text-sm">${info.n}</span>${isNext ? `<span class="text-[9px] block font-bold" style="color:var(--accent)">${remaining} qoldi</span>` : ''}</div></div>
                <div class="flex items-center gap-1.5"><span class="font-bold text-sm tabular">${time}</span>${past ? '<i class="ph-fill ph-check-circle text-emerald-500 text-xs"></i>' : ''}${isNext ? '<i class="ph-fill ph-arrow-right text-xs" style="color:var(--accent)"></i>' : ''}</div>`;
            list.appendChild(div);
        }

        // Countdown
        if (nextPrayerMin !== null) {
            $('prayer-countdown-bar').classList.remove('hidden');
            if (prayerCountdownInterval) clearInterval(prayerCountdownInterval);
            function updateCountdown() {
                const n = new Date();
                const cm = n.getHours() * 60 + n.getMinutes();
                const cs = n.getSeconds();
                const diffSec = (nextPrayerMin - cm) * 60 - cs;
                if (diffSec <= 0) { $('prayer-countdown').textContent = `${nextPrayerName} vaqti!`; clearInterval(prayerCountdownInterval); return; }
                const mm = Math.floor(diffSec / 60);
                const ss = diffSec % 60;
                $('prayer-countdown').textContent = `${nextPrayerName} — ${mm}:${String(ss).padStart(2, '0')}`;
            }
            updateCountdown();
            prayerCountdownInterval = setInterval(updateCountdown, 1000);
        } else { $('prayer-countdown-bar').classList.add('hidden'); }

    } catch (e) { console.error(e); list.innerHTML = '<div class="p-4 text-center text-xs opacity-30">Xatolik</div>'; }
    finally { $('prayer-loading')?.classList.add('hidden'); }
}

$('prayer-toggle')?.addEventListener('change', async (e) => {
    haptic('light');
    const on = e.target.checked;
    $('chip-prayer-text').textContent = on ? 'Namoz ✓' : 'Namoz ✗';
    $('chip-prayer').style.background = on ? 'var(--accent-dim)' : 'rgba(239,68,68,0.1)';
    $('chip-prayer').style.color = on ? 'var(--accent)' : '#ef4444';
    await db.from('users').update({ prayer_notifications: on }).eq('user_id', userId);
});

$('refresh-prayer')?.addEventListener('click', () => { haptic('light'); fetchPrayerTimes(); });

// City select
$('city-select')?.addEventListener('change', async (e) => {
    haptic('medium');
    const city = e.target.value;
    $('chip-city-text').textContent = city;
    await db.from('users').update({ city }).eq('user_id', userId);
    fetchPrayerTimes();
});

// ===== DUAS =====
let allDuas = [];
let duaIdx = 0;

async function fetchDuas() {
    try {
        const { data } = await db.from('duas').select('*').eq('user_id', userId).eq('is_active', true).order('id');
        if (data?.length > 0) {
            allDuas = data;
            duaIdx = Math.floor(Math.random() * data.length);
            showDua(duaIdx);
        } else {
            $('dua-loading')?.classList.add('hidden');
            $('dua-content').classList.remove('hidden');
            $('dua-arabic').classList.add('hidden');
            $('dua-text').textContent = "Duo qo'shilmagan. Bot orqali qo'shing.";
            $('dua-cat-badge').textContent = '';
            $('dua-counter').textContent = '';
        }
    } catch (e) { console.error(e); }
}

function showDua(idx) {
    if (!allDuas.length) return;
    const dua = allDuas[idx % allDuas.length];
    $('dua-loading')?.classList.add('hidden');
    $('dua-content').classList.remove('hidden');

    if (dua.arabic?.trim()) { $('dua-arabic').textContent = dua.arabic; $('dua-arabic').classList.remove('hidden'); }
    else { $('dua-arabic').classList.add('hidden'); }

    $('dua-text').textContent = dua.text || '';
    $('dua-counter').textContent = `${(idx % allDuas.length) + 1}/${allDuas.length}`;

    const cats = { morning: '🌅 Tonggi', evening: '🌙 Kechki', pre_prayer: '🕌 Namoz', bedtime: '🛏 Uxlash', general: '📿 Umumiy', custom: '✍️ Shaxsiy' };
    $('dua-cat-badge').textContent = cats[dua.category] || '📿 Duo';

    $('dua-content').style.opacity = '0';
    $('dua-content').style.transform = 'translateY(4px)';
    requestAnimationFrame(() => {
        $('dua-content').style.transition = 'all 0.25s ease';
        $('dua-content').style.opacity = '1';
        $('dua-content').style.transform = 'translateY(0)';
    });
}

$('next-dua')?.addEventListener('click', () => { if (allDuas.length > 1) { haptic('light'); duaIdx = (duaIdx + 1) % allDuas.length; showDua(duaIdx); } });
$('prev-dua')?.addEventListener('click', () => { if (allDuas.length > 1) { haptic('light'); duaIdx = (duaIdx - 1 + allDuas.length) % allDuas.length; showDua(duaIdx); } });

// START
initApp();
