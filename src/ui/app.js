/**
 * Stock & Scan Pro - Frontend Application
 * Maneja autenticación, multi-tenancy y comandos
 */

const API_BASE = '';

// Función de utilidad para evitar llamadas excesivas a la API
function debounce(func, wait = 300) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

const app = {
    state: {
        currentView: localStorage.getItem('current_view') || 'view-login',
        token: localStorage.getItem('session_token'),
        user: JSON.parse(localStorage.getItem('user_data') || '{}'),
        role: localStorage.getItem('user_role') || 'empleado',
        isPro: false,
        theme: localStorage.getItem('theme') || 'dark',
        lang: localStorage.getItem('lang') || 'es',
        cart: [],
        translations: {}
    },

    async init() {
        console.log("🚀 Stock Pro: Iniciando aplicación...");
        try {
            await this.loadConfig();
            await this.loadTranslations();
            this.applyTheme();
            this.applyTranslations();
            this.setupDebouncedHandlers();
            
            if (this.state.token && this.state.user.id) {
                console.log("✅ Sesión activa detectada.");
                this.setupAuthenticatedUI();
                this.loadStock();
                const targetView = (this.state.currentView && this.state.currentView !== 'view-login') 
                    ? this.state.currentView 
                    : 'view-stock';
                this.switchView(targetView);
            } else {
                console.log("🔑 No hay sesión activa, redirigiendo al Login.");
                this.switchView('view-login');
            }
        } catch (e) {
            console.error("❌ Error crítico durante la inicialización:", e);
            alert("Error al cargar la aplicación. Por favor, revisa la consola.");
        }
    },

    setupAuthenticatedUI() {
        // Mostrar menú de personal si es Dueño
        if (this.state.role === 'OWNER') {
            const navPersonnel = document.getElementById('nav-personnel');
            if (navPersonnel) navPersonnel.classList.remove('hidden');
        }
        
        // Actualizar info de usuario y suscripción
        const userInfo = document.getElementById('user-info');
        if (userInfo && this.state.user) {
            userInfo.innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <strong>👤 ${this.state.user.username}</strong>
                    <button onclick="app.logout()" style="border:none; background:none; cursor:pointer; color:var(--error); font-size:0.7rem; font-weight:bold; padding:0;">Salir</button>
                </div>
                <span style="color: var(--text-muted)">Plan: ${this.state.user.plan || 'FREE'}</span><br>
                <span style="color: var(--primary)">🪙 Créditos: ${this.state.user.credits || 0}</span>
            `;
        }

        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.style.display = 'flex';
    },

    async loadConfig() {
        try {
            const res = await fetch(`${API_BASE}/api/config`);
            const data = await res.json();
            if (data.payload && data.payload.status === 'success') {
                this.state.version = data.payload.data?.version;
                const badge = document.getElementById('version-badge');
                if (badge) {
                    badge.innerText = '✨ Stock Pro v2.0';
                    badge.style.backgroundColor = 'var(--primary)';
                    badge.style.color = 'white';
                }
            }
        } catch (e) { console.error("Config load error", e); }
    },

    async loadTranslations() {
        try {
            const res = await fetch(`/src/ui/lang/${this.state.lang}.json`);
            this.state.translations = await res.json();
        } catch (e) { console.error("Lang load error", e); }
    },

    applyTranslations() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.innerText = this.state.translations[key] || key;
        });
    },

    toggleSidebar() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar) sidebar.classList.toggle('open');
        if (overlay) overlay.classList.toggle('active');
    },

    async setTheme(themeName) {
        this.state.theme = themeName;
        localStorage.setItem('theme', themeName);
        try {
            await this.apiCall('sys.theme.set', { value: themeName });
            this.applyTheme();
        } catch (e) { console.error(e); }
    },

    async applyTheme() {
        const root = document.documentElement;
        
        if (this.state.theme === 'light') {
            root.style.setProperty('--background', '#f8fafc');
            root.style.setProperty('--surface', 'rgba(255, 255, 255, 0.9)');
            root.style.setProperty('--text', '#1e293b');
            root.style.setProperty('--text-muted', '#64748b');
        } else if (this.state.theme === 'night') {
            root.style.setProperty('--background', '#000000');
            root.style.setProperty('--surface', 'rgba(10, 10, 10, 0.8)');
            root.style.setProperty('--text', '#ffffff');
            root.style.setProperty('--text-muted', '#a0a0a0');
        } else {
            // dark (default)
            root.style.setProperty('--background', '#0f172a');
            root.style.setProperty('--surface', 'rgba(15, 23, 42, 0.7)');
            root.style.setProperty('--text', '#f1f5f9');
            root.style.setProperty('--text-muted', '#cbd5e1');
        }
    },

    async setLang(langCode) {
        this.state.lang = langCode;
        localStorage.setItem('lang', langCode);
        try {
            await this.apiCall('sys.lang.set', { value: langCode });
            await this.loadTranslations();
            this.applyTranslations();
        } catch (e) { console.error(e); }
    },

    switchView(viewId) {
        this.state.currentView = viewId;
        localStorage.setItem('current_view', viewId);
        
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        const view = document.getElementById(viewId);
        if (view) view.classList.add('active');
        
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.getAttribute('data-view') === viewId);
        });

        if (viewId === 'view-personnel') {
            this.loadPersonnel();
        }
        if (viewId === 'view-subscription') {
            this.loadSubscription();
        }

        // Ocultar UI global en pantallas de Auth
        const isAuthView = (viewId === 'view-login' || viewId === 'view-register');
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.style.display = isAuthView ? 'none' : 'flex';
    },

    async apiCall(command, params = {}) {
        try {
            const headers = { 'Content-Type': 'application/json' };
            if (this.state.token) {
                headers['Authorization'] = this.state.token;
            }

            const response = await fetch(`${API_BASE}/`, {
                method: 'POST',
                headers: headers,
                body: JSON.stringify({
                    command,
                    params,
                    role: this.state.role,
                    is_pro: this.state.isPro
                })
            });
            
            if (!response.ok) {
                throw new Error(`Server responded with ${response.status}: ${response.statusText}`);
            }

            const res = await response.json();
            return res.payload || res;
        } catch (e) {
            console.error("API Error:", e);
            return { status: "error", message: `Error de conexión: ${e.message}` };
        }
    },

    // --- AUTH METHODS ---

    async login() {
        const user = document.getElementById('login-user').value;
        const pass = document.getElementById('login-pass').value;
        const res = await this.apiCall('auth.login', { username: user, password: pass });
        
        if (res.status === 'success') {
            this.state.token = res.token;
            this.state.user = res.user;
            this.state.role = res.user.role;
            
            localStorage.setItem('session_token', res.token);
            localStorage.setItem('user_data', JSON.stringify(res.user));
            localStorage.setItem('user_role', res.user.role);
            
            this.setupAuthenticatedUI();
            this.loadStock();
            this.switchView('view-stock');
        } else {
            alert(res.message || 'Login fallido');
        }
    },

    async registerOwner() {
        const biz = document.getElementById('reg-business').value;
        const user = document.getElementById('reg-user').value;
        const pass = document.getElementById('reg-pass').value;
        const res = await this.apiCall('auth.register_owner', { 
            business_name: biz, 
            username: user, 
            password: pass 
        });
        
        if (res.status === 'success') {
            alert("Negocio registrado con éxito. Ahora puedes iniciar sesión.");
            this.switchView('view-login');
        } else {
            alert(res.message || 'Registro fallido');
        }
    },

    async logout() {
        localStorage.clear();
        this.state.token = null;
        this.state.user = {};
        this.state.role = 'empleado';
        this.switchView('view-login');
    },

    togglePassword(inputId) {
        const input = document.getElementById(inputId);
        if (input) {
            input.type = input.type === 'password' ? 'text' : 'password';
        }
    },

    // --- PERSONNEL MANAGEMENT ---

    async inviteEmployee() {
        const user = document.getElementById('emp-user')?.value.trim();
        const pass = document.getElementById('emp-pass')?.value;
        
        if (!user || !pass) {
            alert("Por favor, ingrese usuario y contraseña");
            return;
        }

        const res = await this.apiCall('auth.create_employee', { 
            username: user, 
            password: pass, 
            tenant_id: this.state.user.tenant_id 
        });
        
        if (res.status === 'success') {
            alert("Empleado agregado correctamente ✅");
            document.getElementById('emp-user').value = '';
            document.getElementById('emp-pass').value = '';
            this.loadPersonnel();
        } else {
            alert("Error al invitar empleado: " + res.message);
        }
    },

    async setPermission(userId, permKey, granted) {
        const res = await this.apiCall('user.set_permission', { 
            tenant_id: this.state.user.tenant_id, 
            user_id: userId, 
            permission_key: permKey, 
            granted: granted 
        });
        if (res.status === 'success') this.loadPersonnel();
        else alert(res.message);
    },

    async revokeAccess(userId) {
        if (!confirm("¿Estás seguro de revocar el acceso a este usuario?")) return;
        const res = await this.apiCall('user.revoke_access', { user_id: userId });
        if (res.status === 'success') this.loadPersonnel();
        else alert(res.message);
    },

    async loadPersonnel() {
        const res = await this.apiCall('user.list', { tenant_id: this.state.user.tenant_id });
        const container = document.getElementById('personnel-table-body');
        if (!container) return;
        
        container.innerHTML = '';
        
        if (res.status === 'success' && res.data) {
            res.data.forEach(u => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${u.username}</td>
                    <td><span class="badge badge-success">${u.role}</span></td>
                    <td>
                        <button class="btn btn-secondary" style="padding:4px 8px" onclick="app.promptPermission('${u.id}')">🔑</button>
                        <button class="btn btn-danger" style="padding:4px 8px" onclick="app.revokeAccess('${u.id}')">🗑️</button>
                    </td>
                `;
                container.appendChild(row);
            });
        }
    },

    async promptPermission(userId) {
        const permKey = prompt("Ingrese la llave del permiso (ej: perm_stock_read):");
        if (!permKey) return;
        const granted = confirm(`¿Desea CONCEDER el permiso ${permKey}?`);
        await this.setPermission(userId, permKey, granted);
    },

    // --- STOCK MANAGEMENT ---

    async loadStock() {
        const filter = document.getElementById('stock-search')?.value || '';
        const res = await this.apiCall('stock.list', { filter });
        const tbody = document.getElementById('stock-table-body');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (res.status === 'success' && res.data) {
            res.data.forEach(p => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${p.code || p.codigo || '-'}</td>
                    <td>${p.name || p.nombre || '-'}</td>
                    <td>${p.category || p.categoria || '-'}</td>
                    <td>$${parseFloat(p.price || p.precio || 0).toFixed(2)}</td>
                    <td>${p.quantity || p.cantidad || 0}</td>
                    <td>
                        <button class="btn btn-secondary" style="padding:4px 8px" onclick="app.editProduct('${p.code || p.codigo}')">✏️</button>
                        <button class="btn btn-danger" style="padding:4px 8px" onclick="app.deleteProduct('${p.code || p.codigo}')">🗑️</button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    },

    setupDebouncedHandlers() {
        this.debouncedLoadStock = debounce(() => this.loadStock());
        this.debouncedQuickAdd = debounce(() => this.quickAddProduct());
    },

    showModal(id) { 
        const modal = document.getElementById(id);
        if (modal) modal.classList.remove('hidden'); 
    },
    
    closeModal(id) { 
        const modal = document.getElementById(id);
        if (modal) modal.classList.add('hidden'); 
    },

    async saveProduct() {
        const params = {
            code: document.getElementById('p-code')?.value,
            name: document.getElementById('p-name')?.value,
            price: parseFloat(document.getElementById('p-price')?.value || 0),
            quantity: parseFloat(document.getElementById('p-qty')?.value || 0),
            category: document.getElementById('p-cat')?.value,
            is_weight: document.getElementById('p-weight')?.checked || false
        };
        const res = await this.apiCall('stock.add', params);
        if (res.status === 'success') {
            this.closeModal('modal-product');
            this.loadStock();
        } else { alert(res.message); }
    },

    async editProduct(code) {
        const res = await this.apiCall('stock.get', { code });
        if (res.status === 'success') {
            const p = res.data;
            document.getElementById('p-code').value = p.code || p.codigo;
            document.getElementById('p-name').value = p.name || p.nombre;
            document.getElementById('p-price').value = p.price || p.precio;
            document.getElementById('p-qty').value = p.quantity || p.cantidad;
            document.getElementById('p-cat').value = p.category || p.categoria;
            document.getElementById('p-weight').checked = p.is_weight || p.es_peso;
            this.showModal('modal-product');
        }
    },

    async deleteProduct(code) {
        if (confirm('¿Eliminar este producto?')) {
            const res = await this.apiCall('stock.delete', { code });
            if (res.status === 'success') this.loadStock();
        }
    },

    // --- SALES MANAGEMENT ---

    async quickAddProduct() {
        const code = document.getElementById('sale-scan')?.value;
        if (!code || code.length < 2) return;
        const res = await this.apiCall('sales.add_item', { code });
        if (res.status === 'success') {
            this.state.cart.push(res.data);
            this.renderCart();
            document.getElementById('sale-scan').value = '';
        }
    },

    renderCart() {
        const container = document.getElementById('cart-items');
        if (!container) return;
        
        container.innerHTML = '';
        let total = 0;
        
        this.state.cart.forEach((item, idx) => {
            const subtotal = (item.price || item.precio || 0) * (item.quantity || item.cantidad || 1);
            total += subtotal;
            const div = document.createElement('div');
            div.style.cssText = 'display:flex; justify-content:space-between; margin-bottom:8px; padding:8px; background:var(--background); border-radius:8px; font-size:0.9rem;';
            div.innerHTML = `
                <span>${item.name || item.nombre} x ${item.quantity || item.cantidad || 1}</span>
                <span>$${subtotal.toFixed(2)} <button onclick="app.removeFromCart(${idx})" style="border:none; background:none; cursor:pointer; color:var(--error)">🗑️</button></span>
            `;
            container.appendChild(div);
        });
        
        const totalEl = document.getElementById('cart-total');
        if (totalEl) totalEl.innerText = `$${total.toFixed(2)}`;
    },

    removeFromCart(idx) {
        this.state.cart.splice(idx, 1);
        this.renderCart();
    },

    openCheckout() {
        if (this.state.cart.length === 0) return alert("Carrito vacío");
        this.showModal('modal-checkout');
    },

    async confirmSale() {
        const items = this.state.cart.map(item => ({
            code: item.code || item.codigo,
            quantity: item.quantity || item.cantidad || 1
        }));
        
        const res = await this.apiCall('sales.confirm', { items });
        if (res.status === 'success') {
            alert('Venta registrada exitosamente');
            this.state.cart = [];
            this.renderCart();
            this.closeModal('modal-checkout');
        } else {
            alert(res.message);
        }
    },

    // --- IMPORT MANAGEMENT ---

    async handleFileUpload(input) {
        if (!input.files.length) return;
        
        const file = input.files[0];
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                headers: {
                    'Authorization': this.state.token
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
    },

    async runImportPreview() {
        alert('Función de importación en desarrollo');
    },

    async commitImport() {
        alert('Función de importación en desarrollo');
    },

    // --- SUBSCRIPTION MANAGEMENT ---

    async loadSubscription() {
        // Cargar datos de suscripción
        const container = document.getElementById('current-plan');
        if (container && this.state.user) {
            container.innerHTML = `
                <strong>Plan Actual:</strong> ${this.state.user.plan || 'FREE'}<br>
                <strong>Créditos:</strong> ${this.state.user.credits || 0}<br>
                <strong>Tenant ID:</strong> ${this.state.user.tenant_id || '-'}
            `;
        }
    },

    async updatePlan(plan, credits) {
        const res = await this.apiCall('sys.subscription.update', { 
            tenant_id: this.state.user.tenant_id, 
            plan: plan, 
            credits: credits 
        });
        if (res.status === 'success') {
            alert(`¡Plan actualizado a ${plan} exitosamente!`);
            await this.loadSubscription();
        } else {
            alert(res.message);
        }
    },

    // --- ALIAS MANAGEMENT ---

    async addAlias() {
        const name = document.getElementById('alias-name')?.value;
        const limit = parseFloat(document.getElementById('alias-limit')?.value || 0);
        
        if (!name) {
            alert('Ingrese nombre del alias');
            return;
        }

        const res = await this.apiCall('alias.add', { name, limit });
        if (res.status === 'success') {
            alert('Alias agregado');
            document.getElementById('alias-name').value = '';
            document.getElementById('alias-limit').value = '';
        } else {
            alert(res.message);
        }
    },

    async deleteAlias(aliasId) {
        if (confirm('¿Eliminar este alias?')) {
            const res = await this.apiCall('alias.delete', { alias_id: aliasId });
            if (res.status === 'success') {
                alert('Alias eliminado');
            }
        }
    },

    // --- CASH MANAGEMENT ---

    async openCash() {
        const amount = parseFloat(document.getElementById('cash-amount')?.value || 0);
        const res = await this.apiCall('cash.open', { amount });
        if (res.status === 'success') {
            alert('Caja abierta');
        } else {
            alert(res.message);
        }
    },

    async closeCash() {
        const amount = parseFloat(document.getElementById('cash-amount')?.value || 0);
        const res = await this.apiCall('cash.close', { amount });
        if (res.status === 'success') {
            alert('Caja cerrada');
        } else {
            alert(res.message);
        }
    },

    // --- EXPORT ---

    async exportCSV() {
        const res = await this.apiCall('stock.export_csv', {});
        if (res.status === 'success') {
            alert('Exportación completada');
        } else {
            alert(res.message);
        }
    },

    // --- SENTINEL / ADMIN ---

    async updateSentinel() {
        alert('Función de sentinel en desarrollo');
    },

    async rollbackSentinel() {
        alert('Función de rollback en desarrollo');
    },

    async selectMasterTarget() {
        alert('Función de master en desarrollo');
    },

    async masterUpdateSubscription() {
        alert('Función de master en desarrollo');
    }
};

// Inicializar app cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

