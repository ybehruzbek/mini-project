const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

// Supabase Configuration
const SUPABASE_URL = 'https://rvrehsjveyvlnpxnmjqh.supabase.co';
const SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ2cmVoc2p2ZXl2bG5weG5tanFoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODE1MjkwMzgsImV4cCI6MjA5NzEwNTAzOH0.oJne7OxGW_6I1H37YpcOLKQ-_PPRi029VRrBVPlndf8';
const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

// User State
let userId = tg.initDataUnsafe?.user?.id || 1277687464; // Fallback for dev testing
let currentDhikr = null;
let currentCount = 0;

// Theme Logic
function applyTheme() {
    if (tg.colorScheme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
}
tg.onEvent('themeChanged', applyTheme);
applyTheme();

// -----------------------------------------------------
// 1. TAB NAVIGATION
// -----------------------------------------------------
const navItems = document.querySelectorAll('.nav-item');
const views = document.querySelectorAll('.view-container');

navItems.forEach(item => {
    item.addEventListener('click', () => {
        // Remove active class from all
        navItems.forEach(n => n.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        
        // Add active to clicked
        item.classList.add('active');
        const targetId = item.getAttribute('data-target');
        document.getElementById(targetId).classList.add('active');
        
        // Trigger haptic
        tg.HapticFeedback.selectionChanged();
        
        // Refresh specific view data
        if (targetId === 'view-zikrlar') fetchDhikrs();
        if (targetId === 'view-stats') fetchStats();
    });
});

// -----------------------------------------------------
// 2. DATA FETCHING (SUPABASE)
// -----------------------------------------------------

async function initApp() {
    // Show Skeletons for tasbeh
    document.getElementById('dhikr-title').innerHTML = '<div class="skeleton h-8 w-64 mx-auto rounded-md"></div>';
    document.getElementById('target-count').innerHTML = '<div class="skeleton h-4 w-12 inline-block rounded-md"></div>';
    document.getElementById('counter').innerHTML = '<div class="skeleton h-16 w-16 mx-auto rounded-md mt-2"></div>';

    // Show Skeletons for profile
    document.getElementById('profile-name').innerHTML = '<div class="skeleton h-6 w-32 mx-auto rounded-md"></div>';
    document.getElementById('profile-habit').innerHTML = '<div class="skeleton h-4 w-20 mx-auto rounded-md mt-1"></div>';

    const start = Date.now();
    
    // 1. Fetch User Profile
    const { data: user } = await supabaseClient.from('users').select('*').eq('user_id', userId).single();
    if (user) {
        document.getElementById('profile-name').textContent = user.full_name || 'Foydalanuvchi';
        document.getElementById('profile-habit').textContent = (user.habit_level || 'Odat') + ' darajasi';
    }

    // 2. Fetch Dhikrs
    await fetchDhikrs();
    
    // Ensure smooth premium loading feel
    const elapsed = Date.now() - start;
    if (elapsed < 400) await new Promise(r => setTimeout(r, 400 - elapsed));
    
    // If dhikr was loaded, counter was updated. If not, set to 0.
    if (!currentDhikr) {
        document.getElementById('dhikr-title').textContent = "Zikr qo'shing";
        document.getElementById('target-count').textContent = "0";
        document.getElementById('counter').textContent = "0";
    }
}

async function fetchDhikrs() {
    const listEl = document.getElementById('dhikr-list');
    
    // Show Skeletons
    listEl.innerHTML = `
        <div class="glass-card p-4 flex items-center justify-between mb-3 border-transparent">
            <div class="flex-1 pr-4">
                <div class="skeleton h-5 w-3/4 mb-3"></div>
                <div class="flex gap-4">
                    <div class="skeleton h-3 w-16"></div>
                    <div class="skeleton h-3 w-16"></div>
                </div>
            </div>
            <div class="skeleton h-6 w-6 rounded-full"></div>
        </div>
        <div class="glass-card p-4 flex items-center justify-between mb-3 border-transparent">
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
    
    const elapsed = Date.now() - start;
    if (elapsed < 300) await new Promise(r => setTimeout(r, 300 - elapsed));
    
    if (error || !dhikrs || dhikrs.length === 0) {
        listEl.innerHTML = `<p class="text-center opacity-50 py-4">Zikrlar topilmadi. Bot orqali zikr qo'shing.</p>`;
        return;
    }

    // Set first dhikr as active if none selected
    if (!currentDhikr && dhikrs.length > 0) {
        selectDhikr(dhikrs[0]);
    }

    // Render list
    listEl.innerHTML = '';
    dhikrs.forEach(d => {
        const isSelected = currentDhikr && currentDhikr.id === d.id;
        const el = document.createElement('div');
        el.className = `glass-card p-4 flex items-center justify-between active:scale-[0.98] transition-transform ${isSelected ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' : ''}`;
        el.onclick = () => {
            selectDhikr(d);
            // Auto switch to main tab
            navItems[0].click();
        };
        
        el.innerHTML = `
            <div class="flex-1 pr-4">
                <h3 class="font-bold text-lg mb-1">${d.title}</h3>
                <div class="flex gap-4 text-xs font-medium opacity-60">
                    <span><i class="ph ph-target"></i> ${d.daily_target}</span>
                    <span><i class="ph ph-chart-bar"></i> ${d.global_count || 0}</span>
                </div>
            </div>
            ${isSelected ? '<i class="ph ph-check-circle text-2xl text-emerald-500"></i>' : '<i class="ph ph-circle text-2xl opacity-20"></i>'}
        `;
        listEl.appendChild(el);
    });
}

async function fetchStats() {
    // Show Skeletons for stats
    document.getElementById('stat-daily').innerHTML = '<div class="skeleton h-10 w-24 mx-auto rounded-md"></div>';
    document.getElementById('stat-global').innerHTML = '<div class="skeleton h-10 w-24 mx-auto rounded-md"></div>';
    document.getElementById('stat-streak').innerHTML = '<div class="skeleton h-6 w-16 mx-auto rounded-md mt-1"></div>';
    document.getElementById('stat-top').innerHTML = '<div class="skeleton h-5 w-24 mx-auto rounded-md mt-1"></div>';
    
    // Chart skeletons are already in HTML, we'll replace them below

    const start = Date.now();
    const { data: dhikrs } = await supabaseClient.from('dhikrs').select('title, daily_count, global_count').eq('user_id', userId);
    
    const elapsed = Date.now() - start;
    if (elapsed < 300) await new Promise(r => setTimeout(r, 300 - elapsed));
    
    let totalDaily = 0;
    let totalGlobal = 0;
    let topDhikr = { title: "Yo'q", count: -1 };
    
    if (dhikrs) {
        dhikrs.forEach(d => {
            totalDaily += (d.daily_count || 0);
            totalGlobal += (d.global_count || 0);
            if ((d.global_count || 0) > topDhikr.count) {
                topDhikr = { title: d.title, count: d.global_count || 0 };
            }
        });
    }
    
    document.getElementById('stat-daily').textContent = totalDaily;
    document.getElementById('stat-global').textContent = totalGlobal;
    document.getElementById('stat-top').textContent = topDhikr.count > 0 ? topDhikr.title : "Hali yo'q";
    
    // Fetch progress for streak and chart
    const { data: progress } = await supabaseClient.from('daily_progress')
        .select('date, count')
        .eq('user_id', userId)
        .order('date', { ascending: false })
        .limit(100);
        
    // Group by date
    const dailyTotals = {};
    if (progress) {
        progress.forEach(p => {
            dailyTotals[p.date] = (dailyTotals[p.date] || 0) + p.count;
        });
    }
    
    // Calculate Streak
    let streak = 0;
    const today = new Date();
    const getLocalISODate = (d) => new Date(d.getTime() - (d.getTimezoneOffset() * 60000)).toISOString().split('T')[0];
    
    let checkDate = new Date(today);
    let checkStr = getLocalISODate(checkDate);
    
    // If no activity today, check if yesterday had activity to maintain streak
    if (!dailyTotals[checkStr] || dailyTotals[checkStr] === 0) {
        checkDate.setDate(checkDate.getDate() - 1);
        checkStr = getLocalISODate(checkDate);
    }
    
    // Count consecutive days backwards
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
    
    const last7Days = [];
    const daysOfWeek = ['Yak', 'Dush', 'Sesh', 'Chor', 'Pay', 'Jum', 'Shan'];
    let maxCount = 10; // Baseline to prevent div by zero
    
    for (let i = 6; i >= 0; i--) {
        const d = new Date();
        d.setDate(d.getDate() - i);
        const dStr = getLocalISODate(d);
        const count = dailyTotals[dStr] || 0;
        if (count > maxCount) maxCount = count;
        last7Days.push({
            dateStr: dStr,
            dayName: i === 0 ? 'Bugun' : daysOfWeek[d.getDay()],
            count: count
        });
    }
    
    last7Days.forEach(day => {
        let heightPct = Math.max((day.count / maxCount) * 100, 5);
        if (day.count === 0) heightPct = 5;
        
        const isToday = day.dayName === 'Bugun';
        const colorClass = isToday ? 'bg-[var(--accent)] shadow-lg shadow-emerald-500/20' : (day.count > 0 ? 'bg-emerald-200 dark:bg-emerald-800' : 'bg-gray-100 dark:bg-gray-800');
        
        const barDiv = document.createElement('div');
        barDiv.className = 'flex-1 flex flex-col justify-end group relative h-full';
        barDiv.innerHTML = `
            <div class="w-full ${colorClass} rounded-t-md transition-all duration-700 ease-out flex items-start justify-center relative" style="height: 0%">
                <span class="text-[9px] font-bold absolute -top-5 text-gray-600 dark:text-gray-300 opacity-0 group-hover:opacity-100 transition-opacity">${day.count > 0 ? day.count : ''}</span>
            </div>
        `;
        chartContainer.appendChild(barDiv);
        
        // Trigger animation
        setTimeout(() => {
            barDiv.querySelector('div').style.height = `${heightPct}%`;
        }, 50);
        
        const labelDiv = document.createElement('div');
        labelDiv.className = `flex-1 text-center truncate ${isToday ? 'text-[var(--accent)]' : ''}`;
        labelDiv.textContent = day.dayName;
        chartLabels.appendChild(labelDiv);
    });
}

// -----------------------------------------------------
// 3. TASBEH LOGIC
// -----------------------------------------------------

const counterEl = document.getElementById('counter');
const progressRing = document.getElementById('progress-ring');
const tapArea = document.getElementById('tap-area');
const circumference = 2 * Math.PI * 44;

progressRing.style.strokeDasharray = `${circumference} ${circumference}`;
progressRing.style.strokeDashoffset = circumference;

function selectDhikr(d) {
    currentDhikr = d;
    currentCount = d.daily_count || 0;
    
    document.getElementById('dhikr-title').textContent = d.title;
    document.getElementById('target-count').textContent = d.daily_target;
    
    updateCounterUI();
}

function updateCounterUI() {
    counterEl.textContent = currentCount;
    
    if (!currentDhikr) return;
    
    let percent = currentCount / currentDhikr.daily_target;
    if (percent > 1) percent = 1;
    
    const offset = circumference - (percent * circumference);
    progressRing.style.strokeDashoffset = offset;

    if (currentCount >= currentDhikr.daily_target) {
        progressRing.style.stroke = "#f59e0b"; // amber for done
    } else {
        progressRing.style.stroke = "var(--accent)"; 
    }
}

function handleTap(e) {
    if (e.cancelable) e.preventDefault();
    if (!currentDhikr) return;
    
    currentCount++;
    updateCounterUI();
    
    if (currentCount === currentDhikr.daily_target) {
        tg.HapticFeedback.notificationOccurred('success');
    } else if (currentCount % 33 === 0) {
        tg.HapticFeedback.impactOccurred('medium');
    } else {
        tg.HapticFeedback.impactOccurred('light');
    }
}

tapArea.addEventListener('mousedown', handleTap);
tapArea.addEventListener('touchstart', handleTap, {passive: false});

document.getElementById('reset-btn').addEventListener('click', () => {
    currentCount = 0;
    updateCounterUI();
    tg.HapticFeedback.impactOccurred('rigid');
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
        // Calculate diff to add to global count
        const diff = currentCount - (currentDhikr.daily_count || 0);
        const newGlobal = (currentDhikr.global_count || 0) + (diff > 0 ? diff : 0);
        
        // Update dhikr
        await supabaseClient.from('dhikrs').update({
            daily_count: currentCount,
            global_count: newGlobal
        }).eq('id', currentDhikr.id);
        
        // Update daily progress
        const today = new Date().toISOString().split('T')[0];
        
        // check if exists
        const { data: p } = await supabaseClient.from('daily_progress')
            .select('*').eq('user_id', userId).eq('dhikr_id', currentDhikr.id).eq('date', today).single();
            
        if (p) {
            await supabaseClient.from('daily_progress').update({ count: currentCount }).eq('id', p.id);
        } else {
            await supabaseClient.from('daily_progress').insert({
                user_id: userId, dhikr_id: currentDhikr.id, date: today, count: currentCount
            });
        }
        
        // Update local object
        currentDhikr.daily_count = currentCount;
        currentDhikr.global_count = newGlobal;
        
        tg.HapticFeedback.notificationOccurred('success');
        btn.innerHTML = `<i class="ph ph-check text-xl"></i> Saqlandi!`;
        
        // Also send data back to bot for summary message
        tg.sendData(JSON.stringify({
            action: 'save_dhikr',
            title: currentDhikr.title,
            count: currentCount,
            target: currentDhikr.daily_target
        }));
        
    } catch (err) {
        console.error(err);
        tg.HapticFeedback.notificationOccurred('error');
        btn.innerHTML = `<i class="ph ph-warning text-xl"></i> Xatolik`;
    }
    
    setTimeout(() => { btn.innerHTML = originalText; }, 2000);
});

// Profile Hard Reset
document.getElementById('hard-reset-btn').addEventListener('click', async () => {
    tg.showConfirm("Rostdan ham barcha statistika va zikrlarni o'chirasizmi? Bu amalni ortga qaytarib bo'lmaydi.", async (confirmed) => {
        if (confirmed) {
            await supabaseClient.from('dhikrs').delete().eq('user_id', userId);
            await supabaseClient.from('daily_progress').delete().eq('user_id', userId);
            tg.close();
        }
    });
});

// Start
initApp();
