/**
 * Stock & Scan Pro - Frontend Application
 * Maneja autenticación, multi-tenancy y comandos
 */

class StockApp {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.user = JSON.parse(localStorage.getItem('user_data') || '{}');
        this.currentLang = localStorage.getItem('lang') || 'es';
        this.currentTheme = localStorage.getItem('theme') || 'dark';
        this.translations = {};
        this.init();
    }

    async init() {
        // Cargar traducciones
        await this.loadLanguage(this.currentLang);
        
        // Aplicar tema
        this.applyTheme(this.currentTheme);
        
        // Mostrar vista apropiada
        if (this.token && this.user.id) {
            this.showMainApp();
        } else {
            this.showAuthView('view-login');
        }
    }

    async loadLanguage(lang) {
        try {
            const response = await fetch(`/src/ui/lang/${lang}.json`);
            if (response.ok) {
                this.translations = await response.json();
                this.applyTranslations();
            }
        } catch (e) {
            console.error('Error loading language:', e);
        }
    }

    applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (this.translations[key]) {
                el.textContent = this.translations[key];
            }
        });
    }

    applyTheme(theme) {
        const root = document.documentElement;
        
        if (theme === 'light') {
            root.style.setProperty('--background', '#f8fafc');
            root.style.setProperty('--surface', 'rgba(255, 255, 255, 0.9)');
            root.style.setProperty('--surface-light', 'rgba(248, 250, 252, 0.8)');
            root.style.setProperty('--text', '#1e293b');
            root.style.setProperty('--text-muted', '#64748b');
            root.style.setProperty('--border', 'rgba(148, 163, 184, 0.3)');
        } else if (theme === 'night') {
            root.style.setProperty('--background', '#000000');
            root.style.setProperty('--surface', 'rgba(10, 10, 10, 0.8)');
            root.style.setProperty('--surface-light', 'rgba(20, 20, 20, 0.6)');
            root.style.setProperty('--text', '#ffffff');
            root.style.setProperty('--text-muted', '#a0a0a0');
            root.style.setProperty('--border', 'rgba(100, 100, 100, 0.2)');
        } else {
            // dark (default)
            root.style.setProperty('--background', '#0f172a');
            root.style.setProperty('--surface', 'rgba(15, 23, 42, 0.7)');
            root.style.setProperty('--surface-light', 'rgba(30, 41, 59, 0.5)');
            root.style.setProperty('--text', '#f1f5f9');
            root.style.setProperty('--text-muted', '#cbd5e1');
            root.style.setProperty('--border', 'rgba(148, 163, 184, 0.2)');
        }
        
        localStorage.setItem('theme', theme);
        this.currentTheme = theme;
    }

    showAuthView(viewId) {
        // Ocultar todas las vistas
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        document.getElementById('sidebar').style.display = 'none';
        
        // Mostrar vista de autenticación
        const view = document.getElementById(viewId);
        if (view) {
            view.classList.add('active');
        }
    }

    showMainApp() {
        // Ocultar vistas de auth
        document.getElementById('view-login').classList.remove('active');
        document.getElementById('view-register').classList.remove('active');
        
        // Mostrar sidebar y vista principal
        document.getElementById('sidebar').style.display = 'flex';
        document.getElementById('view-stock').classList.add('active');
        
        // Actualizar info de usuario
        this.updateUserInfo();
        
        // Cargar datos iniciales
        this.loadStock();
    }

    updateUserInfo() {
        const userInfo = document.getElementById('user-info');
        if (userInfo && this.user) {
            userInfo.innerHTML = `
                <strong>${this.user.username}</strong><br>
                <small>${this.user.role}</small><br>
                <small>Plan: ${this.user.plan || 'FREE'}</small>
            `;
        }
    }

    async login() {
        const username = document.getElementById('login-user').value;
        const password = document.getElementById('login-pass').value;

        if (!username || !password) {
            alert('Por favor completa todos los campos');
            return;
        }

        try {
            const response = await fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: 'auth.login',
                    username,
                    password
                })
            });

            const data = await response.json();
            
            if (data.payload.status === 'success') {
                this.token = data.payload.token;
                this.user = data.payload.user;
                
                localStorage.setItem('auth_token', this.token);
                localStorage.setItem('user_data', JSON.stringify(this.user));
                
                this.showMainApp();
            } else {
                alert('Error: ' + (data.payload.message || 'Login fallido'));
            }
        } catch (e) {
            alert('Error de conexión: ' + e.message);
        }
    }

    async registerOwner() {
        const business_name = document.getElementById('reg-business').value;
        const username = document.getElementById('reg-user').value;
        const password = document.getElementById('reg-pass').value;

        if (!business_name || !username || !password) {
            alert('Por favor completa todos los campos');
            return;
        }

        try {
            const response = await fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    command: 'auth.register_owner',
                    business_name,
                    username,
                    password
                })
            });

            const data = await response.json();
            
            if (data.payload.status === 'success') {
                alert('Cuenta creada exitosamente. Inicia sesión.');
                this.switchView('view-login');
            } else {
                alert('Error: ' + (data.payload.message || 'Registro fallido'));
            }
        } catch (e) {
            alert('Error de conexión: ' + e.message);
        }
    }

    switchView(viewId) {
        // Ocultar todas las vistas
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        
        // Mostrar vista seleccionada
        const view = document.getElementById(viewId);
        if (view) {
            view.classList.add('active');
        }
        
        // Actualizar nav activo
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-view') === viewId) {
                item.classList.add('active');
            }
        });
    }

    async loadStock() {
        if (!this.token) return;

        try {
            const response = await fetch('/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': this.token
                },
                body: JSON.stringify({
                    command: 'stock.list',
                    params: {}
                })
            });

            const data = await response.json();
            
            if (data.payload.status === 'success') {
                this.renderStockTable(data.payload.data || []);
            }
        } catch (e) {
            console.error('Error loading stock:', e);
        }
    }

    renderStockTable(items) {
        const tbody = document.getElementById('stock-table-body');
        if (!tbody) return;

        tbody.innerHTML = '';
        
        items.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.code || '-'}</td>
                <td>${item.name || '-'}</td>
                <td>${item.category || '-'}</td>
                <td>$${parseFloat(item.price || 0).toFixed(2)}</td>
                <td>${item.quantity || 0}</td>
                <td>
                    <button class="btn btn-secondary" style="padding:6px 12px; font-size:0.8rem;">Editar</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    togglePassword(inputId) {
        const input = document.getElementById(inputId);
        if (input.type === 'password') {
            input.type = 'text';
        } else {
            input.type = 'password';
        }
    }

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    }

    setTheme(theme) {
        this.applyTheme(theme);
        document.getElementById('theme-select').value = theme;
    }

    setLang(lang) {
        this.currentLang = lang;
        localStorage.setItem('lang', lang);
        this.loadLanguage(lang);
        document.getElementById('lang-select').value = lang;
    }

    async exportCSV() {
        alert('Función de exportación en desarrollo');
    }

    async handleFileUpload(input) {
        if (!input.files.length) return;
        
        const file = input.files[0];
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                headers: {
                    'Authorization': this.token
                },
                body: formData
            });

            const data = await response.json();
            
            if (data.payload.status === 'success') {
                document.getElementById('import-status').textContent = '✅ Archivo cargado';
                document.getElementById('btn-run-import').disabled = false;
            } else {
                document.getElementById('import-status').textContent = '❌ Error: ' + data.payload.message;
            }
        } catch (e) {
            document.getElementById('import-status').textContent = '❌ Error: ' + e.message;
        }
    }

    async runImportPreview() {
        alert('Función de importación en desarrollo');
    }

    async commitImport() {
        alert('Función de importación en desarrollo');
    }

    async quickAddProduct() {
        alert('Función de búsqueda rápida en desarrollo');
    }

    async openCheckout() {
        alert('Función de checkout en desarrollo');
    }

    async addAlias() {
        alert('Función de alias en desarrollo');
    }

    async addEmployee() {
        alert('Función de empleados en desarrollo');
    }

    async openCash() {
        alert('Función de caja en desarrollo');
    }

    async closeCash() {
        alert('Función de caja en desarrollo');
    }

    showModal(modalId) {
        alert('Modal en desarrollo');
    }

    logout() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        this.token = null;
        this.user = {};
        this.showAuthView('view-login');
    }
}

// Inicializar app cuando el DOM esté listo
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new StockApp();
});

