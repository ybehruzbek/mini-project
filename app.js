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
    // 1. Fetch User Profile
    const { data: user } = await supabaseClient.from('users').select('*').eq('user_id', userId).single();
    if (user) {
        document.getElementById('profile-name').textContent = user.full_name || 'Foydalanuvchi';
        document.getElementById('profile-habit').textContent = (user.habit_level || 'Odat') + ' darajasi';
    }

    // 2. Fetch Dhikrs
    await fetchDhikrs();
}

async function fetchDhikrs() {
    const listEl = document.getElementById('dhikr-list');
    const { data: dhikrs, error } = await supabaseClient.from('dhikrs').select('*').eq('user_id', userId).order('id');
    
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
    const { data: dhikrs } = await supabaseClient.from('dhikrs').select('daily_count, global_count').eq('user_id', userId);
    
    let totalDaily = 0;
    let totalGlobal = 0;
    
    if (dhikrs) {
        dhikrs.forEach(d => {
            totalDaily += (d.daily_count || 0);
            totalGlobal += (d.global_count || 0);
        });
    }
    
    document.getElementById('stat-daily').textContent = totalDaily;
    document.getElementById('stat-global').textContent = totalGlobal;
    
    // Fetch last 5 days progress
    const { data: progress } = await supabaseClient.from('daily_progress')
        .select('date, count')
        .eq('user_id', userId)
        .order('date', { ascending: false })
        .limit(5);
        
    const pList = document.getElementById('progress-list');
    if (progress && progress.length > 0) {
        pList.innerHTML = progress.map(p => `
            <div class="glass-card p-3 flex justify-between items-center text-sm font-medium">
                <span class="opacity-70">${p.date}</span>
                <span class="text-[var(--accent)]">+${p.count} marta</span>
            </div>
        `).join('');
    } else {
        pList.innerHTML = `<p class="text-sm opacity-50 text-center py-2">Hali faollik yo'q</p>`;
    }
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
