const tg = window.Telegram.WebApp;
tg.expand(); // Mini app'ni butun ekranga ochish

let count = 0;
let target = 100;
let dhikrTitle = "Astag'firulloh";

const counterEl = document.getElementById('counter');
const progressRing = document.getElementById('progress-ring');
const tapArea = document.getElementById('tap-area');
const resetBtn = document.getElementById('reset-btn');
const saveBtn = document.getElementById('save-btn');
const dhikrTitleEl = document.getElementById('dhikr-title');
const targetCountEl = document.getElementById('target-count');

// Aylana uzunligi (2 * PI * r) qayerda r = 44 (svg ichida)
const circumference = 2 * Math.PI * 44;
progressRing.style.strokeDasharray = `${circumference} ${circumference}`;
progressRing.style.strokeDashoffset = circumference;

function updateUI() {
    counterEl.textContent = count;
    
    // Progressni hisoblash (0 dan 100 gacha)
    let percent = count / target;
    if (percent > 1) percent = 1; // 100% dan oshmasligi uchun
    
    // Offsetni hisoblash (0 offset = to'liq halqa)
    const offset = circumference - (percent * circumference);
    progressRing.style.strokeDashoffset = offset;

    // Tugatganda rangini o'zgartirish (Apple uslubi)
    if (count >= target) {
        progressRing.style.stroke = "#FF9500"; // iOS Orange
    } else {
        progressRing.style.stroke = "#34C759"; // iOS Green
    }
}

function handleTap(e) {
    if (e.cancelable) e.preventDefault(); // Double tap zoom'ni to'xtatish
    
    count++;
    updateUI();
    
    // Haptic Feedback (vibratsiya)
    if (count === target) {
        tg.HapticFeedback.notificationOccurred('success');
    } else if (count % 33 === 0) {
        tg.HapticFeedback.impactOccurred('medium');
    } else {
        tg.HapticFeedback.impactOccurred('light');
    }
}

// Butun markaziy qismni bosish mumkin
tapArea.addEventListener('mousedown', handleTap);
tapArea.addEventListener('touchstart', handleTap, {passive: false});

resetBtn.addEventListener('click', () => {
    count = 0;
    updateUI();
    tg.HapticFeedback.impactOccurred('rigid');
});

saveBtn.addEventListener('click', () => {
    const data = JSON.stringify({
        action: 'save_dhikr',
        title: dhikrTitle,
        count: count
    });
    // Telegram botga ma'lumot jo'natish
    tg.sendData(data);
});

// Boshlang'ich holatni o'rnatish
updateUI();

// Telegram tema ranglarini qabul qilish
tg.onEvent('themeChanged', function() {
    document.body.style.backgroundColor = tg.themeParams.bg_color || '#ffffff';
    document.body.style.color = tg.themeParams.text_color || '#000000';
});
