/**
 * 坐姿监测系统 - 前端主程序
 *
 * 功能：
 * - 摄像头访问
 * - WebSocket实时通信
 * - Canvas绘制关键点
 * - 提醒触发
 * - 统计数据更新
 */

// ============================================================================
// 全局变量和配置
// ============================================================================

const APP_CONFIG = {
    wsUrl: `ws://${window.location.host}/ws/posture`,
    apiUrl: `/api`,
    frameRate: 10, // 每秒发送帧数
    videoWidth: 640,
    videoHeight: 480
};

// 应用状态
const appState = {
    isMonitoring: false,
    ws: null,
    stream: null,
    video: null,
    canvas: null,
    ctx: null,
    frameInterval: null,
    fpsCounter: {
        frames: 0,
        lastTime: Date.now()
    },
    statistics: {
        alertCount: 0,
        monitorStartTime: null,
        goodTimeAccumulator: 0,
        lastStatusChange: Date.now()
    }
};

// COCO 17 关键点连接关系（19条，用于绘制骨架）
const POSE_CONNECTIONS = [
    // 头部: nose-eyes-ears
    [0, 1], [0, 2], [1, 2], [1, 3], [2, 4],
    // 头肩连接
    [3, 5], [4, 6],
    // 躯干: shoulders-hips
    [5, 6], [5, 11], [6, 12], [11, 12],
    // 上肢: shoulders-elbows-wrists
    [5, 7], [7, 9], [6, 8], [8, 10],
    // 下肢: hips-knees-ankles
    [11, 13], [13, 15], [12, 14], [14, 16]
];

const POSE_COLOR_VARS = {
    normal: '--pose-color-normal',
    headForward: '--pose-color-head-forward',
    hunchback: '--pose-color-hunchback',
    crossedLegs: '--pose-color-crossed-legs'
};

// ============================================================================
// DOM元素引用
// ============================================================================

let elements = {};

function initElements() {
    elements = {
        // 视频和画布
        video: document.getElementById('videoElement'),
        canvas: document.getElementById('canvasElement'),
        videoOverlay: document.getElementById('videoOverlay'),
        overlayText: document.getElementById('overlayText'),

        // 控制按钮
        startBtn: document.getElementById('startBtn'),
        stopBtn: document.getElementById('stopBtn'),

        // 状态显示
        statusDot: document.getElementById('statusDot'),
        statusText: document.getElementById('statusText'),
        fpsValue: document.getElementById('fpsValue'),
        detectionStatus: document.getElementById('detectionStatus'),
        issuesValue: document.getElementById('issuesValue'),

        // 实时角度
        headAngle: document.getElementById('headAngle'),
        hunchOffset: document.getElementById('hunchOffset'),
        legsDiff: document.getElementById('legsDiff'),

        // 统计数据
        alertCount: document.getElementById('alertCount'),
        monitorTime: document.getElementById('monitorTime'),
        goodTime: document.getElementById('goodTime'),

        // 本周统计
        weeklyGoodCount: document.getElementById('goodCount'),
        weeklyWarningCount: document.getElementById('warningCount'),
        weeklyBadCount: document.getElementById('badCount'),
        weeklyTotalRecords: document.getElementById('totalRecords'),

        // 设置
        settingsBtn: document.getElementById('settingsBtn'),
        settingsModal: document.getElementById('settingsModal'),
        closeSettingsBtn: document.getElementById('closeSettingsBtn'),
        cancelSettingsBtn: document.getElementById('cancelSettingsBtn'),
        saveSettingsBtn: document.getElementById('saveSettingsBtn'),

        // 设置输入
        headThreshold: document.getElementById('headThreshold'),
        hunchThreshold: document.getElementById('hunchThreshold'),
        legsThreshold: document.getElementById('legsThreshold'),
        cooldownSeconds: document.getElementById('cooldownSeconds'),
        enableSound: document.getElementById('enableSound'),
        enablePopup: document.getElementById('enablePopup'),

        // 提醒弹窗
        alertPopup: document.getElementById('alertPopup'),
        alertTitle: document.getElementById('alertTitle'),
        alertMessage: document.getElementById('alertMessage'),
        alertSuggestions: document.getElementById('alertSuggestions'),
        closeAlertBtn: document.getElementById('closeAlertBtn')
    };

    appState.video = elements.video;
    appState.canvas = elements.canvas;
    appState.ctx = elements.canvas.getContext('2d');
}

// ============================================================================
// 摄像头访问
// ============================================================================

async function initCamera() {
    try {
        updateOverlay('正在请求摄像头权限...', false);

        const constraints = {
            video: {
                width: { ideal: APP_CONFIG.videoWidth },
                height: { ideal: APP_CONFIG.videoHeight },
                facingMode: 'user'
            },
            audio: false
        };

        appState.stream = await navigator.mediaDevices.getUserMedia(constraints);
        appState.video.srcObject = appState.stream;

        // 等待视频准备就绪
        await new Promise((resolve) => {
            appState.video.onloadedmetadata = () => {
                appState.video.play();
                resolve();
            };
        });

        // 设置Canvas尺寸匹配视频
        const videoWidth = appState.video.videoWidth;
        const videoHeight = appState.video.videoHeight;
        appState.canvas.width = videoWidth;
        appState.canvas.height = videoHeight;

        console.log(`摄像头初始化成功: ${videoWidth}x${videoHeight}`);
        return true;
    } catch (error) {
        console.error('摄像头访问失败:', error);
        updateOverlay(`摄像头访问失败: ${error.message}`, false);
        return false;
    }
}

function stopCamera() {
    if (appState.stream) {
        appState.stream.getTracks().forEach(track => track.stop());
        appState.stream = null;
        appState.video.srcObject = null;
        console.log('摄像头已停止');
    }
}

// ============================================================================
// WebSocket 连接
// ============================================================================

function connectWebSocket() {
    return new Promise((resolve, reject) => {
        try {
            console.log('正在连接 WebSocket:', APP_CONFIG.wsUrl);
            appState.ws = new WebSocket(APP_CONFIG.wsUrl);

            // 设置连接超时（5秒）
            const timeout = setTimeout(() => {
                if (appState.ws.readyState !== WebSocket.OPEN) {
                    appState.ws.close();
                    reject(new Error('WebSocket 连接超时（5秒），请检查网络或服务器状态'));
                }
            }, 5000);

            appState.ws.onopen = () => {
                clearTimeout(timeout);
                console.log('WebSocket 连接成功');
                updateStatus('good', '已连接');
                updateOverlay('连接成功，正在检测...', true);
                resolve();
            };

            appState.ws.onmessage = (event) => {
                handleWebSocketMessage(event.data);
            };

            appState.ws.onerror = (event) => {
                clearTimeout(timeout);
                console.error('WebSocket 错误事件:', event);
                updateStatus('bad', '连接错误');
                // WebSocket 的 onerror 不提供详细错误信息，需要手动创建
                reject(new Error('WebSocket 连接失败，请检查服务器是否运行在 ' + APP_CONFIG.wsUrl));
            };

            appState.ws.onclose = (event) => {
                clearTimeout(timeout);
                console.log('WebSocket 连接已关闭, code:', event.code, 'reason:', event.reason);
                updateStatus('bad', '未连接');
                if (appState.isMonitoring) {
                    stopMonitoring();
                    alert('WebSocket连接已断开，监测已停止');
                }
            };
        } catch (error) {
            console.error('WebSocket 创建失败:', error);
            reject(new Error('无法创建 WebSocket 连接: ' + error.message));
        }
    });
}

function disconnectWebSocket() {
    if (appState.ws) {
        appState.ws.close();
        appState.ws = null;
    }
}

function sendFrame() {
    if (!appState.ws || appState.ws.readyState !== WebSocket.OPEN) {
        console.warn('WebSocket 未连接，停止发送帧');
        stopMonitoring();
        return;
    }

    // 绘制当前视频帧到Canvas
    appState.ctx.drawImage(
        appState.video,
        0, 0,
        appState.canvas.width,
        appState.canvas.height
    );

    // 将Canvas转换为Base64
    const frameData = appState.canvas.toDataURL('image/jpeg', 0.8);

    // 发送到服务器
    appState.ws.send(JSON.stringify({
        type: 'video_frame',
        data: frameData.split(',')[1], // 移除 data:image/jpeg;base64, 前缀
        timestamp: Date.now() / 1000
    }));

    // 更新FPS
    updateFPS();
}

// ============================================================================
// WebSocket 消息处理
// ============================================================================

function handleWebSocketMessage(data) {
    try {
        const message = JSON.parse(data);

        switch (message.type) {
            case 'posture_result':
                handlePostureResult(message);
                break;
            case 'error':
                console.error('服务器错误:', message.message);
                elements.detectionStatus.textContent = '检测错误';
                break;
            default:
                console.warn('未知消息类型:', message.type);
        }
    } catch (error) {
        console.error('消息解析失败:', error);
    }
}

function handlePostureResult(message) {
    const { pose_landmarks, analysis, alert, timestamp } = message;

    // 更新检测状态
    if (pose_landmarks && pose_landmarks.length > 0) {
        elements.detectionStatus.textContent = '检测中';

        // 绘制关键点和骨架
        drawPose(pose_landmarks, analysis);

        // 更新状态指示器
        const status = analysis.status || 'good';
        const statusText = getStatusText(status);
        updateStatus(status, statusText);

        // 更新问题列表
        const issues = analysis.issues || [];
        elements.issuesValue.textContent = issues.length > 0
            ? issues.map(i => getIssueText(i)).join(', ')
            : '无';

        // 更新实时角度
        if (analysis.angles) {
            elements.headAngle.textContent = analysis.angles.head_forward
                ? `${analysis.angles.head_forward.toFixed(1)}°`
                : '--';
            elements.hunchOffset.textContent = analysis.angles.hunchback
                ? analysis.angles.hunchback.toFixed(3)
                : '--';
            elements.legsDiff.textContent = analysis.angles.crossed_legs
                ? analysis.angles.crossed_legs.toFixed(3)
                : '--';
        }

        // 更新统计数据
        updateStatistics(status);

        // 处理提醒
        if (alert && alert.should_alert) {
            handleAlert(alert);
        }
    } else {
        elements.detectionStatus.textContent = '未检测到人体';
        clearCanvas();
    }
}

// ============================================================================
// Canvas 绘制
// ============================================================================

function getPoseColor(analysis) {
    const rootStyle = getComputedStyle(document.documentElement);
    const issues = Array.isArray(analysis?.issues) ? analysis.issues : [];
    let colorVar = POSE_COLOR_VARS.normal;

    if (issues.includes('hunchback')) {
        colorVar = POSE_COLOR_VARS.hunchback;
    } else if (issues.includes('head_forward')) {
        colorVar = POSE_COLOR_VARS.headForward;
    } else if (issues.includes('crossed_legs')) {
        colorVar = POSE_COLOR_VARS.crossedLegs;
    }

    return rootStyle.getPropertyValue(colorVar).trim() || '#00FF00';
}

function drawPose(landmarks, analysis) {
    const ctx = appState.ctx;
    const canvas = appState.canvas;

    if (!Array.isArray(landmarks) || landmarks.length === 0) {
        return;
    }

    const poseColor = getPoseColor(analysis);

    // 绘制骨架连线
    ctx.strokeStyle = poseColor;
    ctx.lineWidth = 2;
    ctx.beginPath();

    for (const [startIdx, endIdx] of POSE_CONNECTIONS) {
        const start = landmarks[startIdx];
        const end = landmarks[endIdx];

        if (!start || !end) {
            continue;
        }

        const startVisibility = Number.isFinite(start.visibility) ? start.visibility : 0;
        const endVisibility = Number.isFinite(end.visibility) ? end.visibility : 0;
        if (startVisibility > 0.5 && endVisibility > 0.5) {
            const startX = start.x * canvas.width;
            const startY = start.y * canvas.height;
            const endX = end.x * canvas.width;
            const endY = end.y * canvas.height;

            ctx.moveTo(startX, startY);
            ctx.lineTo(endX, endY);
        }
    }
    ctx.stroke();

    // 绘制关键点
    for (const landmark of landmarks) {
        if (!landmark) {
            continue;
        }

        const visibility = Number.isFinite(landmark.visibility) ? landmark.visibility : 0;
        if (visibility > 0.5) {
            const x = landmark.x * canvas.width;
            const y = landmark.y * canvas.height;

            // 绘制外圈
            ctx.fillStyle = poseColor;
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, 2 * Math.PI);
            ctx.fill();

            // 绘制内圈
            ctx.fillStyle = '#FFFFFF';
            ctx.beginPath();
            ctx.arc(x, y, 2, 0, 2 * Math.PI);
            ctx.fill();
        }
    }
}

function clearCanvas() {
    const ctx = appState.ctx;
    ctx.clearRect(0, 0, appState.canvas.width, appState.canvas.height);

    // 绘制当前视频帧
    ctx.drawImage(
        appState.video,
        0, 0,
        appState.canvas.width,
        appState.canvas.height
    );
}

// ============================================================================
// 提醒处理
// ============================================================================

function handleAlert(alert) {
    console.log('触发提醒:', alert);

    // 更新提醒计数
    appState.statistics.alertCount++;
    elements.alertCount.textContent = appState.statistics.alertCount;

    // 显示弹窗提醒
    if (alert.popup_alert) {
        showAlertPopup(alert.popup_alert);
    }

    // 播放声音提醒
    if (alert.sound_alert) {
        playAlertSound(alert.sound_alert);
    }

    // 提醒后刷新本周统计（因为数据库新增了记录）
    loadWeeklyStats();
}

function showAlertPopup(popupData) {
    elements.alertTitle.textContent = popupData.title || '坐姿提醒';
    elements.alertMessage.textContent = popupData.summary || '检测到不良坐姿';

    // 显示建议
    elements.alertSuggestions.innerHTML = '';
    if (popupData.suggestions && popupData.suggestions.length > 0) {
        popupData.suggestions.forEach(suggestion => {
            const li = document.createElement('li');
            li.textContent = suggestion;
            elements.alertSuggestions.appendChild(li);
        });
    }

    // 显示弹窗
    elements.alertPopup.classList.add('show');

    // 3秒后自动关闭
    setTimeout(() => {
        closeAlertPopup();
    }, 3000);
}

function closeAlertPopup() {
    elements.alertPopup.classList.remove('show');
}

function playAlertSound(soundData) {
    // 使用 Web Audio API 播放提醒音
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.type = soundData.wave_type || 'sine';
        oscillator.frequency.value = soundData.frequency || 440;
        gainNode.gain.value = soundData.volume || 0.5;

        const duration = soundData.duration || 0.3;
        oscillator.start();
        oscillator.stop(audioContext.currentTime + duration);

        console.log('播放提醒音:', soundData);
    } catch (error) {
        console.error('播放声音失败:', error);
    }
}

// ============================================================================
// 统计数据
// ============================================================================

function updateStatistics(currentStatus) {
    const now = Date.now();

    // 更新监测时长
    if (appState.statistics.monitorStartTime) {
        const totalSeconds = Math.floor((now - appState.statistics.monitorStartTime) / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        elements.monitorTime.textContent = `${minutes}分钟`;
    }

    // 累积良好时长
    if (currentStatus === 'good') {
        appState.statistics.goodTimeAccumulator += now - appState.statistics.lastStatusChange;
    }
    appState.statistics.lastStatusChange = now;

    const goodSeconds = Math.floor(appState.statistics.goodTimeAccumulator / 1000);
    const goodMinutes = Math.floor(goodSeconds / 60);
    elements.goodTime.textContent = `${goodMinutes}分钟`;
}

async function loadTodayStatistics() {
    try {
        const today = new Date();
        const startTime = new Date(today.setHours(0, 0, 0, 0)).toISOString();
        const endTime = new Date(today.setHours(23, 59, 59, 999)).toISOString();

        const response = await fetch(
            `${APP_CONFIG.apiUrl}/statistics?period=day&end_time=${endTime}`
        );

        if (response.ok) {
            const data = await response.json();
            elements.alertCount.textContent = data.total_records || 0;
            console.log('今日统计加载成功:', data);
        }
    } catch (error) {
        console.error('加载今日统计失败:', error);
    }
}

async function loadWeeklyStats() {
    try {
        console.log('📊 正在加载本周统计数据...');
        const url = `${APP_CONFIG.apiUrl}/statistics?period=week`;
        console.log('请求URL:', url);

        const response = await fetch(url);
        console.log('响应状态:', response.status);

        if (response.ok) {
            const data = await response.json();
            console.log('📊 本周统计数据返回:', data);
            displayWeeklyStats(data);
        } else {
            console.error('❌ API响应失败:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('❌ 加载本周统计失败:', error);
    }
}

function displayWeeklyStats(data) {
    console.log('📊 开始显示本周统计...');
    const distribution = data.posture_distribution || {};
    console.log('姿态分布:', distribution);

    // 检查DOM元素是否存在
    if (!elements.weeklyGoodCount) {
        console.error('❌ 找不到 weeklyGoodCount 元素');
        return;
    }

    // 更新各项数字
    const goodCount = distribution.good || 0;
    const warningCount = distribution.warning || 0;
    const badCount = distribution.bad || 0;
    const totalRecords = data.total_records || 0;

    elements.weeklyGoodCount.textContent = goodCount;
    elements.weeklyWarningCount.textContent = warningCount;
    elements.weeklyBadCount.textContent = badCount;
    elements.weeklyTotalRecords.textContent = totalRecords;

    console.log(`✅ 本周统计已更新: 良好=${goodCount}, 欠佳=${warningCount}, 不良=${badCount}, 总计=${totalRecords}`);
}

// ============================================================================
// 监测控制
// ============================================================================

async function startMonitoring() {
    if (appState.isMonitoring) {
        console.warn('监测已在运行中');
        return;
    }

    try {
        console.log('开始启动监测...');

        // 1. 初始化摄像头
        console.log('步骤1: 初始化摄像头...');
        const cameraOk = await initCamera();
        if (!cameraOk) {
            throw new Error('摄像头初始化失败，请检查摄像头权限或设备连接');
        }

        // 2. 连接WebSocket
        console.log('步骤2: 连接 WebSocket...');
        await connectWebSocket();

        // 3. 开始发送帧
        console.log('步骤3: 开始发送视频帧...');
        const frameDelay = 1000 / APP_CONFIG.frameRate;
        appState.frameInterval = setInterval(sendFrame, frameDelay);

        // 4. 更新状态
        appState.isMonitoring = true;
        appState.statistics.monitorStartTime = Date.now();
        appState.statistics.lastStatusChange = Date.now();

        // 5. 更新UI
        elements.startBtn.disabled = true;
        elements.stopBtn.disabled = false;

        console.log('✅ 监测已成功启动');
    } catch (error) {
        console.error('❌ 启动监测失败:', error);
        stopMonitoring();

        // 确保错误信息有意义
        const errorMessage = error && error.message
            ? error.message
            : '未知错误，请查看浏览器控制台获取详细信息';

        alert(`启动监测失败:\n\n${errorMessage}\n\n请确保:\n1. 服务器正在运行\n2. 摄像头权限已授予\n3. 浏览器支持WebSocket和摄像头`);
    }
}

function stopMonitoring() {
    if (!appState.isMonitoring) {
        return;
    }

    // 1. 停止发送帧
    if (appState.frameInterval) {
        clearInterval(appState.frameInterval);
        appState.frameInterval = null;
    }

    // 2. 断开WebSocket
    disconnectWebSocket();

    // 3. 停止摄像头
    stopCamera();

    // 4. 更新状态
    appState.isMonitoring = false;

    // 5. 更新UI
    elements.startBtn.disabled = false;
    elements.stopBtn.disabled = true;
    updateStatus('bad', '未连接');
    updateOverlay('监测已停止', false);

    console.log('监测已停止');
}

// ============================================================================
// UI更新辅助函数
// ============================================================================

function updateStatus(status, text) {
    elements.statusDot.className = `status-dot ${status}`;
    elements.statusText.textContent = text;
}

function updateOverlay(text, hideAfterDelay = false) {
    elements.overlayText.textContent = text;

    if (hideAfterDelay) {
        setTimeout(() => {
            elements.videoOverlay.classList.add('hidden');
        }, 1000);
    } else {
        elements.videoOverlay.classList.remove('hidden');
    }
}

function updateFPS() {
    appState.fpsCounter.frames++;
    const now = Date.now();
    const elapsed = now - appState.fpsCounter.lastTime;

    if (elapsed >= 1000) {
        const fps = Math.round(appState.fpsCounter.frames / (elapsed / 1000));
        elements.fpsValue.textContent = fps;
        appState.fpsCounter.frames = 0;
        appState.fpsCounter.lastTime = now;
    }
}

function getStatusText(status) {
    const statusMap = {
        'good': '坐姿良好',
        'warning': '坐姿欠佳',
        'bad': '坐姿不良'
    };
    return statusMap[status] || status;
}

function getIssueText(issue) {
    const issueMap = {
        'head_forward': '头部前倾',
        'hunchback': '驼背',
        'crossed_legs': '跷二郎腿'
    };
    return issueMap[issue] || issue;
}

// ============================================================================
// 设置管理
// ============================================================================

function openSettings() {
    // 加载当前设置
    loadSettings();
    elements.settingsModal.classList.add('show');
}

function closeSettings() {
    elements.settingsModal.classList.remove('show');
}

async function loadSettings() {
    try {
        const response = await fetch(`${APP_CONFIG.apiUrl}/settings`);
        if (response.ok) {
            const data = await response.json();

            // 填充表单
            elements.headThreshold.value = data.detection_thresholds.head_forward_angle;
            elements.hunchThreshold.value = data.detection_thresholds.hunchback_offset;
            elements.legsThreshold.value = data.detection_thresholds.crossed_legs_diff;
            elements.cooldownSeconds.value = data.alert_settings.cooldown_seconds;
            elements.enableSound.checked = data.alert_settings.enable_sound;
            elements.enablePopup.checked = data.alert_settings.enable_popup;

            console.log('设置加载成功:', data);
        }
    } catch (error) {
        console.error('加载设置失败:', error);
    }
}

async function saveSettings() {
    const settings = {
        detection_thresholds: {
            head_forward_angle: parseFloat(elements.headThreshold.value),
            hunchback_offset: parseFloat(elements.hunchThreshold.value),
            crossed_legs_diff: parseFloat(elements.legsThreshold.value)
        },
        alert_settings: {
            cooldown_seconds: parseFloat(elements.cooldownSeconds.value),
            enable_sound: elements.enableSound.checked,
            enable_popup: elements.enablePopup.checked
        }
    };

    try {
        const response = await fetch(`${APP_CONFIG.apiUrl}/settings`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(settings)
        });

        if (response.ok) {
            const data = await response.json();
            console.log('设置保存成功:', data);
            alert('设置已保存！');
            closeSettings();
        } else {
            throw new Error('保存失败');
        }
    } catch (error) {
        console.error('保存设置失败:', error);
        alert(`保存设置失败: ${error.message}`);
    }
}

// ============================================================================
// 事件绑定
// ============================================================================

function bindEvents() {
    // 控制按钮
    elements.startBtn.addEventListener('click', startMonitoring);
    elements.stopBtn.addEventListener('click', stopMonitoring);

    // 设置
    elements.settingsBtn.addEventListener('click', openSettings);
    elements.closeSettingsBtn.addEventListener('click', closeSettings);
    elements.cancelSettingsBtn.addEventListener('click', closeSettings);
    elements.saveSettingsBtn.addEventListener('click', saveSettings);

    // 提醒弹窗
    elements.closeAlertBtn.addEventListener('click', closeAlertPopup);

    // 点击模态框外部关闭
    elements.settingsModal.addEventListener('click', (e) => {
        if (e.target === elements.settingsModal) {
            closeSettings();
        }
    });

    // 页面卸载时清理资源
    window.addEventListener('beforeunload', () => {
        stopMonitoring();
    });
}

// ============================================================================
// 应用初始化
// ============================================================================

async function initApp() {
    console.log('🚀 坐姿监测系统初始化...');

    // 初始化DOM元素
    initElements();
    console.log('✅ DOM元素初始化完成');

    // 绑定事件
    bindEvents();
    console.log('✅ 事件绑定完成');

    // 加载今日统计
    console.log('📊 加载今日统计...');
    await loadTodayStatistics();

    // 加载本周统计
    console.log('📊 加载本周统计...');
    await loadWeeklyStats();

    // 定期刷新本周统计（每5分钟）
    setInterval(() => {
        console.log('⏰ 定时刷新本周统计...');
        loadWeeklyStats();
    }, 5 * 60 * 1000);

    console.log('✅ 系统初始化完成');
}

// 页面加载完成后初始化
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initApp);
} else {
    initApp();
}
