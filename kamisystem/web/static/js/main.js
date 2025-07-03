// 主要的JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // 初始化弹出框
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    const popoverList = [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    // 自动关闭Alert
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        if (alert.classList.contains('alert-success') || alert.classList.contains('alert-info')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
    
    // 表格行高亮
    const tableRows = document.querySelectorAll('tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = '#f8f9fa';
        });
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
    
    // 复制到剪贴板功能
    window.copyToClipboard = function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                showToast('已复制到剪贴板', 'success');
            }).catch(err => {
                console.error('复制失败:', err);
                showToast('复制失败', 'error');
            });
        } else {
            // 降级方案
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                showToast('已复制到剪贴板', 'success');
            } catch (err) {
                console.error('复制失败:', err);
                showToast('复制失败', 'error');
            }
            document.body.removeChild(textArea);
        }
    };
    
    // 显示Toast消息
    window.showToast = function(message, type = 'info') {
        const toastContainer = getOrCreateToastContainer();
        const toastEl = createToast(message, type);
        toastContainer.appendChild(toastEl);
        
        const toast = new bootstrap.Toast(toastEl);
        toast.show();
        
        // 自动清理
        toastEl.addEventListener('hidden.bs.toast', () => {
            toastEl.remove();
        });
    };
    
    // 获取或创建Toast容器
    function getOrCreateToastContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container position-fixed top-0 end-0 p-3';
            container.style.zIndex = '1055';
            document.body.appendChild(container);
        }
        return container;
    }
    
    // 创建Toast元素
    function createToast(message, type) {
        const toastEl = document.createElement('div');
        toastEl.className = 'toast';
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        
        const typeColors = {
            success: 'text-bg-success',
            error: 'text-bg-danger',
            warning: 'text-bg-warning',
            info: 'text-bg-info'
        };
        
        const typeIcons = {
            success: 'bi-check-circle',
            error: 'bi-exclamation-triangle',
            warning: 'bi-exclamation-triangle',
            info: 'bi-info-circle'
        };
        
        toastEl.innerHTML = `
            <div class="toast-header ${typeColors[type] || 'text-bg-info'}">
                <i class="bi ${typeIcons[type] || 'bi-info-circle'} me-2"></i>
                <strong class="me-auto">系统消息</strong>
                <small>刚刚</small>
                <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        return toastEl;
    }
    
    // 确认对话框
    window.confirmAction = function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    };
    
    // 格式化时间
    window.formatTime = function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };
    
    // 格式化数字
    window.formatNumber = function(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    };
    
    // 检查网络状态
    window.addEventListener('online', function() {
        showToast('网络连接已恢复', 'success');
    });
    
    window.addEventListener('offline', function() {
        showToast('网络连接已断开', 'warning');
    });
    
    // 键盘快捷键
    document.addEventListener('keydown', function(e) {
        // Ctrl+K 聚焦搜索框
        if (e.ctrlKey && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[name="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape 关闭模态框
        if (e.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
    
    // 表单验证增强
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
                
                // 聚焦到第一个无效字段
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            form.classList.add('was-validated');
        });
    });
    
    // 自动保存表单数据
    const autoSaveForms = document.querySelectorAll('[data-auto-save]');
    autoSaveForms.forEach(form => {
        const formId = form.getAttribute('data-auto-save');
        
        // 恢复保存的数据
        const savedData = localStorage.getItem(`form_${formId}`);
        if (savedData) {
            const data = JSON.parse(savedData);
            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = data[key];
                }
            });
        }
        
        // 监听表单变化
        form.addEventListener('input', function() {
            const formData = new FormData(form);
            const data = {};
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            localStorage.setItem(`form_${formId}`, JSON.stringify(data));
        });
        
        // 提交后清除保存的数据
        form.addEventListener('submit', function() {
            localStorage.removeItem(`form_${formId}`);
        });
    });
    
    // 懒加载图片
    const lazyImages = document.querySelectorAll('img[data-lazy]');
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.lazy;
                    img.classList.remove('lazy');
                    observer.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    }
    
    // 平滑滚动
    const scrollLinks = document.querySelectorAll('a[href^="#"]');
    scrollLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // 页面加载进度
    window.addEventListener('beforeunload', function() {
        document.body.classList.add('page-loading');
    });
    
    // 代码高亮（如果有prism.js）
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    }
    
    // 打印功能
    window.printPage = function() {
        window.print();
    };
    
    // 全屏功能
    window.toggleFullscreen = function() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    };
    
    // 主题切换
    window.toggleTheme = function() {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    };
    
    // 恢复主题设置
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.body.setAttribute('data-theme', savedTheme);
    }
    
    // 设置页面标题
    window.setPageTitle = function(title) {
        document.title = title + ' - 卡密授权管理系统';
    };
    
    // 显示加载状态
    window.showLoading = function(element) {
        if (element) {
            element.disabled = true;
            element.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>加载中...';
        }
    };
    
    // 隐藏加载状态
    window.hideLoading = function(element, originalText) {
        if (element) {
            element.disabled = false;
            element.innerHTML = originalText;
        }
    };
    
    console.log('卡密授权管理系统已就绪');
});

// 全局错误处理
window.addEventListener('error', function(e) {
    console.error('发生错误:', e.error);
    // 可以在这里添加错误上报逻辑
});

// 未处理的Promise拒绝
window.addEventListener('unhandledrejection', function(e) {
    console.error('未处理的Promise拒绝:', e.reason);
    // 可以在这里添加错误上报逻辑
});

// 导出常用函数
window.KamiSystem = {
    copyToClipboard: window.copyToClipboard,
    showToast: window.showToast,
    confirmAction: window.confirmAction,
    formatTime: window.formatTime,
    formatNumber: window.formatNumber,
    toggleTheme: window.toggleTheme,
    setPageTitle: window.setPageTitle,
    showLoading: window.showLoading,
    hideLoading: window.hideLoading
};
