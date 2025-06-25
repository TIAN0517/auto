// 4D科技贊助系統 - 主要 JavaScript 文件

// 全局變數
const App = {
  theme: localStorage.getItem('theme') || 'dark',
  notifications: [],
  modals: {},
  animations: {},
  config: {
    apiBaseUrl: '/api',
    animationDuration: 300,
    notificationTimeout: 5000,
    loadingTimeout: 2000
  }
};

// DOM 載入完成後初始化
document.addEventListener('DOMContentLoaded', function() {
  initializeApp();
});

// 應用程式初始化
function initializeApp() {
  console.log('🚀 4D科技贊助系統啟動中...');
  
  // 初始化各個模組
  initializeTheme();
  initializeNavigation();
  initializeModals();
  initializeAnimations();
  initializeNotifications();
  initializeLoadingScreen();
  initializeScrollEffects();
  initializeFormValidation();
  initializePaymentSystem();
  initializeStatusMonitoring();
  
  console.log('✅ 系統初始化完成');
}

// 主題系統
function initializeTheme() {
  const themeToggle = document.querySelector('.theme-toggle');
  const body = document.body;
  
  // 設置初始主題
  body.setAttribute('data-theme', App.theme);
  updateThemeIcon();
  
  // 主題切換事件
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }
  
  // 監聽系統主題變化
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', handleSystemThemeChange);
  }
}

function toggleTheme() {
  const themes = ['dark', 'light', 'high-contrast'];
  const currentIndex = themes.indexOf(App.theme);
  const nextIndex = (currentIndex + 1) % themes.length;
  
  App.theme = themes[nextIndex];
  document.body.setAttribute('data-theme', App.theme);
  localStorage.setItem('theme', App.theme);
  
  updateThemeIcon();
  showNotification(`已切換至${getThemeName(App.theme)}主題`, 'info');
}

function updateThemeIcon() {
  const themeToggle = document.querySelector('.theme-toggle');
  if (!themeToggle) return;
  
  const icons = {
    dark: '🌙',
    light: '☀️',
    'high-contrast': '🔆'
  };
  
  themeToggle.innerHTML = icons[App.theme] || '🌙';
}

function getThemeName(theme) {
  const names = {
    dark: '深色',
    light: '淺色',
    'high-contrast': '高對比度'
  };
  return names[theme] || '深色';
}

function handleSystemThemeChange(e) {
  if (!localStorage.getItem('theme')) {
    App.theme = e.matches ? 'dark' : 'light';
    document.body.setAttribute('data-theme', App.theme);
    updateThemeIcon();
  }
}

// 導航系統
function initializeNavigation() {
  const nav = document.querySelector('.main-nav');
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  const navMenu = document.querySelector('.nav-menu');
  
  // 滾動時導航欄效果
  window.addEventListener('scroll', handleNavScroll);
  
  // 移動端選單
  if (mobileMenuBtn && navMenu) {
    mobileMenuBtn.addEventListener('click', toggleMobileMenu);
  }
  
  // 導航連結點擊效果
  const navLinks = document.querySelectorAll('.nav-link');
  navLinks.forEach(link => {
    link.addEventListener('click', handleNavLinkClick);
  });
}

function handleNavScroll() {
  const nav = document.querySelector('.main-nav');
  if (!nav) return;
  
  const scrollY = window.scrollY;
  
  if (scrollY > 50) {
    nav.style.background = 'rgba(10, 10, 15, 0.98)';
    nav.style.backdropFilter = 'blur(20px)';
    nav.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
  } else {
    nav.style.background = 'rgba(10, 10, 15, 0.95)';
    nav.style.backdropFilter = 'blur(20px)';
    nav.style.boxShadow = 'none';
  }
}

function toggleMobileMenu() {
  const navMenu = document.querySelector('.nav-menu');
  const mobileMenuBtn = document.querySelector('.mobile-menu-btn');
  
  if (navMenu && mobileMenuBtn) {
    navMenu.classList.toggle('active');
    mobileMenuBtn.classList.toggle('active');
    
    // 更新按鈕圖標
    const isActive = mobileMenuBtn.classList.contains('active');
    mobileMenuBtn.innerHTML = isActive ? '✕' : '☰';
  }
}

function handleNavLinkClick(e) {
  const link = e.currentTarget;
  const href = link.getAttribute('href');
  
  // 如果是錨點連結，平滑滾動
  if (href && href.startsWith('#')) {
    e.preventDefault();
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }
  }
  
  // 更新活動狀態
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  link.classList.add('active');
  
  // 關閉移動端選單
  const navMenu = document.querySelector('.nav-menu');
  if (navMenu && navMenu.classList.contains('active')) {
    toggleMobileMenu();
  }
}

// 模態框系統
function initializeModals() {
  const modalTriggers = document.querySelectorAll('[data-modal]');
  const modalCloses = document.querySelectorAll('.modal-close, .modal-overlay');
  
  // 模態框觸發器
  modalTriggers.forEach(trigger => {
    trigger.addEventListener('click', (e) => {
      e.preventDefault();
      const modalId = trigger.getAttribute('data-modal');
      openModal(modalId);
    });
  });
  
  // 模態框關閉
  modalCloses.forEach(close => {
    close.addEventListener('click', (e) => {
      if (e.target === close) {
        closeModal();
      }
    });
  });
  
  // ESC 鍵關閉模態框
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
    }
  });
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (!modal) return;
  
  modal.classList.add('active');
  document.body.style.overflow = 'hidden';
  
  // 焦點管理
  const firstInput = modal.querySelector('input, button, textarea, select');
  if (firstInput) {
    setTimeout(() => firstInput.focus(), 100);
  }
  
  App.modals[modalId] = modal;
}

function closeModal(modalId) {
  if (modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove('active');
      delete App.modals[modalId];
    }
  } else {
    // 關閉所有模態框
    Object.values(App.modals).forEach(modal => {
      modal.classList.remove('active');
    });
    App.modals = {};
  }
  
  document.body.style.overflow = '';
}

// 動畫系統
function initializeAnimations() {
  // 觀察器設置
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };
  
  const observer = new IntersectionObserver(handleIntersection, observerOptions);
  
  // 觀察需要動畫的元素
  const animatedElements = document.querySelectorAll(
    '.feature-card, .payment-card, .pricing-card, .status-card, .section-header'
  );
  
  animatedElements.forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(30px)';
    observer.observe(el);
  });
  
  // 初始化粒子效果
  initializeParticles();
  
  // 初始化全息效果
  initializeHolographicEffects();
}

function handleIntersection(entries) {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const element = entry.target;
      
      // 添加動畫類別
      element.style.transition = 'all 0.6s ease';
      element.style.opacity = '1';
      element.style.transform = 'translateY(0)';
      
      // 停止觀察已動畫的元素
      observer.unobserve(element);
    }
  });
}

function initializeParticles() {
  const heroSection = document.querySelector('.hero-section');
  if (!heroSection) return;
  
  // 創建粒子容器
  const particlesContainer = document.createElement('div');
  particlesContainer.className = 'particles-container';
  particlesContainer.style.cssText = `
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 1;
  `;
  
  heroSection.appendChild(particlesContainer);
  
  // 創建粒子
  for (let i = 0; i < 50; i++) {
    createParticle(particlesContainer);
  }
}

function createParticle(container) {
  const particle = document.createElement('div');
  const size = Math.random() * 4 + 1;
  const x = Math.random() * 100;
  const y = Math.random() * 100;
  const duration = Math.random() * 20 + 10;
  
  particle.style.cssText = `
    position: absolute;
    width: ${size}px;
    height: ${size}px;
    background: rgba(0, 212, 255, ${Math.random() * 0.5 + 0.2});
    border-radius: 50%;
    left: ${x}%;
    top: ${y}%;
    animation: float ${duration}s infinite linear;
    box-shadow: 0 0 ${size * 2}px rgba(0, 212, 255, 0.5);
  `;
  
  container.appendChild(particle);
  
  // 添加浮動動畫
  const keyframes = `
    @keyframes float {
      0% { transform: translateY(0px) rotate(0deg); }
      50% { transform: translateY(-20px) rotate(180deg); }
      100% { transform: translateY(0px) rotate(360deg); }
    }
  `;
  
  if (!document.querySelector('#particle-animations')) {
    const style = document.createElement('style');
    style.id = 'particle-animations';
    style.textContent = keyframes;
    document.head.appendChild(style);
  }
}

function initializeHolographicEffects() {
  const holographicElements = document.querySelectorAll('.holographic');
  
  holographicElements.forEach(element => {
    element.addEventListener('mousemove', handleHolographicMove);
    element.addEventListener('mouseleave', handleHolographicLeave);
  });
}

function handleHolographicMove(e) {
  const element = e.currentTarget;
  const rect = element.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  
  const centerX = rect.width / 2;
  const centerY = rect.height / 2;
  
  const rotateX = (y - centerY) / 10;
  const rotateY = (centerX - x) / 10;
  
  element.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`;
}

function handleHolographicLeave(e) {
  const element = e.currentTarget;
  element.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
}

// 通知系統
function initializeNotifications() {
  // 創建通知容器
  if (!document.querySelector('.notification-container')) {
    const container = document.createElement('div');
    container.className = 'notification-container';
    document.body.appendChild(container);
  }
  
  // 通知按鈕事件
  const notificationBtn = document.querySelector('.notification-btn');
  if (notificationBtn) {
    notificationBtn.addEventListener('click', showTestNotification);
  }
}

function showNotification(message, type = 'info', duration = 5000) {
  const container = document.querySelector('.notification-container');
  if (!container) return;
  
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <div class="notification-content">
      <span class="notification-icon">${getNotificationIcon(type)}</span>
      <span class="notification-message">${message}</span>
      <button class="notification-close" onclick="closeNotification(this)">✕</button>
    </div>
  `;
  
  container.appendChild(notification);
  
  // 顯示動畫
  setTimeout(() => notification.classList.add('show'), 100);
  
  // 自動關閉
  if (duration > 0) {
    setTimeout(() => closeNotification(notification), duration);
  }
  
  App.notifications.push(notification);
  return notification;
}

function closeNotification(element) {
  const notification = element.closest ? element.closest('.notification') : element;
  if (!notification) return;
  
  notification.classList.remove('show');
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification);
    }
    
    const index = App.notifications.indexOf(notification);
    if (index > -1) {
      App.notifications.splice(index, 1);
    }
  }, 300);
}

function getNotificationIcon(type) {
  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };
  return icons[type] || 'ℹ️';
}

function showTestNotification() {
  const messages = [
    { text: '系統運行正常', type: 'success' },
    { text: '新的支付方式已啟用', type: 'info' },
    { text: '請注意系統維護時間', type: 'warning' },
    { text: '連接超時，請重試', type: 'error' }
  ];
  
  const randomMessage = messages[Math.floor(Math.random() * messages.length)];
  showNotification(randomMessage.text, randomMessage.type);
}

// 載入畫面
function initializeLoadingScreen() {
  const loadingScreen = document.querySelector('.loading-screen');
  if (!loadingScreen) return;
  
  // 模擬載入過程
  setTimeout(() => {
    loadingScreen.classList.add('hidden');
    
    // 載入完成後移除元素
    setTimeout(() => {
      if (loadingScreen.parentNode) {
        loadingScreen.parentNode.removeChild(loadingScreen);
      }
    }, 500);
  }, App.config.loadingTimeout);
}

// 滾動效果
function initializeScrollEffects() {
  // 平滑滾動到頂部按鈕
  createScrollToTopButton();
  
  // 滾動進度條
  createScrollProgressBar();
  
  // 視差滾動效果
  initializeParallaxEffects();
}

function createScrollToTopButton() {
  const button = document.createElement('button');
  button.className = 'scroll-to-top';
  button.innerHTML = '↑';
  button.style.cssText = `
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 50px;
    height: 50px;
    background: var(--gradient-primary);
    color: white;
    border: none;
    border-radius: 50%;
    font-size: 20px;
    cursor: pointer;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
    z-index: 1000;
    box-shadow: var(--shadow-lg);
  `;
  
  button.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
  
  document.body.appendChild(button);
  
  // 滾動顯示/隱藏
  window.addEventListener('scroll', () => {
    if (window.scrollY > 300) {
      button.style.opacity = '1';
      button.style.visibility = 'visible';
    } else {
      button.style.opacity = '0';
      button.style.visibility = 'hidden';
    }
  });
}

function createScrollProgressBar() {
  const progressBar = document.createElement('div');
  progressBar.className = 'scroll-progress';
  progressBar.style.cssText = `
    position: fixed;
    top: 0;
    left: 0;
    width: 0%;
    height: 3px;
    background: var(--gradient-primary);
    z-index: 9999;
    transition: width 0.1s ease;
  `;
  
  document.body.appendChild(progressBar);
  
  window.addEventListener('scroll', () => {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrollPercent = (scrollTop / docHeight) * 100;
    
    progressBar.style.width = `${Math.min(scrollPercent, 100)}%`;
  });
}

function initializeParallaxEffects() {
  const parallaxElements = document.querySelectorAll('.parallax');
  
  window.addEventListener('scroll', () => {
    const scrollY = window.scrollY;
    
    parallaxElements.forEach(element => {
      const speed = element.dataset.speed || 0.5;
      const yPos = -(scrollY * speed);
      element.style.transform = `translateY(${yPos}px)`;
    });
  });
}

// 表單驗證
function initializeFormValidation() {
  const forms = document.querySelectorAll('form');
  
  forms.forEach(form => {
    form.addEventListener('submit', handleFormSubmit);
    
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
      input.addEventListener('blur', validateField);
      input.addEventListener('input', clearFieldError);
    });
  });
}

function handleFormSubmit(e) {
  e.preventDefault();
  
  const form = e.target;
  const formData = new FormData(form);
  const isValid = validateForm(form);
  
  if (!isValid) {
    showNotification('請檢查表單內容', 'error');
    return;
  }
  
  // 顯示載入狀態
  const submitBtn = form.querySelector('button[type="submit"]');
  if (submitBtn) {
    submitBtn.classList.add('loading');
    submitBtn.disabled = true;
  }
  
  // 模擬提交
  setTimeout(() => {
    if (submitBtn) {
      submitBtn.classList.remove('loading');
      submitBtn.disabled = false;
    }
    
    showNotification('提交成功！', 'success');
    form.reset();
  }, 2000);
}

function validateForm(form) {
  const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
  let isValid = true;
  
  inputs.forEach(input => {
    if (!validateField({ target: input })) {
      isValid = false;
    }
  });
  
  return isValid;
}

function validateField(e) {
  const input = e.target;
  const value = input.value.trim();
  const type = input.type;
  const required = input.hasAttribute('required');
  
  let isValid = true;
  let errorMessage = '';
  
  // 必填驗證
  if (required && !value) {
    isValid = false;
    errorMessage = '此欄位為必填';
  }
  
  // 類型驗證
  if (value && type === 'email') {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      isValid = false;
      errorMessage = '請輸入有效的電子郵件地址';
    }
  }
  
  if (value && type === 'password') {
    if (value.length < 6) {
      isValid = false;
      errorMessage = '密碼至少需要6個字符';
    }
  }
  
  if (value && type === 'tel') {
    const phoneRegex = /^[0-9+\-\s()]+$/;
    if (!phoneRegex.test(value)) {
      isValid = false;
      errorMessage = '請輸入有效的電話號碼';
    }
  }
  
  // 顯示錯誤
  showFieldError(input, isValid ? '' : errorMessage);
  
  return isValid;
}

function showFieldError(input, message) {
  // 移除舊的錯誤訊息
  const existingError = input.parentNode.querySelector('.field-error');
  if (existingError) {
    existingError.remove();
  }
  
  // 更新輸入框樣式
  if (message) {
    input.classList.add('error');
    
    // 添加錯誤訊息
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    errorElement.style.cssText = `
      color: var(--error-color);
      font-size: 0.875rem;
      margin-top: 0.25rem;
    `;
    
    input.parentNode.appendChild(errorElement);
  } else {
    input.classList.remove('error');
  }
}

function clearFieldError(e) {
  const input = e.target;
  input.classList.remove('error');
  
  const errorElement = input.parentNode.querySelector('.field-error');
  if (errorElement) {
    errorElement.remove();
  }
}

// 支付系統
function initializePaymentSystem() {
  const paymentCards = document.querySelectorAll('.payment-card');
  const paymentButtons = document.querySelectorAll('.btn-payment');
  
  paymentCards.forEach(card => {
    card.addEventListener('click', selectPaymentMethod);
  });
  
  paymentButtons.forEach(button => {
    button.addEventListener('click', processPayment);
  });
}

function selectPaymentMethod(e) {
  const card = e.currentTarget;
  const method = card.dataset.method;
  
  // 移除其他選中狀態
  document.querySelectorAll('.payment-card').forEach(c => c.classList.remove('selected'));
  
  // 選中當前卡片
  card.classList.add('selected');
  
  showNotification(`已選擇 ${card.querySelector('.payment-name').textContent}`, 'info');
}

function processPayment(e) {
  e.preventDefault();
  
  const button = e.currentTarget;
  const amount = button.dataset.amount || '100';
  const selectedMethod = document.querySelector('.payment-card.selected');
  
  if (!selectedMethod) {
    showNotification('請先選擇支付方式', 'warning');
    return;
  }
  
  // 顯示載入狀態
  button.classList.add('loading');
  button.disabled = true;
  
  // 模擬支付處理
  setTimeout(() => {
    button.classList.remove('loading');
    button.disabled = false;
    
    const success = Math.random() > 0.2; // 80% 成功率
    
    if (success) {
      showNotification(`支付成功！金額：NT$ ${amount}`, 'success');
      // 這裡可以跳轉到成功頁面或更新UI
    } else {
      showNotification('支付失敗，請重試', 'error');
    }
  }, 3000);
}

// 狀態監控
function initializeStatusMonitoring() {
  updateSystemStatus();
  
  // 每30秒更新一次狀態
  setInterval(updateSystemStatus, 30000);
}

function updateSystemStatus() {
  const statusCards = document.querySelectorAll('.status-card');
  
  statusCards.forEach(card => {
    const indicator = card.querySelector('.status-indicator');
    const metrics = card.querySelectorAll('.metric-value');
    
    // 模擬狀態更新
    const isOnline = Math.random() > 0.1; // 90% 在線率
    
    if (indicator) {
      indicator.className = `status-indicator ${isOnline ? 'online' : 'error'}`;
      indicator.textContent = isOnline ? '運行正常' : '連接異常';
    }
    
    // 更新指標數據
    metrics.forEach(metric => {
      const type = metric.dataset.type;
      let value;
      
      switch (type) {
        case 'uptime':
          value = `${(Math.random() * 10 + 95).toFixed(1)}%`;
          break;
        case 'response':
          value = `${Math.floor(Math.random() * 50 + 10)}ms`;
          break;
        case 'load':
          value = `${(Math.random() * 30 + 10).toFixed(1)}%`;
          break;
        case 'memory':
          value = `${(Math.random() * 40 + 30).toFixed(1)}%`;
          break;
        default:
          value = Math.floor(Math.random() * 100);
      }
      
      metric.textContent = value;
    });
  });
}

// 工具函數
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

function throttle(func, limit) {
  let inThrottle;
  return function() {
    const args = arguments;
    const context = this;
    if (!inThrottle) {
      func.apply(context, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
}

function formatCurrency(amount, currency = 'TWD') {
  return new Intl.NumberFormat('zh-TW', {
    style: 'currency',
    currency: currency
  }).format(amount);
}

function formatDate(date, options = {}) {
  const defaultOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  };
  
  return new Intl.DateTimeFormat('zh-TW', { ...defaultOptions, ...options }).format(date);
}

function generateId(prefix = 'id') {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function copyToClipboard(text) {
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(() => {
      showNotification('已複製到剪貼板', 'success');
    }).catch(() => {
      fallbackCopyToClipboard(text);
    });
  } else {
    fallbackCopyToClipboard(text);
  }
}

function fallbackCopyToClipboard(text) {
  const textArea = document.createElement('textarea');
  textArea.value = text;
  textArea.style.position = 'fixed';
  textArea.style.left = '-999999px';
  textArea.style.top = '-999999px';
  document.body.appendChild(textArea);
  textArea.focus();
  textArea.select();
  
  try {
    document.execCommand('copy');
    showNotification('已複製到剪貼板', 'success');
  } catch (err) {
    showNotification('複製失敗', 'error');
  }
  
  document.body.removeChild(textArea);
}

// API 請求函數
async function apiRequest(endpoint, options = {}) {
  const defaultOptions = {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-Requested-With': 'XMLHttpRequest'
    }
  };
  
  const config = { ...defaultOptions, ...options };
  const url = `${App.config.apiBaseUrl}${endpoint}`;
  
  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error('API request failed:', error);
    return { success: false, error: error.message };
  }
}

// 性能監控
function initializePerformanceMonitoring() {
  // 監控頁面載入性能
  window.addEventListener('load', () => {
    const perfData = performance.getEntriesByType('navigation')[0];
    const loadTime = perfData.loadEventEnd - perfData.loadEventStart;
    
    console.log(`頁面載入時間: ${loadTime}ms`);
    
    if (loadTime > 3000) {
      console.warn('頁面載入時間過長，建議優化');
    }
  });
  
  // 監控資源載入
  const observer = new PerformanceObserver((list) => {
    list.getEntries().forEach((entry) => {
      if (entry.duration > 1000) {
        console.warn(`資源載入緩慢: ${entry.name} (${entry.duration}ms)`);
      }
    });
  });
  
  observer.observe({ entryTypes: ['resource'] });
}

// 錯誤處理
window.addEventListener('error', (e) => {
  console.error('JavaScript 錯誤:', e.error);
  showNotification('系統發生錯誤，請重新整理頁面', 'error');
});

window.addEventListener('unhandledrejection', (e) => {
  console.error('未處理的 Promise 拒絕:', e.reason);
  showNotification('網路請求失敗，請檢查連線', 'error');
});

// 導出全局函數
window.App = App;
window.showNotification = showNotification;
window.openModal = openModal;
window.closeModal = closeModal;
window.copyToClipboard = copyToClipboard;
window.formatCurrency = formatCurrency;
window.formatDate = formatDate;

console.log('🎉 4D科技贊助系統已就緒！');