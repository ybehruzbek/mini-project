const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Supabase Configuration
const SUPABASE_URL = 'https://rvrehsjveyvlnpxnmjqh.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ2cmVoc2p2ZXl2bG5weG5tanFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1MjkwMzgsImV4cCI6MjA5NzEwNTAzOH0.oJne7OxGW_6I1H37YpcOLKQ-_PPRi029VRrBVPlndf8';
const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

// User State
let userId = tg.initDataUnsafe?.user?.id || 1277687464;
let currentDhikr = null;
let currentCount = 0;

// Helpers
const getLocalISODate = (d) => new Date(d.getTime() - (d.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
const todayStr = () => getLocalISODate(new Date());
const formatNumber = (n) => n?.toLocaleString('uz-UZ') || '0';

// Theme Logic
let currentThemeOverride = localStorage.getItem('appTheme') || 'auto';

function applyTheme() {
    if (currentThemeOverride === 'dark') {
        document.body.classList.add('dark-theme');
    } else if (currentThemeOverride === 'light') {
        document.body.classList.remove('dark-theme');
    } else {
        if (tg.colorScheme === 'dark') {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }
    updateThemeUI();
}

function updateThemeUI() {
    const btnAuto = document.getElementById('theme-auto');
    const btnLight = document.getElementById('theme-light');
    const btnDark = document.getElementById('theme-dark');
    if(!btnAuto) return;
    
    [btnAuto, btnLight, btnDark].forEach(btn => {
        btn.classList.remove('bg-white', 'dark:bg-gray-600', 'text-[var(--accent)]', 'shadow-sm');
        btn.classList.add('opacity-60');
    });
    
    let activeBtn = btnAuto;
    if (currentThemeOverride === 'light') activeBtn = btnLight;
    if (currentThemeOverride === 'dark') activeBtn = btnDark;
    
    activeBtn.classList.remove('opacity-60');
    activeBtn.classList.add('bg-white', 'dark:bg-gray-600', 'text-[var(--accent)]', 'shadow-sm');
}

tg.onEvent('themeChanged', applyTheme);

// Initialize Theme & Haptic Listeners when DOM is ready
setTimeout(() => {
    document.getElementById('theme-auto')?.addEventListener('click', () => { currentThemeOverride = 'auto'; localStorage.setItem('appTheme', 'auto'); applyTheme(); });
    document.getElementById('theme-light')?.addEventListener('click', () => { currentThemeOverride = 'light'; localStorage.setItem('appTheme', 'light'); applyTheme(); });
    document.getElementById('theme-dark')?.addEventListener('click', () => { currentThemeOverride = 'dark'; localStorage.setItem('appTheme', 'dark'); applyTheme(); });
    
    const hToggle = document.getElementById('haptic-toggle');
    if(hToggle) {
        hToggle.checked = hapticsEnabled;
        hToggle.addEventListener('change', (e) => {
            hapticsEnabled = e.target.checked;
            localStorage.setItem('hapticsEnabled', hapticsEnabled);
            if(hapticsEnabled) tg.HapticFeedback.impactOccurred('light');
        });
    }
    applyTheme();
}, 0);

// Haptics Logic
let hapticsEnabled = localStorage.getItem('hapticsEnabled') !== 'false';

// -----------------------------------------------------
// 1. TAB NAVIGATION
// -----------------------------------------------------
const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view-container');

navItems.forEach(item => {
    item.addEventListener('click', () => {
        navItems.forEach(n => n.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        
        item.classList.add('active');
        const targetId = item.getAttribute('data-target');
        const targetView = document.getElementById(targetId);
        targetView.classList.add('active');
        
        // Scroll to top when switching tabs
        targetView.scrollTop = 0;
        
        tg.HapticFeedback.selectionChanged();
        
        if (targetId === 'view-zikrlar') fetchDhikrs();
        if (targetId === 'view-stats') fetchStats();
        if (targetId === 'view-profile') {
            fetchReminders();
            fetchPrayerTimes();
            fetchDuas();
        }
    });
});

// -----------------------------------------------------
// 2. DATA FETCHING (SUPABASE)
// -----------------------------------------------------

async function initApp() {
    // Show Skeletons
    document.getElementById('dhikr-title').innerHTML = '<div class="skeleton h-8 w-64 mx-auto rounded-md"></div>';
    document.getElementById('target-count').innerHTML = '<div class="skeleton h-4 w-12 inline-block rounded-md"></div>';
    document.getElementById('counter').innerHTML = '<div class="skeleton h-16 w-16 mx-auto rounded-md mt-2"></div>';
    document.getElementById('profile-name').innerHTML = '<div class="skeleton h-6 w-32 rounded-md"></div>';
    document.getElementById('profile-habit').innerHTML = '<div class="skeleton h-4 w-20 rounded-md mt-1"></div>';

    const start = Date.now();
    
    // 1. Fetch User Profile
    const { data: user } = await supabaseClient.from('users').select('*').eq('user_id', userId).single();
    if (user) {
        document.getElementById('profile-name').textContent = user.full_name || 'Foydalanuvchi';
        
        const habitTexts = {
            beginner: '🌱 Yangi boshlayapman',
            medium: '🌿 Vaqt topganda',
            advanced: '🌳 Doimiy odat'
        };
        document.getElementById('profile-habit').textContent = habitTexts[user.habit_level] || user.habit_level || '';
        
        // Profile chips
        const cityChip = document.getElementById('profile-city-text');
        const prayerChip = document.getElementById('profile-prayer-status');
        if (cityChip) cityChip.textContent = user.city || 'Toshkent';
        if (prayerChip) {
            if (user.prayer_notifications) {
                prayerChip.textContent = 'Namoz ✓';
                document.getElementById('profile-prayer-chip').style.background = 'var(--accent-dim)';
                document.getElementById('profile-prayer-chip').style.color = 'var(--accent)';
            } else {
                prayerChip.textContent = 'Namoz ✗';
                document.getElementById('profile-prayer-chip').style.background = 'rgba(239,68,68,0.1)';
                document.getElementById('profile-prayer-chip').style.color = '#ef4444';
            }
        }
    }

    // 2. Fetch Dhikrs
    await fetchDhikrs();
    
    // 3. Fetch Reminders
    fetchReminders();
    
    const elapsed = Date.now() - start;
    if (elapsed < 400) await new Promise(r => setTimeout(r, 400 - elapsed));
    
    if (!currentDhikr) {
        document.getElementById('dhikr-title').textContent = "Zikr qo'shing";
        document.getElementById('target-count').textContent = "0";
        document.getElementById('counter').textContent = "0";
    }
}

async function fetchDhikrs() {
    const listEl = document.getElementById('dhikr-list');
    
    listEl.innerHTML = `
        <div class="glass-card p-4 flex items-center justify-between border-transparent">
            <div class="flex-1 pr-4">
                <div class="skeleton h-5 w-3/4 mb-3"></div>
                <div class="flex gap-4">
                    <div class="skeleton h-3 w-16"></div>
                    <div class="skeleton h-3 w-16"></div>
                </div>
            </div>
            <div class="skeleton h-6 w-6 rounded-full"></div>
        </div>
        <div class="glass-card p-4 flex items-center justify-between border-transparent">
            <div class="flex-1 pr-4">
                <div class="skeleton h-5 w-1/2 mb-3"></div>
                <div class="flex gap-4">
                    <div class="skeleton h-3 w-16"></div>
                    <div class="skeleton h-3 w-16"></div>
                </div>
            </div>
            <div class="skeleton h-6 w-6 rounded-full"></div>
        </div>
    `;

    const start = Date.now();
    const { data: dhikrs, error } = await supabaseClient.from('dhikrs').select('*').eq('user_id', userId).order('id');
    
    // Bugungi progress'ni ham olib kelamiz
    const today = todayStr();
    const { data: todayProgress } = await supabaseClient.from('daily_progress')
        .select('dhikr_id, count').eq('user_id', userId).eq('date', today);
    
    const progressMap = {};
    if (todayProgress) todayProgress.forEach(p => { progressMap[p.dhikr_id] = p.count || 0; });
    
    const elapsed = Date.now() - start;
    if (elapsed < 300) await new Promise(r => setTimeout(r, 300 - elapsed));
    
    if (error || !dhikrs || dhikrs.length === 0) {
        listEl.innerHTML = `
            <div class="flex flex-col items-center justify-center py-16 text-center">
                <div class="w-16 h-16 rounded-full flex items-center justify-center mb-4 opacity-20" style="background: var(--border);">
                    <i class="ph ph-book-open text-3xl"></i>
                </div>
                <p class="text-sm opacity-40 font-medium">Hali zikr qo'shilmagan</p>
                <p class="text-xs opacity-30 mt-1">Bot orqali zikr qo'shing</p>
            </div>`;
        document.getElementById('dhikr-count-badge').textContent = '0 ta';
        return;
    }

    // Badge
    document.getElementById('dhikr-count-badge').textContent = `${dhikrs.length} ta`;

    if (!currentDhikr && dhikrs.length > 0) {
        await selectDhikr(dhikrs[0]);
    }

    listEl.innerHTML = '';
    dhikrs.forEach(d => {
        const isSelected = currentDhikr && currentDhikr.id === d.id;
        const dailyDone = progressMap[d.id] || 0;
        const dailyPercent = d.daily_target > 0 ? Math.min(100, Math.round((dailyDone / d.daily_target) * 100)) : 0;
        const isDailyComplete = dailyDone >= d.daily_target && d.daily_target > 0;
        
        const el = document.createElement('div');
        el.className = `glass-card glass-card-interactive p-4 cursor-pointer ${isSelected ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-900/20' : ''}`;
        el.onclick = async () => {
            await selectDhikr(d);
            navItems[0].click();
        };
        
        el.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <h3 class="font-bold text-base">${d.title}</h3>
                ${isSelected 
                    ? '<i class="ph-fill ph-check-circle text-xl text-emerald-500"></i>' 
                    : '<i class="ph ph-circle text-xl opacity-15"></i>'}
            </div>
            <div class="flex gap-4 text-xs font-medium opacity-50 mb-2.5">
                <span class="flex items-center gap-1"><i class="ph ph-target text-xs"></i> ${formatNumber(d.daily_target)}/kun</span>
                <span class="flex items-center gap-1"><i class="ph ph-chart-bar text-xs"></i> ${formatNumber(d.global_count || 0)} jami</span>
                ${isDailyComplete ? '<span class="text-emerald-500 font-bold">✓ Bajarildi</span>' : `<span>${formatNumber(dailyDone)} bugun</span>`}
            </div>
            <div class="dhikr-progress">
                <div class="dhikr-progress-fill ${isDailyComplete ? '!bg-amber-400' : ''}" style="width: ${dailyPercent}%"></div>
            </div>
        `;
        listEl.appendChild(el);
    });
}

async function fetchStats() {
    document.getElementById('stat-daily').innerHTML = '<div class="skeleton h-6 w-12 mx-auto rounded-md mt-1"></div>';
    document.getElementById('stat-global').innerHTML = '<div class="skeleton h-6 w-16 mx-auto rounded-md mt-1"></div>';
    document.getElementById('stat-streak').innerHTML = '<div class="skeleton h-6 w-16 mx-auto rounded-md mt-1"></div>';
    document.getElementById('stat-top').innerHTML = '<div class="skeleton h-5 w-24 mx-auto rounded-md mt-1"></div>';

    const start = Date.now();
    const { data: dhikrs } = await supabaseClient.from('dhikrs').select('title, global_count').eq('user_id', userId);
    
    const today = todayStr();
    const { data: todayProgress } = await supabaseClient.from('daily_progress')
        .select('count').eq('user_id', userId).eq('date', today);
    
    const elapsed = Date.now() - start;
    if (elapsed < 300) await new Promise(r => setTimeout(r, 300 - elapsed));
    
    let totalDaily = 0;
    let totalGlobal = 0;
    let topDhikr = { title: "Yo'q", count: -1 };
    
    if (todayProgress) {
        todayProgress.forEach(p => { totalDaily += (p.count || 0); });
    }
    
    if (dhikrs) {
        dhikrs.forEach(d => {
            totalGlobal += (d.global_count || 0);
            if ((d.global_count || 0) > topDhikr.count) {
                topDhikr = { title: d.title, count: d.global_count || 0 };
            }
        });
    }
    
    // Animate numbers
    animateNumber('stat-daily', totalDaily);
    animateNumber('stat-global', totalGlobal);
    document.getElementById('stat-top').textContent = topDhikr.count > 0 ? topDhikr.title : "Hali yo'q";
    
    // Fetch progress for streak and chart
    const { data: progress } = await supabaseClient.from('daily_progress')
        .select('date, count')
        .eq('user_id', userId)
        .order('date', { ascending: false })
        .limit(100);
        
    const dailyTotals = {};
    if (progress) {
        progress.forEach(p => {
            dailyTotals[p.date] = (dailyTotals[p.date] || 0) + p.count;
        });
    }
    
    // Calculate Streak
    let streak = 0;
    let checkDate = new Date();
    let checkStr = getLocalISODate(checkDate);
    
    if (!dailyTotals[checkStr] || dailyTotals[checkStr] === 0) {
        checkDate.setDate(checkDate.getDate() - 1);
        checkStr = getLocalISODate(checkDate);
    }
    
    while (dailyTotals[checkStr] > 0) {
        streak++;
        checkDate.setDate(checkDate.getDate() - 1);
        checkStr = getLocalISODate(checkDate);
    }
    
    document.getElementById('stat-streak').textContent = `${streak} kun`;
    
    // Render 7-day Bar Chart
    const chartContainer = document.getElementById('chart-container');
    const chartLabels = document.getElementById('chart-labels');
    chartContainer.innerHTML = '';
    chartLabels.innerHTML = '';
    
    const dayNames = ['Yak', 'Du', 'Se', 'Cho', 'Pay', 'Ju', 'Sha'];
    const last7 = [];
    
    for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const dateStr = getLocalISODate(d);
        last7.push({
            date: dateStr,
            dayName: dayNames[d.getDay()],
            count: dailyTotals[dateStr] || 0,
            isToday: i === 0
        });
    }
    
    const maxCount = Math.max(...last7.map(d => d.count), 1);
    
    last7.forEach((day, idx) => {
        const percent = (day.count / maxCount) * 100;
        const minHeight = day.count > 0 ? 12 : 4;
        const height = Math.max(minHeight, percent);
        
        const bar = document.createElement('div');
        bar.className = 'flex-1 rounded-t-lg chart-bar relative group cursor-pointer';
        bar.style.height = '0%';
        bar.style.background = day.isToday 
            ? 'var(--accent)' 
            : day.count > 0 
                ? 'var(--accent-dim)' 
                : 'var(--border)';
        bar.style.opacity = day.isToday ? '1' : day.count > 0 ? '0.7' : '0.3';
        
        // Count label on top
        if (day.count > 0) {
            const label = document.createElement('span');
            label.className = 'absolute -top-5 left-1/2 -translate-x-1/2 text-[9px] font-bold opacity-0 tabular-nums transition-opacity';
            label.textContent = formatNumber(day.count);
            bar.appendChild(label);
            bar.addEventListener('touchstart', () => { label.style.opacity = '1'; });
            bar.addEventListener('touchend', () => { setTimeout(() => { label.style.opacity = '0'; }, 1500); });
        }
        
        chartContainer.appendChild(bar);
        
        // Animate bars with delay
        setTimeout(() => {
            bar.style.height = `${height}%`;
        }, 100 + idx * 80);
        
        const labelEl = document.createElement('span');
        labelEl.className = `flex-1 text-center ${day.isToday ? 'text-[var(--accent)] font-extrabold' : ''}`;
        labelEl.textContent = day.isToday ? 'Bugun' : day.dayName;
        chartLabels.appendChild(labelEl);
    });
}

function animateNumber(elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const duration = 600;
    const start = performance.now();
    const startVal = 0;
    
    function update(now) {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // easeOutCubic
        const current = Math.round(startVal + (target - startVal) * eased);
        el.textContent = formatNumber(current);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// -----------------------------------------------------
// 3. TASBEH COUNTER
// -----------------------------------------------------

const counterEl = document.getElementById('counter');
const tapArea = document.getElementById('tap-area');
const progressRing = document.getElementById('progress-ring');
const circumference = 2 * Math.PI * 44;

progressRing.style.strokeDasharray = `${circumference} ${circumference}`;
progressRing.style.strokeDashoffset = circumference;

let goalReachedNotified = false;

async function selectDhikr(d) {
    currentDhikr = d;
    goalReachedNotified = false;
    
    const today = todayStr();
    
    try {
        const { data: prog } = await supabaseClient.from('daily_progress')
            .select('count')
            .eq('user_id', userId)
            .eq('dhikr_id', d.id)
            .eq('date', today)
            .single();
        
        currentCount = prog ? (prog.count || 0) : 0;
    } catch {
        currentCount = 0;
    }
    
    currentDhikr._todayCount = currentCount;
    
    document.getElementById('dhikr-title').textContent = d.title;
    document.getElementById('target-count').textContent = formatNumber(d.daily_target);
    
    // Global progress bar
    const globalBar = document.getElementById('global-progress-bar');
    const globalFill = document.getElementById('global-progress-fill');
    const globalText = document.getElementById('global-progress-text');
    
    if (d.global_target && d.global_target > 0) {
        globalBar.classList.remove('hidden');
        const globalPercent = Math.min(100, ((d.global_count || 0) / d.global_target) * 100);
        globalFill.style.width = `${globalPercent}%`;
        globalText.textContent = `${formatNumber(d.global_count || 0)} / ${formatNumber(d.global_target)}`;
    } else {
        globalBar.classList.add('hidden');
    }
    
    if (currentCount >= d.daily_target && d.daily_target > 0) {
        goalReachedNotified = true;
    }
    
    updateCounterUI();
}

function updateCounterUI() {
    counterEl.textContent = formatNumber(currentCount);
    
    if (!currentDhikr) return;
    
    let percent = currentCount / currentDhikr.daily_target;
    if (percent > 1) percent = 1;
    
    const offset = circumference - (percent * circumference);
    progressRing.style.strokeDashoffset = offset;
    
    const label = document.getElementById('counter-label');

    if (currentCount >= currentDhikr.daily_target && currentDhikr.daily_target > 0) {
        progressRing.style.stroke = "#f59e0b";
        label.classList.remove('hidden');
        
        if (!goalReachedNotified) {
            goalReachedNotified = true;
            tg.HapticFeedback.notificationOccurred('success');
            
            // Pulse effect
            tapArea.classList.add('goal-reached');
            setTimeout(() => tapArea.classList.remove('goal-reached'), 1000);
            
            // Confetti burst
            const burst = document.createElement('div');
            burst.className = 'confetti-burst';
            tapArea.appendChild(burst);
            setTimeout(() => burst.remove(), 700);
        }
    } else {
        progressRing.style.stroke = "var(--accent)";
        label.classList.add('hidden');
    }
}

// Tap counter
tapArea.addEventListener('click', () => {
    currentCount++;
    updateCounterUI();
    if (hapticsEnabled) tg.HapticFeedback.impactOccurred('light');
});

// Reset
document.getElementById('reset-btn').addEventListener('click', () => {
    if (currentCount === 0) return;
    tg.showConfirm("Hisoblagichni qayta boshlaysizmi?", (confirmed) => {
        if (confirmed) {
            currentCount = currentDhikr?._todayCount || 0;
            goalReachedNotified = currentCount >= (currentDhikr?.daily_target || 0);
            updateCounterUI();
            if (hapticsEnabled) tg.HapticFeedback.impactOccurred('rigid');
        }
    });
});

// -----------------------------------------------------
// 4. SAVE DATA TO SUPABASE
// -----------------------------------------------------

document.getElementById('save-btn').addEventListener('click', async () => {
    if (!currentDhikr) return;
    
    tg.HapticFeedback.impactOccurred('medium');
    const btn = document.getElementById('save-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = `<i class="ph ph-spinner-gap animate-spin text-xl"></i> Saqlanmoqda...`;
    
    try {
        const today = todayStr();
        
        const { data: existingProg } = await supabaseClient.from('daily_progress')
            .select('id, count').eq('user_id', userId).eq('dhikr_id', currentDhikr.id).eq('date', today).single();
        
        const previouslySaved = existingProg ? (existingProg.count || 0) : 0;
        const savedBefore = currentDhikr._todayCount || 0;
        const newTaps = currentCount - savedBefore;
        
        if (newTaps <= 0) {
            tg.HapticFeedback.notificationOccurred('warning');
            btn.innerHTML = `<i class="ph ph-info text-xl"></i> O'zgarish yo'q`;
            setTimeout(() => { btn.innerHTML = originalText; }, 2000);
            return;
        }
        
        const newDailyTotal = previouslySaved + newTaps;
        
        if (existingProg) {
            await supabaseClient.from('daily_progress').update({ count: newDailyTotal }).eq('id', existingProg.id);
        } else {
            await supabaseClient.from('daily_progress').insert({
                user_id: userId, dhikr_id: currentDhikr.id, date: today, count: newDailyTotal
            });
        }
        
        const { data: freshDhikr } = await supabaseClient.from('dhikrs')
            .select('global_count').eq('id', currentDhikr.id).single();
        const currentGlobal = freshDhikr ? (freshDhikr.global_count || 0) : 0;
        const newGlobal = currentGlobal + newTaps;
        
        await supabaseClient.from('dhikrs').update({
            global_count: newGlobal
        }).eq('id', currentDhikr.id);
        
        currentDhikr.global_count = newGlobal;
        currentDhikr._todayCount = newDailyTotal;
        currentCount = newDailyTotal;
        updateCounterUI();
        
        // Update global progress bar
        if (currentDhikr.global_target > 0) {
            const globalPercent = Math.min(100, (newGlobal / currentDhikr.global_target) * 100);
            document.getElementById('global-progress-fill').style.width = `${globalPercent}%`;
            document.getElementById('global-progress-text').textContent = `${formatNumber(newGlobal)} / ${formatNumber(currentDhikr.global_target)}`;
        }
        
        tg.HapticFeedback.notificationOccurred('success');
        btn.innerHTML = `<i class="ph ph-check text-xl"></i> +${formatNumber(newTaps)} saqlandi!`;
        
        tg.sendData(JSON.stringify({
            action: 'save_dhikr',
            title: currentDhikr.title,
            count: newDailyTotal,
            target: currentDhikr.daily_target
        }));
        
    } catch (err) {
        console.error(err);
        tg.HapticFeedback.notificationOccurred('error');
        btn.innerHTML = `<i class="ph ph-warning text-xl"></i> Xatolik`;
    }
    
    setTimeout(() => { btn.innerHTML = originalText; }, 2500);
});

// Profile Hard Reset
document.getElementById('hard-reset-btn').addEventListener('click', async () => {
    tg.showConfirm("Rostdan ham barcha statistika va zikrlarni o'chirasizmi? Bu amalni ortga qaytarib bo'lmaydi.", async (confirmed) => {
        if (confirmed) {
            await supabaseClient.from('dhikrs').delete().eq('user_id', userId);
            await supabaseClient.from('daily_progress').delete().eq('user_id', userId);
            await supabaseClient.from('duas').delete().eq('user_id', userId);
            tg.close();
        }
    });
});

// -----------------------------------------------------
// 5. REMINDERS LOGIC
// -----------------------------------------------------

async function fetchReminders() {
    const listEl = document.getElementById('reminders-list');
    const loadingEl = document.getElementById('reminders-loading');
    if(!listEl) return;
    
    loadingEl.classList.remove('hidden');
    
    try {
        const { data: reminders, error } = await supabaseClient.from('user_reminders')
            .select('*')
            .eq('user_id', userId)
            .order('time', { ascending: true });
            
        if (error) throw error;
        
        listEl.innerHTML = '';
        
        if (reminders && reminders.length > 0) {
            reminders.forEach(r => {
                const typeIcon = r.type === 'dua' ? 'ph-hands-praying' : r.type === 'prayer_reminder' ? 'ph-mosque' : 'ph-clock';
                const typeColor = r.type === 'dua' ? 'text-amber-500 bg-amber-50 dark:bg-amber-900/20' : r.type === 'prayer_reminder' ? 'text-indigo-500 bg-indigo-50 dark:bg-indigo-900/20' : 'text-indigo-500 bg-indigo-50 dark:bg-indigo-900/20';
                
                listEl.innerHTML += `
                    <div class="p-4 flex items-center justify-between border-b border-[var(--border)]">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 rounded-full ${typeColor} flex items-center justify-center">
                                <i class="ph ${typeIcon} text-lg"></i>
                            </div>
                            <div>
                                <span class="font-bold text-lg tabular-nums">${r.time}</span>
                                ${r.label ? `<span class="text-[10px] opacity-50 block">${r.label}</span>` : ''}
                            </div>
                        </div>
                        <div class="flex items-center gap-2">
                            <label class="relative inline-flex items-center cursor-pointer">
                                <input type="checkbox" class="sr-only peer" ${r.is_active ? 'checked' : ''} onchange="toggleReminder(${r.id}, this.checked)">
                                <div class="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
                            </label>
                            <button onclick="deleteReminder(${r.id})" class="text-red-400 p-1.5 rounded-lg active:bg-red-50 dark:active:bg-red-900/20 transition-colors">
                                <i class="ph ph-trash text-sm"></i>
                            </button>
                        </div>
                    </div>
                `;
            });
        } else {
            listEl.innerHTML = `<div class="p-6 text-center text-sm opacity-40">Hali hech qanday eslatma qo'shilmagan</div>`;
        }
    } catch (e) {
        console.error(e);
        listEl.innerHTML = `<div class="p-4 text-center text-sm text-red-500">Xatolik yuz berdi</div>`;
    } finally {
        loadingEl.classList.add('hidden');
    }
}

async function addReminder(timeStr) {
    tg.HapticFeedback.impactOccurred('light');
    document.getElementById('reminders-loading').classList.remove('hidden');
    try {
        await supabaseClient.from('user_reminders').insert({
            user_id: userId,
            time: timeStr,
            is_active: true
        });
        fetchReminders();
    } catch(e) {
        console.error(e);
        document.getElementById('reminders-loading').classList.add('hidden');
    }
}

window.toggleReminder = async function(id, isActive) {
    tg.HapticFeedback.impactOccurred('light');
    try {
        await supabaseClient.from('user_reminders').update({ is_active: isActive }).eq('id', id);
    } catch(e) {
        console.error(e);
        fetchReminders();
    }
};

window.deleteReminder = async function(id) {
    tg.showConfirm("Ushbu eslatmani o'chirib tashlaysizmi?", async (confirmed) => {
        if (confirmed) {
            tg.HapticFeedback.impactOccurred('medium');
            document.getElementById('reminders-loading').classList.remove('hidden');
            await supabaseClient.from('user_reminders').delete().eq('id', id);
            fetchReminders();
        }
    });
};

const timeInput = document.getElementById('reminder-time-input');
if (timeInput) {
    timeInput.addEventListener('change', (e) => {
        if (e.target.value) {
            addReminder(e.target.value);
            e.target.value = '';
        }
    });
}

// -----------------------------------------------------
// 6. PRAYER TIMES LOGIC
// -----------------------------------------------------

const PRAYER_NAMES = {
    fajr: { name: 'Bomdod', emoji: '🌅' },
    dhuhr: { name: 'Peshin', emoji: '☀️' },
    asr: { name: 'Asr', emoji: '🌤' },
    maghrib: { name: 'Shom', emoji: '🌆' },
    isha: { name: 'Xufton', emoji: '🌙' },
};

async function fetchPrayerTimes() {
    const loadingEl = document.getElementById('prayer-loading');
    const listEl = document.getElementById('prayer-times-list');
    const cityEl = document.getElementById('prayer-city');
    if (!listEl) return;
    
    loadingEl?.classList.remove('hidden');
    
    try {
        const { data: user } = await supabaseClient.from('users').select('city, prayer_notifications').eq('user_id', userId).single();
        const city = user?.city || 'Toshkent';
        const prayerOn = user?.prayer_notifications ?? true;
        
        const prayerToggle = document.getElementById('prayer-toggle');
        if (prayerToggle) prayerToggle.checked = prayerOn;
        
        cityEl.textContent = `📍 ${city}`;
        
        const today = todayStr();
        const { data: cached } = await supabaseClient.from('prayer_cache')
            .select('*').eq('city', city).eq('date', today).single();
        
        let times;
        if (cached) {
            times = {
                fajr: cached.fajr, dhuhr: cached.dhuhr, asr: cached.asr,
                maghrib: cached.maghrib, isha: cached.isha,
            };
        } else {
            const CITIES = {
                "Toshkent": [41.2995, 69.2401], "Samarqand": [39.6542, 66.9597],
                "Buxoro": [39.7681, 64.4556], "Andijon": [40.7821, 72.3442],
                "Namangan": [40.9983, 71.6726], "Farg'ona": [40.3834, 71.7870],
                "Nukus": [42.4628, 59.6003], "Qarshi": [38.8610, 65.8004],
                "Jizzax": [40.1158, 67.8422], "Urganch": [41.5533, 60.6236],
                "Navoiy": [40.1034, 65.3792], "Termiz": [37.2241, 67.2783],
                "Chirchiq": [41.4689, 69.5828], "Kokand": [40.5286, 70.9425],
            };
            const coords = CITIES[city] || CITIES["Toshkent"];
            const d = new Date();
            const dateStr = `${String(d.getDate()).padStart(2,'0')}-${String(d.getMonth()+1).padStart(2,'0')}-${d.getFullYear()}`;
            
            const resp = await fetch(`https://api.aladhan.com/v1/timings/${dateStr}?latitude=${coords[0]}&longitude=${coords[1]}&method=3`);
            const data = await resp.json();
            const t = data.data.timings;
            
            times = {
                fajr: t.Fajr.slice(0, 5), dhuhr: t.Dhuhr.slice(0, 5), asr: t.Asr.slice(0, 5),
                maghrib: t.Maghrib.slice(0, 5), isha: t.Isha.slice(0, 5),
            };
        }
        
        // Render prayer times
        listEl.innerHTML = '';
        const now = new Date();
        const currentMinutes = now.getHours() * 60 + now.getMinutes();
        let nextPrayerFound = false;
        
        for (const [key, info] of Object.entries(PRAYER_NAMES)) {
            const time = times[key] || '--:--';
            const [h, m] = time.split(':').map(Number);
            const prayerMinutes = h * 60 + m;
            const isPast = prayerMinutes <= currentMinutes;
            const isNext = !isPast && !nextPrayerFound;
            
            if (isNext) nextPrayerFound = true;
            
            // Calculate time remaining for next prayer
            let remaining = '';
            if (isNext) {
                const diff = prayerMinutes - currentMinutes;
                const hrs = Math.floor(diff / 60);
                const mins = diff % 60;
                remaining = hrs > 0 ? `${hrs} soat ${mins} min` : `${mins} min`;
            }
            
            const div = document.createElement('div');
            div.className = `p-4 flex items-center justify-between border-b border-[var(--border)] transition-colors ${isNext ? 'next-prayer' : isPast ? 'opacity-40' : ''}`;
            div.innerHTML = `
                <div class="flex items-center gap-3">
                    <span class="text-xl">${info.emoji}</span>
                    <div>
                        <span class="font-medium text-sm">${info.name}</span>
                        ${isNext ? `<span class="text-[10px] block font-semibold" style="color: var(--accent);">${remaining} qoldi</span>` : ''}
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="font-bold text-sm tabular-nums">${time}</span>
                    ${isPast ? '<i class="ph-fill ph-check-circle text-emerald-500 text-sm"></i>' : ''}
                    ${isNext ? '<i class="ph-fill ph-arrow-right text-xs" style="color: var(--accent);"></i>' : ''}
                </div>
            `;
            listEl.appendChild(div);
        }
        
    } catch (e) {
        console.error('Prayer times error:', e);
        listEl.innerHTML = `<div class="p-4 text-center text-sm opacity-40">Namoz vaqtlarini yuklashda xatolik</div>`;
    } finally {
        loadingEl?.classList.add('hidden');
    }
}

// Prayer notification toggle
const prayerToggle = document.getElementById('prayer-toggle');
if (prayerToggle) {
    prayerToggle.addEventListener('change', async (e) => {
        tg.HapticFeedback.impactOccurred('light');
        
        // Update chip
        const chip = document.getElementById('profile-prayer-status');
        if (e.target.checked) {
            chip.textContent = 'Namoz ✓';
            document.getElementById('profile-prayer-chip').style.background = 'var(--accent-dim)';
            document.getElementById('profile-prayer-chip').style.color = 'var(--accent)';
        } else {
            chip.textContent = 'Namoz ✗';
            document.getElementById('profile-prayer-chip').style.background = 'rgba(239,68,68,0.1)';
            document.getElementById('profile-prayer-chip').style.color = '#ef4444';
        }
        
        try {
            await supabaseClient.from('users').update({ 
                prayer_notifications: e.target.checked 
            }).eq('user_id', userId);
        } catch(err) {
            console.error(err);
            e.target.checked = !e.target.checked;
        }
    });
}

document.getElementById('refresh-prayer-btn')?.addEventListener('click', () => {
    tg.HapticFeedback.impactOccurred('light');
    fetchPrayerTimes();
});

// -----------------------------------------------------
// 7. DAILY DUA LOGIC
// -----------------------------------------------------

let allDuas = [];
let currentDuaIndex = 0;

async function fetchDuas() {
    const loadingEl = document.getElementById('dua-loading');
    const contentEl = document.getElementById('dua-content');
    if (!contentEl) return;
    
    try {
        const { data: duas } = await supabaseClient.from('duas')
            .select('*')
            .eq('user_id', userId)
            .eq('is_active', true)
            .order('id');
        
        if (duas && duas.length > 0) {
            allDuas = duas;
            currentDuaIndex = Math.floor(Math.random() * duas.length);
            showDua(currentDuaIndex);
        } else {
            loadingEl?.classList.add('hidden');
            contentEl.classList.remove('hidden');
            document.getElementById('dua-arabic').classList.add('hidden');
            document.getElementById('dua-text').textContent = "Hali duo qo'shilmagan. Bot orqali duo qo'shing.";
            document.getElementById('dua-meaning').textContent = '';
        }
    } catch (e) {
        console.error('Duas fetch error:', e);
        loadingEl?.classList.add('hidden');
        contentEl.classList.remove('hidden');
        document.getElementById('dua-text').textContent = "Duolarni yuklashda xatolik.";
    }
}

function showDua(index) {
    const loadingEl = document.getElementById('dua-loading');
    const contentEl = document.getElementById('dua-content');
    if (!allDuas.length || !contentEl) return;
    
    const dua = allDuas[index % allDuas.length];
    
    loadingEl?.classList.add('hidden');
    contentEl.classList.remove('hidden');
    
    const arabicEl = document.getElementById('dua-arabic');
    const textEl = document.getElementById('dua-text');
    const meaningEl = document.getElementById('dua-meaning');
    
    if (dua.arabic && dua.arabic.length > 0) {
        arabicEl.textContent = dua.arabic;
        arabicEl.classList.remove('hidden');
    } else {
        arabicEl.classList.add('hidden');
    }
    
    textEl.textContent = dua.text || '';
    meaningEl.textContent = '';
    
    // Category badge
    const catNames = {
        morning: '🌅 Tonggi', evening: '🌙 Kechki', pre_prayer: '🕌 Namoz',
        bedtime: '🛏 Uxlashdan oldin', general: '📿 Umumiy', custom: '✍️ Shaxsiy'
    };
    if (dua.category && catNames[dua.category]) {
        meaningEl.textContent = catNames[dua.category];
    }
    
    // Slide animation
    contentEl.style.opacity = '0';
    contentEl.style.transform = 'translateY(6px)';
    requestAnimationFrame(() => {
        contentEl.style.transition = 'all 0.3s ease';
        contentEl.style.opacity = '1';
        contentEl.style.transform = 'translateY(0)';
    });
}

document.getElementById('next-dua-btn')?.addEventListener('click', () => {
    if (allDuas.length > 1) {
        tg.HapticFeedback.impactOccurred('light');
        currentDuaIndex = (currentDuaIndex + 1) % allDuas.length;
        showDua(currentDuaIndex);
    }
});

// Start
initApp();
