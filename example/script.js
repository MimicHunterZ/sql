// API 基础地址
const API_BASE_URL = 'http://localhost:8080/api';
let gamesData = [];
let charts = {};

// 粒子追踪效果
const canvas = document.getElementById('particleCanvas');
const ctx = canvas.getContext('2d');

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', resizeCanvas);

let particles = [];
const MAX_PARTICLES = 80;

class Particle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.size = Math.random() * 5 + 2;
        this.speedX = (Math.random() - 0.5) * 1.2;
        this.speedY = (Math.random() - 0.5) * 1.2;
        this.opacity = 1;
        this.hue = Math.random() * 60 + 180;
    }
    
    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.opacity -= 0.015;
        this.size *= 0.97;
    }
    
    draw() {
        ctx.save();
        ctx.globalAlpha = this.opacity;
        const gradient = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.size * 3);
        gradient.addColorStop(0, `hsla(${this.hue}, 100%, 70%, ${this.opacity})`);
        gradient.addColorStop(0.5, `hsla(${this.hue}, 100%, 60%, ${this.opacity * 0.3})`);
        gradient.addColorStop(1, 'transparent');
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size * 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = `hsla(${this.hue}, 100%, 80%, ${this.opacity})`;
        ctx.shadowBlur = 15;
        ctx.shadowColor = `hsla(${this.hue}, 100%, 70%, 0.8)`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
    }
}

document.addEventListener('mousemove', (e) => {
    for (let i = 0; i < 3; i++) {
        particles.push(new Particle(
            e.clientX + (Math.random() - 0.5) * 15,
            e.clientY + (Math.random() - 0.5) * 15
        ));
    }
    while (particles.length > MAX_PARTICLES) particles.shift();
});

function animateParticles() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let i = particles.length - 1; i >= 0; i--) {
        particles[i].update();
        particles[i].draw();
        if (particles[i].opacity <= 0 || particles[i].size <= 0.3) particles.splice(i, 1);
    }
    requestAnimationFrame(animateParticles);
}
animateParticles();

// 3D卡片倾斜效果
function init3DCards(containerSelector, cardSelector) {
    const containers = document.querySelectorAll(containerSelector);
    containers.forEach(container => {
        container.addEventListener('mousemove', (e) => {
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = ((y - centerY) / centerY) * -10;
            const rotateY = ((x - centerX) / centerX) * 10;
            container.style.setProperty('--int-rotate-x', rotateX + 'deg');
            container.style.setProperty('--int-rotate-y', rotateY + 'deg');
        });
        container.addEventListener('mouseleave', () => {
            container.style.setProperty('--int-rotate-x', '0deg');
            container.style.setProperty('--int-rotate-y', '0deg');
        });
    });
}

// 初始化图表
function initCharts() {
    charts.score = echarts.init(document.getElementById('scoreChart'));
    charts.genre = echarts.init(document.getElementById('genreChart'));
    charts.tag = echarts.init(document.getElementById('tagChart'));
    charts.yearly = echarts.init(document.getElementById('yearlyChart'));
    window.addEventListener('resize', () => Object.values(charts).forEach(c => c.resize()));
}

// 爬取游戏数据
async function crawlGames() {
    try {
        showNotification('开始爬取数据...', 'info');
        await axios.post(`${API_BASE_URL}/crawler/crawl/all`);
        showNotification('爬取成功！', 'success');
        loadGamesData();
    } catch (error) {
        console.error('爬取数据失败:', error);
        showNotification('爬取失败，请检查后端服务是否启动', 'error');
    }
}

// 加载游戏数据
async function loadGamesData() {
    try {
        // 加载游戏列表
        const gamesResponse = await axios.get(`${API_BASE_URL}/games`);
        if (Array.isArray(gamesResponse.data)) {
            gamesData = gamesResponse.data;
        } else {
            gamesData = [];
        }
        updateStats();
        updateCharts();
        updateGamesGrid();
    } catch (error) {
        console.error('加载数据失败:', error);
        gamesData = [];
        updateGamesGrid();
        showNotification('加载数据失败，请检查后端服务是否启动', 'error');
    }
}

function updateStats() {
    const statsGrid = document.getElementById('statsGrid');
    const total = gamesData.length;
    const avgScore = total ? (gamesData.reduce((s, g) => s + (g.score || 0), 0) / total).toFixed(1) : '0';
    const genres = new Set();
    gamesData.forEach(g => {
        if (g.genres) g.genres.forEach(genre => genres.add(genre));
    });
    const years = gamesData.map(g => g.releaseYear).filter(y => y);
    const yearRange = years.length ? `${Math.min(...years)}-${Math.max(...years)}` : '-';
    
    statsGrid.innerHTML = `
        <div class="stat-card-container" data-card="stat1"><div class="stat-card"><div class="card-glow"></div><i class="fas fa-database"></i><div class="stat-number">${total}</div><div class="stat-label">游戏总数</div></div></div>
        <div class="stat-card-container" data-card="stat2"><div class="stat-card"><div class="card-glow"></div><i class="fas fa-star"></i><div class="stat-number">${avgScore}</div><div class="stat-label">平均评分</div></div></div>
        <div class="stat-card-container" data-card="stat3"><div class="stat-card"><div class="card-glow"></div><i class="fas fa-tags"></i><div class="stat-number">${genres.size}</div><div class="stat-label">游戏类型</div></div></div>
        <div class="stat-card-container" data-card="stat4"><div class="stat-card"><div class="card-glow"></div><i class="fas fa-calendar-alt"></i><div class="stat-number">${yearRange}</div><div class="stat-label">年份跨度</div></div></div>
    `;
    setTimeout(() => init3DCards('.stat-card-container', '.stat-card'), 100);
}

function updateCharts() {
    if (!gamesData.length) return;
    
    // 评分分布
    const scores = gamesData.map(g => g.score || 0).filter(s => s > 0);
    const bins = [0, 2, 4, 6, 8, 10];
    const counts = Array(bins.length - 1).fill(0);
    scores.forEach(s => {
        for (let i = 0; i < bins.length - 1; i++) {
            if (s >= bins[i] && s < bins[i+1]) { counts[i]++; break; }
        }
    });
    charts.score.setOption({
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(17,24,39,0.9)', borderColor: '#60a5fa' },
        grid: { left: '3%', right: '4%', containLabel: true },
        xAxis: { type: 'category', data: ['0-2分', '2-4分', '4-6分', '6-8分', '8-10分'], axisLabel: { color: '#9ca3af' } },
        yAxis: { type: 'value', name: '游戏数量', nameTextStyle: { color: '#9ca3af' }, axisLabel: { color: '#9ca3af' } },
        series: [{ data: counts, type: 'bar', itemStyle: { borderRadius: [8,8,0,0], color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: '#60a5fa' }, { offset: 1, color: '#a78bfa' }] } }, label: { show: true, color: '#e0e0e0' } }]
    });
    
    // 类型分布
    const genreCount = {};
    gamesData.forEach(g => {
        if (g.genres) {
            g.genres.forEach(genre => {
                if (genre && genre !== 'Unknown') {
                    genreCount[genre] = (genreCount[genre] || 0) + 1;
                }
            });
        }
    });
    const genreData = Object.entries(genreCount).sort((a,b) => b[1] - a[1]).slice(0, 8).map(([n,v]) => ({ name: n, value: v }));
    charts.genre.setOption({
        tooltip: { trigger: 'item', backgroundColor: 'rgba(17,24,39,0.9)', borderColor: '#60a5fa' },
        legend: { orient: 'vertical', left: 'left', textStyle: { color: '#9ca3af' } },
        series: [{ type: 'pie', radius: '55%', data: genreData, itemStyle: { borderRadius: 8, borderColor: '#0a0a1a', borderWidth: 2 }, label: { color: '#e0e0e0' } }]
    });
    
    // 热门标签
    const tagCount = {};
    gamesData.forEach(g => {
        if (g.tags) {
            g.tags.forEach(t => {
                if (t) tagCount[t] = (tagCount[t] || 0) + 1;
            });
        }
    });
    const tagData = Object.entries(tagCount).sort((a,b) => b[1] - a[1]).slice(0, 12);
    charts.tag.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '15%', containLabel: true },
        xAxis: { type: 'value', name: '出现次数', axisLabel: { color: '#9ca3af' } },
        yAxis: { type: 'category', data: tagData.map(d => d[0]), axisLabel: { color: '#9ca3af' } },
        series: [{ data: tagData.map(d => d[1]), type: 'bar', itemStyle: { borderRadius: [0,8,8,0], color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: '#f093fb' }, { offset: 1, color: '#f5576c' }] } }, label: { show: true, position: 'right', color: '#e0e0e0' } }]
    });
    
    // 年度趋势
    const yearScores = {};
    gamesData.forEach(g => {
        if (g.releaseYear && g.score) {
            if (!yearScores[g.releaseYear]) {
                yearScores[g.releaseYear] = { sum: 0, count: 0 };
            }
            yearScores[g.releaseYear].sum += g.score;
            yearScores[g.releaseYear].count++;
        }
    });
    const years = Object.keys(yearScores).sort();
    const avgScores = years.map(y => (yearScores[y].sum / yearScores[y].count).toFixed(1));
    charts.yearly.setOption({
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(17,24,39,0.9)', borderColor: '#60a5fa' },
        xAxis: { type: 'category', data: years, name: '年份', axisLabel: { rotate: 45, color: '#9ca3af' } },
        yAxis: { type: 'value', name: '平均评分', min: 0, max: 10, axisLabel: { color: '#9ca3af' } },
        series: [{ data: avgScores, type: 'line', smooth: true, lineStyle: { width: 3, color: '#60a5fa' }, areaStyle: { color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: 'rgba(96,165,250,0.3)' }, { offset: 1, color: 'rgba(167,139,250,0.1)' }] } }, symbol: 'circle', symbolSize: 8, label: { show: true, color: '#e0e0e0' } }]
    });
}

function updateGamesGrid() {
    const grid = document.getElementById('gamesGrid');
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    let filtered = gamesData.filter(g => g.title && g.title.toLowerCase().includes(searchTerm));
    if (!filtered.length) {
        grid.innerHTML = '<div class="loading-text"><i class="fas fa-inbox"></i> 暂无游戏数据</div>';
        return;
    }
    grid.innerHTML = filtered.map(game => `
        <div class="game-card-container" data-game='${JSON.stringify(game)}' onclick="showGameDetail(${JSON.stringify(game).replace(/"/g, '&quot;')})">
            <div class="game-card" style="--int-rotate-x:0deg;--int-rotate-y:0deg">
                <div class="card-glow"></div>
                <div class="game-name">
                    <span>${escapeHtml(game.title || '未知游戏')}</span>
                    <span class="game-score">${game.score ? game.score.toFixed(1) : '-'}</span>
                </div>
                <div class="game-info">
                    <span><i class="fas fa-calendar"></i> ${game.releaseYear || '未知'}</span>
                    <span><i class="fas fa-desktop"></i> ${game.platforms ? game.platforms.join(', ') : '多平台'}</span>
                </div>
                <div class="game-tags">
                    ${(game.tags || ['游戏']).slice(0, 3).map(t => `<span class="game-tag">${escapeHtml(t)}</span>`).join('')}
                </div>
            </div>
        </div>
    `).join('');
    setTimeout(() => {
        document.querySelectorAll('.game-card-container').forEach(el => {
            const card = el.querySelector('.game-card');
            el.addEventListener('mousemove', (e) => {
                const rect = el.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                const rotateX = ((y - centerY) / centerY) * -8;
                const rotateY = ((x - centerX) / centerX) * 8;
                card.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
            });
            el.addEventListener('mouseleave', () => { card.style.transform = ''; });
        });
    }, 50);
}

function showGameDetail(game) {
    const modal = document.getElementById('gameModal');
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div class="modal-game-name">${escapeHtml(game.title || '未知游戏')}</div>
        <div class="modal-game-score"><i class="fas fa-star"></i> ${game.score ? game.score.toFixed(1) : '暂无评分'} / 10</div>
        <div class="modal-game-detail"><i class="fas fa-calendar"></i> 发行年份：${game.releaseYear || '未知'}</div>
        <div class="modal-game-detail"><i class="fas fa-desktop"></i> 平台：${game.platforms ? game.platforms.join(', ') : '多平台'}</div>
        <div class="modal-game-detail"><i class="fas fa-tag"></i> 类型：${game.genres ? game.genres.join(', ') : '未知'}</div>
        <div class="modal-game-detail"><i class="fas fa-hashtag"></i> 标签：${(game.tags || ['游戏']).slice(0, 5).join(' · ')}</div>
        <div class="modal-game-detail"><i class="fas fa-building"></i> 开发商：${game.developer || '未知'}</div>
        <div class="modal-game-detail"><i class="fas fa-globe"></i> 发行商：${game.publisher || '未知'}</div>
    `;
    modal.classList.add('active');
}

function escapeHtml(str) {
    if (!str) return '-';
    return String(str).replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

function showNotification(msg, type) {
    const notif = document.createElement('div');
    notif.style.cssText = `position:fixed;top:20px;right:20px;padding:12px 20px;background:${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};color:#fff;border-radius:8px;z-index:1001;animation:fadeInDown 0.3s ease;box-shadow:0 4px 12px rgba(0,0,0,0.3)`;
    notif.textContent = msg;
    document.body.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
}

// 页面加载完成后初始化
window.onload = function() {
    initCharts();
    
    // 绑定按钮事件
    document.getElementById('crawlBtn').addEventListener('click', crawlGames);
    document.getElementById('refreshBtn').addEventListener('click', loadGamesData);
    document.getElementById('searchInput').addEventListener('input', updateGamesGrid);
    document.getElementById('modalClose').addEventListener('click', () => document.getElementById('gameModal').classList.remove('active'));
    document.getElementById('gameModal').addEventListener('click', (e) => {
        if (e.target === document.getElementById('gameModal')) {
            document.getElementById('gameModal').classList.remove('active');
        }
    });
    
    // 初始加载数据
    loadGamesData();
};
