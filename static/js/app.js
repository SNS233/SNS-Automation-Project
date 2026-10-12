/**
 * MASTER BOREWELL & TUBEWELL MANAGEMENT PORTAL
 * Core Frontend Application Script
 */

/* =========================================================================
<<<<<<< HEAD
   PERMANENT LIGHT THEME ENFORCEMENT
   ========================================================================= */
const ThemeManager = {
    init() {
        try { localStorage.removeItem('app_theme'); } catch (e) {}
        document.documentElement.setAttribute('data-theme', 'light');
        if (document.body) {
            document.body.setAttribute('data-theme', 'light');
        }
    },
    setTheme() {},
    toggleTheme() {},
    applyTheme() {},
    updateControls() {}
=======
   THEME MANAGER (LIGHT / DARK MODE ENGINE)
   ========================================================================= */
const ThemeManager = {
    init() {
        const saved = localStorage.getItem('app_theme') || 'light';
        this.applyTheme(saved, false);
        this.updateControls();
    },

    setTheme(theme) {
        if (theme !== 'light' && theme !== 'dark') theme = 'light';
        localStorage.setItem('app_theme', theme);
        this.applyTheme(theme, true);
    },

    toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        this.setTheme(next);
    },

    applyTheme(theme, notify = false) {
        document.documentElement.setAttribute('data-theme', theme);
        if (document.body) {
            document.body.setAttribute('data-theme', theme);
        }

        // Update header toggle icons & labels
        const adminIcon = document.getElementById('headerThemeIcon');
        const userIcon = document.getElementById('userHeaderThemeIcon');
        const iconName = theme === 'dark' ? 'sun' : 'moon';
        
        [adminIcon, userIcon].forEach(el => {
            if (el) {
                el.setAttribute('data-lucide', iconName);
                el.style.color = theme === 'dark' ? '#f59e0b' : '#64748b';
            }
        });

        const headerText = document.getElementById('headerThemeText');
        if (headerText) {
            headerText.textContent = theme === 'dark' ? 'Light' : 'Dark';
        }

        this.updateControls();

        if (window.lucide) {
            lucide.createIcons();
        }

        if (window.App && App.charts && App.charts.statusChart && typeof DashboardManager !== 'undefined' && DashboardManager.load) {
            DashboardManager.load();
        }

        if (notify && window.App && App.toast) {
            App.toast(`Appearance switched to ${theme === 'dark' ? 'Dark Mode' : 'Light Mode'}`, 'info');
        }
    },

    updateControls() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        
        const radioLight = document.getElementById('themeRadioLight');
        const radioDark = document.getElementById('themeRadioDark');
        const cardLight = document.getElementById('themeCardLight');
        const cardDark = document.getElementById('themeCardDark');
        const badge = document.getElementById('currentThemeBadge');

        if (radioLight) radioLight.checked = (current === 'light');
        if (radioDark) radioDark.checked = (current === 'dark');

        if (cardLight) cardLight.classList.toggle('active', current === 'light');
        if (cardDark) cardDark.classList.toggle('active', current === 'dark');

        if (badge) {
            badge.textContent = current === 'dark' ? 'Dark Mode' : 'Light Mode';
            badge.style.background = current === 'dark' ? 'rgba(59, 130, 246, 0.2)' : 'var(--primary-light)';
            badge.style.color = current === 'dark' ? '#93c5fd' : 'var(--primary)';
        }
    }
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
};

window.ThemeManager = ThemeManager;

const App = {
    currentView: 'dashboard',
    charts: {},
    mapInstances: {},

    init() {
        lucide.createIcons();
        ThemeManager.init();
        this.bindNavigation();
        this.bindGlobalEvents();
        const role = document.body.getAttribute('data-user-role') || 'admin';
        if (role === 'user') {
            this.navigate('user-dashboard');
            UserWorkManager.init();
        } else {
            this.navigate('dashboard');
            AdminNotificationManager.init();
        }
        ReactiveSyncManager.init();
        this.checkSqlHealth();
    },

    bindNavigation() {
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetView = btn.getAttribute('data-view');
                if (targetView) this.navigate(targetView);
            });
        });

        // Mobile menu toggle
        const menuBtn = document.getElementById('mobileMenuBtn');
        const sidebar = document.getElementById('sidebar');
        if (menuBtn && sidebar) {
            menuBtn.addEventListener('click', () => {
                sidebar.classList.toggle('open');
            });
        }

        // Top Resume button
        const resumeBtn = document.getElementById('topResumeBtn');
        if (resumeBtn) {
            resumeBtn.addEventListener('click', () => this.navigate('processing'));
        }

        // Logout button
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async () => {
                try {
                    await fetch('/api/auth/logout', { method: 'POST' });
                    window.location.href = '/login';
                } catch (e) {
                    window.location.href = '/login';
                }
            });
        }
    },

    bindGlobalEvents() {
        // Close modal on backdrop click
        document.querySelectorAll('.modal-backdrop').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.closeModal(modal.id);
            });
        });
    },

    navigate(viewName) {
        // Update nav styling
        document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
            if (btn.getAttribute('data-view') === viewName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });

        // Hide all views
        document.querySelectorAll('.app-view').forEach(view => {
            view.style.display = 'none';
        });

        // Show selected view
        const targetSection = document.getElementById(`view-${viewName}`);
        if (targetSection) {
            targetSection.style.display = 'block';
        }

        // Update header title
        const titles = {
            dashboard: 'Dashboard Overview',
            import: 'Import Villages (Excel / CSV)',
            'assign-person': 'Assign Person & Village Allocation',
            'user-settings': 'User Settings & Access Management',
            villages: 'All Villages Management',
            processing: 'Village Processing Queue',
            automation: 'AUTO FINDING AI Automation',
            export: 'Export Excel',
            history: 'Import Batch History',
            settings: 'System Settings & Diagnostics',
            'user-dashboard': 'Surveyor Dashboard',
<<<<<<< HEAD
            'user-excel-files': 'Excel Files — Assigned Villages',
            'user-history': 'History'
=======
            'user-excel-files': 'Excel Files — Assigned Villages'
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        };
        const titleEl = document.getElementById('pageTitle');
        if (titleEl) titleEl.textContent = titles[viewName] || 'Portal';

        this.currentView = viewName;
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Load data for specific view
        if (viewName === 'dashboard') DashboardManager.load();
<<<<<<< HEAD
        else if (viewName === 'import') ImportManager.loadBatches();
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        else if (viewName === 'assign-person') PersonManager.load();
        else if (viewName === 'user-settings') UserSettingsManager.load();
        else if (viewName === 'villages') VillagesManager.load();
        else if (viewName === 'processing') QueueManager.load();
        else if (viewName === 'automation') AutomationManager.load();
        else if (viewName === 'history') HistoryManager.load();
        else if (viewName === 'settings') {
            SettingsManager.load();
            ThemeManager.updateControls();
        }
        else if (viewName === 'export') ExportManager.init();
<<<<<<< HEAD
        else if (viewName === 'user-dashboard') {
            UserWorkManager.loadDashboard();
            UserWorkManager.loadHistory();
        }
        else if (viewName === 'user-excel-files') UserWorkManager.loadAssignedVillages();
        else if (viewName === 'user-history') UserWorkManager.loadHistory();
=======
        else if (viewName === 'user-dashboard') UserWorkManager.loadDashboard();
        else if (viewName === 'user-excel-files') UserWorkManager.loadAssignedVillages();
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

        // Re-render icons
        setTimeout(() => lucide.createIcons(), 50);
    },

    toast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        
        let iconName = 'info';
        if (type === 'success') iconName = 'check-circle-2';
        if (type === 'error') iconName = 'alert-circle';
        if (type === 'warning') iconName = 'alert-triangle';

        toast.innerHTML = `
            <i data-lucide="${iconName}" style="width: 20px; height: 20px; flex-shrink: 0;"></i>
            <span style="font-size: 0.86rem; color: #1e293b;">${message}</span>
        `;
        container.appendChild(toast);
        lucide.createIcons();

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.25s ease';
            setTimeout(() => toast.remove(), 250);
        }, 4000);
    },

    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'flex';
            setTimeout(() => lucide.createIcons(), 50);
        }
    },

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.style.display = 'none';
    },

    promptDeleteVillage(id, name, code) {
        const idInput = document.getElementById('deleteVillageId');
        const nameEl = document.getElementById('deleteVillageName');
        const codeEl = document.getElementById('deleteVillageCode');
        const btn = document.getElementById('confirmDeleteVillageBtn');

        if (idInput) idInput.value = id;
        if (nameEl) nameEl.textContent = name || '-';
        if (codeEl) codeEl.textContent = code || '-';
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="trash-2" style="width: 15px; height: 15px;"></i><span>Remove Village</span>';
        }
        this.openModal('deleteVillageModal');
        if (window.lucide) lucide.createIcons();
    },

    async executeVillageDelete() {
        const id = document.getElementById('deleteVillageId')?.value;
        if (!id) return;

        const btn = document.getElementById('confirmDeleteVillageBtn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span>Removing...</span>';
        }

        try {
            const resp = await fetch(`/api/villages/${id}`, { method: 'DELETE' });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error || 'Failed to remove village');

            this.closeModal('deleteVillageModal');
            this.toast(data.message || 'Village removed successfully.', 'success');

            const numId = parseInt(id);

            // Clean up selections across both modules
            if (window.PersonManager) {
                PersonManager.selectedUnassignedIds.delete(numId);
                PersonManager.selectedAssignedIds.delete(numId);
                PersonManager.updateUnassignedSelectedBadge();
                PersonManager.updateAssignedSelectedBadge();
            }
            if (window.VillagesManager) {
                VillagesManager.selectedIds.delete(numId);
                VillagesManager.updateBulkActionBar();
            }

            // Immediately update Dashboard KPIs
            if (window.DashboardManager && typeof DashboardManager.load === 'function') {
                DashboardManager.load();
            }

            // Immediately update Person Manager (KPIs, roster counts, and tables)
            if (window.PersonManager && typeof PersonManager.load === 'function') {
                PersonManager.load();
            }

            // Immediately update All Villages list
            if (window.VillagesManager && typeof VillagesManager.load === 'function') {
                VillagesManager.load();
            }
        } catch (err) {
            this.toast(`Remove error: ${err.message}`, 'error');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="trash-2" style="width: 15px; height: 15px;"></i><span>Remove Village</span>';
                if (window.lucide) lucide.createIcons();
            }
        }
    },

    async checkSqlHealth() {
        try {
            const resp = await fetch('/api/settings');
            const data = await resp.json();
            const badge = document.getElementById('sqlStatusBadge');
            if (badge) {
                badge.style.display = 'none';
            }
        } catch (e) {
            console.warn('System status check notice:', e);
        }
    }
};
<<<<<<< HEAD
window.App = App;
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

/* =========================================================================
   1. DASHBOARD MANAGER (STREAMLINED FOR LARGE DATASETS)
   ========================================================================= */
const DashboardManager = {
    zoneInsights: [],
    currentZoneSort: { column: 'total_villages', dir: 'desc' },
<<<<<<< HEAD

    async load() {
        try {
            const resp = await fetch('/api/dashboard/metrics');
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            // 1. Four Main Top KPI Cards
=======
    activeZone: '',

    async filterByZone(zone) {
        this.activeZone = zone || '';
        await this.load();
    },

    async load() {
        try {
            const url = this.activeZone ? `/api/dashboard/metrics?zone=${encodeURIComponent(this.activeZone)}` : '/api/dashboard/metrics';
            const resp = await fetch(url);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            const m = data.data.summary || {};
            if (document.getElementById('statTotalVillages')) {
                document.getElementById('statTotalVillages').textContent = (m.total_villages || 0).toLocaleString();
            }
            if (document.getElementById('statPendingVillages')) {
                document.getElementById('statPendingVillages').textContent = (m.pending_villages || 0).toLocaleString();
            }
            if (document.getElementById('statAssignedVillages')) {
                document.getElementById('statAssignedVillages').textContent = (m.assigned_villages || 0).toLocaleString();
            }
            if (document.getElementById('statCompleted')) {
                document.getElementById('statCompleted').textContent = (m.completed_villages || 0).toLocaleString();
            }

<<<<<<< HEAD
            // Overall Progress Bar
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            const pct = m.progress_percentage || 0;
            if (document.getElementById('progressText')) {
                document.getElementById('progressText').textContent = `${pct}%`;
            }
            if (document.getElementById('progressBar')) {
                document.getElementById('progressBar').style.width = `${Math.min(pct, 100)}%`;
            }

<<<<<<< HEAD
            // 2. Total Remaining Villages KPI Card
            if (document.getElementById('statTotalRemaining')) {
                document.getElementById('statTotalRemaining').textContent = (data.data.total_remaining_villages || 0).toLocaleString();
            }

            // 3. Exactly Four Zone Cards: GPIC, KPIC, VPIC, RPIC
            const fourMap = data.data.four_zones_map || {};

            // GPIC
            const gpic = fourMap['GPIC'] || {};
            if (document.getElementById('gpicTotal')) document.getElementById('gpicTotal').textContent = (gpic.total_villages || 0).toLocaleString();
            if (document.getElementById('gpicPending')) document.getElementById('gpicPending').textContent = (gpic.pending_villages || 0).toLocaleString();
            if (document.getElementById('gpicAssigned')) document.getElementById('gpicAssigned').textContent = (gpic.assigned_villages || 0).toLocaleString();
            if (document.getElementById('gpicCompleted')) document.getElementById('gpicCompleted').textContent = (gpic.completed_villages || 0).toLocaleString();
            const gpicPct = gpic.completion_percentage || 0;
            if (document.getElementById('gpicProgress')) document.getElementById('gpicProgress').textContent = `${gpicPct}%`;
            if (document.getElementById('gpicProgressBar')) document.getElementById('gpicProgressBar').style.width = `${Math.min(gpicPct, 100)}%`;

            // KPIC
            const kpic = fourMap['KPIC'] || {};
            if (document.getElementById('kpicTotal')) document.getElementById('kpicTotal').textContent = (kpic.total_villages || 0).toLocaleString();
            if (document.getElementById('kpicPending')) document.getElementById('kpicPending').textContent = (kpic.pending_villages || 0).toLocaleString();
            if (document.getElementById('kpicAssigned')) document.getElementById('kpicAssigned').textContent = (kpic.assigned_villages || 0).toLocaleString();
            if (document.getElementById('kpicCompleted')) document.getElementById('kpicCompleted').textContent = (kpic.completed_villages || 0).toLocaleString();
            const kpicPct = kpic.completion_percentage || 0;
            if (document.getElementById('kpicProgress')) document.getElementById('kpicProgress').textContent = `${kpicPct}%`;
            if (document.getElementById('kpicProgressBar')) document.getElementById('kpicProgressBar').style.width = `${Math.min(kpicPct, 100)}%`;

            // VPIC
            const vpic = fourMap['VPIC'] || {};
            if (document.getElementById('vpicTotal')) document.getElementById('vpicTotal').textContent = (vpic.total_villages || 0).toLocaleString();
            if (document.getElementById('vpicPending')) document.getElementById('vpicPending').textContent = (vpic.pending_villages || 0).toLocaleString();
            if (document.getElementById('vpicAssigned')) document.getElementById('vpicAssigned').textContent = (vpic.assigned_villages || 0).toLocaleString();
            if (document.getElementById('vpicCompleted')) document.getElementById('vpicCompleted').textContent = (vpic.completed_villages || 0).toLocaleString();
            const vpicPct = vpic.completion_percentage || 0;
            if (document.getElementById('vpicProgress')) document.getElementById('vpicProgress').textContent = `${vpicPct}%`;
            if (document.getElementById('vpicProgressBar')) document.getElementById('vpicProgressBar').style.width = `${Math.min(vpicPct, 100)}%`;

            // RPIC
            const rpic = fourMap['RPIC'] || {};
            if (document.getElementById('rpicTotal')) document.getElementById('rpicTotal').textContent = (rpic.total_villages || 0).toLocaleString();
            if (document.getElementById('rpicPending')) document.getElementById('rpicPending').textContent = (rpic.pending_villages || 0).toLocaleString();
            if (document.getElementById('rpicAssigned')) document.getElementById('rpicAssigned').textContent = (rpic.assigned_villages || 0).toLocaleString();
            if (document.getElementById('rpicCompleted')) document.getElementById('rpicCompleted').textContent = (rpic.completed_villages || 0).toLocaleString();
            const rpicPct = rpic.completion_percentage || 0;
            if (document.getElementById('rpicProgress')) document.getElementById('rpicProgress').textContent = `${rpicPct}%`;
            if (document.getElementById('rpicProgressBar')) document.getElementById('rpicProgressBar').style.width = `${Math.min(rpicPct, 100)}%`;

            // Unrecognized / Other Zones Notice
            const otherAlert = document.getElementById('otherZoneAlertBox');
            const other = data.data.other_zones || {};
            if (otherAlert) {
                if (other.total_villages > 0) {
                    otherAlert.style.display = 'block';
                    if (document.getElementById('otherZoneCount')) document.getElementById('otherZoneCount').textContent = (other.total_villages || 0).toLocaleString();
                    if (document.getElementById('otherZonePending')) document.getElementById('otherZonePending').textContent = (other.pending_villages || 0).toLocaleString();
                    if (document.getElementById('otherZoneCompleted')) document.getElementById('otherZoneCompleted').textContent = (other.completed_villages || 0).toLocaleString();
                } else {
                    otherAlert.style.display = 'none';
                }
            }

            await this.loadCompletedVillages();
=======
            // Render 4 Zone Overview KPI cards
            const zk = data.data.zone_kpis || {};
            if (document.getElementById('zoneKpiTotalZones')) {
                document.getElementById('zoneKpiTotalZones').textContent = (zk.total_zones || 0).toLocaleString();
            }
            if (document.getElementById('zoneKpiCompletedZones')) {
                document.getElementById('zoneKpiCompletedZones').textContent = (zk.completed_zones || 0).toLocaleString();
            }
            if (document.getElementById('zoneKpiInProgressZones')) {
                document.getElementById('zoneKpiInProgressZones').textContent = (zk.in_progress_zones || 0).toLocaleString();
            }
            if (document.getElementById('zoneKpiPendingZones')) {
                document.getElementById('zoneKpiPendingZones').textContent = (zk.pending_zones || 0).toLocaleString();
            }

            // Populate / sync Dashboard Zone Filter Select options
            const zoneSelect = document.getElementById('dashboardZoneSelect');
            if (zoneSelect && data.data.filter_options && data.data.filter_options.zones) {
                const currentVal = this.activeZone;
                const zones = data.data.filter_options.zones || [];
                const targetCount = zones.length + 1;
                if (zoneSelect.children.length !== targetCount) {
                    let html = '<option value="">All Zones (Overall)</option>';
                    zones.forEach(z => {
                        html += `<option value="${escapeQuotes(z)}" ${z === currentVal ? 'selected' : ''}>Zone: ${z}</option>`;
                    });
                    zoneSelect.innerHTML = html;
                }
                zoneSelect.value = currentVal;
            }

            // Render live Done vs Pending Pie Chart (scoped to active zone or overall)
            this.renderPieChart(m.completed_villages || 0, m.pending_villages || 0);

            // Update zone count badge
            const badge = document.getElementById('zoneCountBadge');
            if (badge && data.data.zone_insights) {
                badge.textContent = `${data.data.zone_insights.length} Zones`;
            }

>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            lucide.createIcons();
        } catch (e) {
            console.error('Error loading dashboard:', e);
            App.toast('Failed to load dashboard metrics.', 'error');
        }
    },

<<<<<<< HEAD
    viewDetail(statusType) {
        App.navigate('villages');
        if (window.VillagesManager && VillagesManager.openWithFilters) {
            VillagesManager.openWithFilters({ zone: '', status: statusType || 'all' });
        }
    },

    viewZoneDetail(zoneName) {
        App.navigate('villages');
        if (window.VillagesManager && VillagesManager.openWithFilters) {
            VillagesManager.openWithFilters({ zone: zoneName, status: 'all' });
        }
    },

=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    renderZoneInsights(zones) {
        const tbody = document.getElementById('zoneInsightsTableBody');
        const tfoot = document.getElementById('zoneInsightsTableFoot');
        const badge = document.getElementById('zoneCountBadge');
        if (!tbody) return;

        if (badge) badge.textContent = `${zones.length} Zones`;

        if (!zones || zones.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; color: #94a3b8; padding: 24px;">No zone records found.</td></tr>';
            if (tfoot) tfoot.innerHTML = '';
            return;
        }

        // Render zone rows
        tbody.innerHTML = zones.map(z => {
            const compPct = z.completion_percentage || 0;
            const remPct = z.remaining_percentage || 0;
            const inProg = z.in_progress_villages || 0;
            const isFinished = compPct === 100 && z.total_villages > 0;
            const barGradient = isFinished 
                ? 'linear-gradient(90deg, #10b981, #059669)' 
                : 'linear-gradient(90deg, #2563eb, #3b82f6)';

            return `
                <tr>
                    <td>
                        <strong style="color: var(--text-primary); cursor: pointer;" onclick="DashboardManager.viewZoneVillages('${escapeQuotes(z.zone_name)}')" title="Filter villages by ${z.zone_name}">${z.zone_name}</strong>
                    </td>
                    <td style="text-align: right; font-weight: 600;">
                        ${(z.total_villages || 0).toLocaleString()}
                    </td>
                    <td style="text-align: right;">
                        <span class="badge" style="background: rgba(16, 185, 129, 0.1); color: #059669; font-weight: 700; border: 1px solid rgba(16, 185, 129, 0.25);">
                            ${(z.completed_villages || 0).toLocaleString()}
                        </span>
                    </td>
                    <td style="text-align: right;">
                        <span class="badge" style="background: rgba(245, 158, 11, 0.1); color: #d97706; font-weight: 700; border: 1px solid rgba(245, 158, 11, 0.25);">
                            ${(z.pending_villages || 0).toLocaleString()}
                        </span>
                    </td>
                    <td style="text-align: right;">
                        <span class="badge" style="background: rgba(99, 102, 241, 0.1); color: #4f46e5; font-weight: 600;">
                            ${inProg.toLocaleString()}
                        </span>
                    </td>
                    <td style="text-align: right; font-weight: 700; color: #059669;">
                        ${compPct}%
                    </td>
                    <td style="text-align: right; color: #64748b;">
                        ${remPct}%
                    </td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="flex: 1; height: 8px; background: #e2e8f0; border-radius: 9999px; overflow: hidden;">
                                <div style="width: ${Math.min(compPct, 100)}%; height: 100%; background: ${barGradient}; border-radius: 9999px; transition: width 0.3s ease;"></div>
                            </div>
                            <span style="font-size: 0.74rem; font-weight: 600; color: #64748b; width: 34px; text-align: right;">${compPct}%</span>
                        </div>
                    </td>
                    <td style="text-align: right;">
                        <button class="btn btn-secondary btn-xs" onclick="DashboardManager.viewZoneVillages('${escapeQuotes(z.zone_name)}')" title="View villages in this zone" style="padding: 3px 8px; font-size: 0.76rem; display: inline-flex; align-items: center; gap: 4px;">
                            <i data-lucide="eye" style="width: 12px; height: 12px;"></i> View
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        // Compute overall totals across all zones
        const totAll = zones.reduce((acc, z) => acc + (z.total_villages || 0), 0);
        const compAll = zones.reduce((acc, z) => acc + (z.completed_villages || 0), 0);
        const pendAll = zones.reduce((acc, z) => acc + (z.pending_villages || 0), 0);
        const inProgAll = zones.reduce((acc, z) => acc + (z.in_progress_villages || 0), 0);
        const compPctAll = totAll > 0 ? ((compAll / totAll) * 100).toFixed(1) : '0.0';
        const remPctAll = totAll > 0 ? Math.max(0, 100 - parseFloat(compPctAll)).toFixed(1) : '0.0';

        if (tfoot) {
            tfoot.innerHTML = `
                <tr>
                    <td style="color: var(--text-primary); font-weight: 700;">Overall Total (All Zones)</td>
                    <td style="text-align: right; font-weight: 700; color: var(--text-primary);">${totAll.toLocaleString()}</td>
                    <td style="text-align: right; font-weight: 700; color: #059669;">${compAll.toLocaleString()}</td>
                    <td style="text-align: right; font-weight: 700; color: #d97706;">${pendAll.toLocaleString()}</td>
                    <td style="text-align: right; font-weight: 700; color: #4f46e5;">${inProgAll.toLocaleString()}</td>
                    <td style="text-align: right; font-weight: 700; color: #059669;">${compPctAll}%</td>
                    <td style="text-align: right; font-weight: 700; color: #64748b;">${remPctAll}%</td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div style="flex: 1; height: 8px; background: #cbd5e1; border-radius: 9999px; overflow: hidden;">
                                <div style="width: ${Math.min(parseFloat(compPctAll), 100)}%; height: 100%; background: linear-gradient(90deg, #2563eb, #10b981); border-radius: 9999px;"></div>
                            </div>
                            <span style="font-size: 0.74rem; font-weight: 700; color: var(--text-primary); width: 34px; text-align: right;">${compPctAll}%</span>
                        </div>
                    </td>
                    <td style="text-align: right;">
                        <button class="btn btn-primary btn-xs" onclick="App.navigate('villages')" style="padding: 3px 8px; font-size: 0.76rem;">All</button>
                    </td>
                </tr>
            `;
        }

        lucide.createIcons();
    },

    sortZones(column) {
        if (!this.zoneInsights || !this.zoneInsights.length) return;

        if (this.currentZoneSort.column === column) {
            this.currentZoneSort.dir = this.currentZoneSort.dir === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentZoneSort.column = column;
            this.currentZoneSort.dir = (column === 'zone_name') ? 'asc' : 'desc';
        }

        const dir = this.currentZoneSort.dir;
        this.zoneInsights.sort((a, b) => {
            let valA = a[column];
            let valB = b[column];

            if (typeof valA === 'string') {
                return dir === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
            }
            valA = valA || 0;
            valB = valB || 0;
            return dir === 'asc' ? (valA - valB) : (valB - valA);
        });

        this.renderZoneInsights(this.zoneInsights);
    },

    viewZoneVillages(zoneName) {
        App.navigate('villages');
        const filterZone = document.getElementById('filterZone');
        if (filterZone) {
            filterZone.value = (zoneName === 'Unassigned Zone') ? '' : zoneName;
        }
        if (typeof VillagesManager !== 'undefined' && VillagesManager.load) {
            VillagesManager.page = 1;
            VillagesManager.load();
        }
    },

    renderPieChart(doneCount, pendingCount) {
        const canvas = document.getElementById('statusChart');
        if (!canvas) return;

        const total = doneCount + pendingCount;
        const donePct = total > 0 ? ((doneCount / total) * 100).toFixed(1) : '0.0';
        const pendingPct = total > 0 ? ((pendingCount / total) * 100).toFixed(1) : '0.0';

        if (document.getElementById('chartDoneCount')) {
            document.getElementById('chartDoneCount').textContent = doneCount.toLocaleString();
        }
        if (document.getElementById('chartDonePct')) {
            document.getElementById('chartDonePct').textContent = `(${donePct}%)`;
        }
        if (document.getElementById('chartPendingCount')) {
            document.getElementById('chartPendingCount').textContent = pendingCount.toLocaleString();
        }
        if (document.getElementById('chartPendingPct')) {
            document.getElementById('chartPendingPct').textContent = `(${pendingPct}%)`;
        }
        if (document.getElementById('chartTotalCount')) {
            document.getElementById('chartTotalCount').textContent = total.toLocaleString();
        }

        // Destroy existing chart instance to prevent duplicates/glitches
        if (App.charts.statusChart) {
            App.charts.statusChart.destroy();
            App.charts.statusChart = null;
        }

<<<<<<< HEAD
        const textColor = '#0f172a';
        const borderColor = '#ffffff';
=======
        const isDark = document.body.classList.contains('dark-theme');
        const textColor = isDark ? '#f1f5f9' : '#0f172a';
        const borderColor = isDark ? '#1e293b' : '#ffffff';
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

        const ctx = canvas.getContext('2d');
        App.charts.statusChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Done / Completed', 'Not Done / Pending'],
                datasets: [{
                    data: [doneCount, pendingCount],
                    backgroundColor: ['#10b981', '#f59e0b'],
                    borderColor: borderColor,
                    borderWidth: 2,
                    hoverOffset: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: textColor,
                            font: { family: 'inherit', size: 12, weight: '500' },
                            padding: 14,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const val = context.raw || 0;
                                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                                return ` ${context.label}: ${val.toLocaleString()} (${pct}%)`;
                            }
                        }
                    }
                }
            }
        });
    },

    renderRecentVillages(villages) {
        const tbody = document.getElementById('recentVillagesTable');
        if (!tbody) return;
        if (!villages || villages.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #94a3b8; padding: 24px;">No villages processed yet.</td></tr>';
            return;
        }

        tbody.innerHTML = villages.map(v => `
            <tr>
                <td><strong>${v.village_name}</strong></td>
                <td><code>${v.village_code}</code></td>
                <td>${v.district_name}</td>
                <td><span class="badge ${getStatusBadgeClass(v.kml_status)}">${v.kml_status}</span></td>
                <td><strong>${v.total_wells || 0}</strong> <span style="font-size:0.75rem; color:#64748b;">(B:${v.bores||0} / D:${v.dugwells||0})</span></td>
                <td style="text-align: right;">
                    <button class="btn btn-secondary btn-sm" onclick="QueueManager.openVillage(${v.id})" title="Open Details">
                        <i data-lucide="play" style="width:14px; height:14px;"></i> Open
                    </button>
                </td>
            </tr>
        `).join('');
        lucide.createIcons();
<<<<<<< HEAD
    },

    async loadCompletedVillages() {
        const tbody = document.getElementById('dashboardCompletedVillagesTableBody');
        const badge = document.getElementById('dashboardCompletedCountBadge');
        if (!tbody) return;

        try {
            const resp = await fetch('/api/dashboard/completed-villages');
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            const items = data.items || [];
            if (badge) {
                badge.textContent = `${items.length.toLocaleString()} Completed`;
            }

            if (items.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="8" style="text-align: center; color: #64748b; padding: 36px 20px;">
                            <i data-lucide="check-circle" style="width: 36px; height: 36px; color: #94a3b8; margin-bottom: 8px; display: inline-block;"></i>
                            <div style="font-weight: 600; font-size: 0.95rem; color: #1e293b; margin-bottom: 4px;">No Completed Villages Yet</div>
                            <div style="font-size: 0.82rem; color: #94a3b8;">When field surveyors complete well markings and save villages, their genuine review links will appear here.</div>
                        </td>
                    </tr>
                `;
                lucide.createIcons();
                return;
            }

            tbody.innerHTML = items.map((v, idx) => {
                const villageName = escapeQuotes(v.village_name || '');
                const villageCode = escapeQuotes(v.village_code || '');
                const assignedPerson = escapeQuotes(v.assigned_person_name || 'Unassigned');
                const completionDate = v.completion_date || '-';
                const hasUrl = Boolean(v.generated_review_url && String(v.generated_review_url).trim().startsWith('http'));

                const viewWorkBtn = `<button class="btn btn-sm btn-primary" onclick="VillagesManager.openVillageWork(${v.id}, '${escapeQuotes(v.generated_review_url || '')}', this)" style="padding: 5px 12px; font-size: 0.82rem; font-weight: 600; display: inline-flex; align-items: center; gap: 5px;" title="Open saved work on Village Wells marking portal">
                    <i data-lucide="external-link" style="width: 14px; height: 14px;"></i> <span>View Work</span>
                </button>`;

                const reopenBtn = `<button class="btn btn-secondary btn-sm" style="color: #d97706; border-color: #fde68a; padding: 5px 10px; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 4px;" onclick="VillagesManager.promptReopenVillage(${v.id}, '${villageName}', '${villageCode}', ${v.assigned_person_id || 'null'}, '${assignedPerson}')" title="Reopen &amp; Send for Correction">
                    <i data-lucide="rotate-ccw" style="width: 13px; height: 13px;"></i> <span>Reopen</span>
                </button>`;

                const reassignBtn = `<button class="btn btn-secondary btn-sm" style="color: #4338ca; border-color: #c7d2fe; padding: 5px 9px; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 4px;" onclick="VillagesManager.promptReassignVillage(${v.id}, '${villageName}', '${villageCode}', ${v.assigned_person_id || 'null'}, '${assignedPerson}')" title="Reassign to another surveyor">
                    <i data-lucide="user-plus" style="width: 13px; height: 13px;"></i> <span>Reassign</span>
                </button>`;

                const historyBtn = `<button class="btn btn-secondary btn-sm" style="padding: 5px 8px; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 3px;" onclick="VillagesManager.showAssignmentHistory(${v.id}, '${villageName}', '${villageCode}')" title="View Assignment History">
                    <i data-lucide="history" style="width: 13px; height: 13px;"></i> <span>History</span>
                </button>`;

                return `
                    <tr>
                        <td style="color: #64748b; font-weight: 500;">${idx + 1}</td>
                        <td>
                            <strong style="color: #0f172a; font-size: 0.9rem;">${v.village_name}</strong>
                            <div style="font-size: 0.74rem; color: #64748b;">${v.zone || '-'} &bull; ${v.district_name || '-'}</div>
                        </td>
                        <td>
                            <code style="font-weight: 600; color: #1e293b; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.82rem;">${v.village_code || '-'}</code>
                        </td>
                        <td>
                            <div style="font-weight: 600; color: #1e293b; font-size: 0.86rem; display: flex; align-items: center; gap: 4px;">
                                <i data-lucide="user" style="width: 13px; height: 13px; color: #4f46e5;"></i>
                                <span>${v.assigned_person_name || '<em style="color:#94a3b8; font-weight:400;">Unassigned</em>'}</span>
                            </div>
                        </td>
                        <td>
                            <span style="font-size: 0.84rem; color: #0f172a; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
                                <i data-lucide="calendar" style="width: 13px; height: 13px; color: #059669;"></i>
                                ${completionDate}
                            </span>
                        </td>
                        <td>
                            <div style="font-size: 0.84rem; color: #0f172a; font-weight: 700;">Total: ${v.total_wells || 0} wells</div>
                            <div style="font-size: 0.74rem; color: #64748b;">Dug Wells: <strong>${v.dugwells || 0}</strong> &bull; Borewells: <strong>${v.bores || 0}</strong></div>
                        </td>
                        <td>
                            <span class="badge" style="background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">
                                <i data-lucide="check-circle-2" style="width: 12px; height: 12px;"></i> Completed
                            </span>
                        </td>
                        <td style="text-align: right; white-space: nowrap;">
                            <div style="display: inline-flex; gap: 5px; align-items: center; justify-content: flex-end;">
                                ${viewWorkBtn}
                                ${reopenBtn}
                                ${reassignBtn}
                                ${historyBtn}
                            </div>
                        </td>
                    </tr>
                `;
            }).join('');

            lucide.createIcons();
        } catch (err) {
            console.error('Error loading dashboard completed villages:', err);
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #ef4444; padding: 24px;">Failed to load completed villages: ${err.message}</td></tr>`;
        }
    },

    warnMissingReviewLink(villageName, villageCode) {
        App.toast(`Warning: No genuine review URL recorded in database for village "${villageName}" (${villageCode}). Generating fake URLs is strictly prohibited.`, 'warning');
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    }
};

/* =========================================================================
   2. IMPORT MANAGER (Excel / CSV)
   ========================================================================= */
const ImportManager = {
    selectedFile: null,
    previewData: null,
<<<<<<< HEAD
    batches: [],
    currentBatchId: null,
    currentBatchVillages: [],
    batchVillagesPage: 1,
    batchVillagesTotalPages: 1,
    batchVillagesPageSize: 20,
    correctionFile: null,
    searchDebounceTimer: null,
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

    init() {
        const dropzone = document.getElementById('excelDropzone');
        const fileInput = document.getElementById('excelFileInput');
        const startBtn = document.getElementById('startImportBtn');
        const resetBtn = document.getElementById('resetImportBtn');

        if (dropzone && fileInput) {
            dropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropzone.classList.add('drag-over');
            });
            dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.classList.remove('drag-over');
                if (e.dataTransfer.files.length) {
                    this.handleFile(e.dataTransfer.files[0]);
                }
            });
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length) {
                    this.handleFile(e.target.files[0]);
                }
            });
        }

        if (startBtn) {
            startBtn.addEventListener('click', () => this.executeImport());
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.reset());
        }
<<<<<<< HEAD

        // Batch Review Table search/filters
        const batchSearchInput = document.getElementById('batchVillageSearchInput');
        if (batchSearchInput) {
            batchSearchInput.addEventListener('input', () => {
                clearTimeout(this.searchDebounceTimer);
                this.searchDebounceTimer = setTimeout(() => this.loadBatchVillages(1), 350);
            });
        }

        const batchDistFilter = document.getElementById('batchDistrictFilter');
        if (batchDistFilter) {
            batchDistFilter.addEventListener('input', () => {
                clearTimeout(this.searchDebounceTimer);
                this.searchDebounceTimer = setTimeout(() => this.loadBatchVillages(1), 350);
            });
        }

        const batchTalukaFilter = document.getElementById('batchTalukaFilter');
        if (batchTalukaFilter) {
            batchTalukaFilter.addEventListener('input', () => {
                clearTimeout(this.searchDebounceTimer);
                this.searchDebounceTimer = setTimeout(() => this.loadBatchVillages(1), 350);
            });
        }

        // Batch correction dropzone
        const correctDropzone = document.getElementById('batchCorrectDropzone');
        if (correctDropzone) {
            correctDropzone.addEventListener('dragover', (e) => {
                e.preventDefault();
                correctDropzone.classList.add('drag-over');
            });
            correctDropzone.addEventListener('dragleave', () => correctDropzone.classList.remove('drag-over'));
            correctDropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                correctDropzone.classList.remove('drag-over');
                if (e.dataTransfer.files.length) {
                    this.handleCorrectionFileSelected(e.dataTransfer.files[0]);
                }
            });
        }

        // Load batches if on view-import or initial load
        this.loadBatches();
    },

    async loadBatches() {
        const container = document.getElementById('batchesContainer');
        if (!container) return;

        try {
            const resp = await fetch('/api/import/batches');
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.batches = data.batches || [];
            this.renderBatches(this.batches);
        } catch (e) {
            console.error('Failed to load import batches:', e);
            if (container) {
                container.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 24px; color: #ef4444;">
                        Failed to load imported batches: ${e.message}
                    </div>
                `;
            }
        }
    },

    renderBatches(batches) {
        const container = document.getElementById('batchesContainer');
        if (!container) return;

        if (!batches || batches.length === 0) {
            container.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 36px 16px; background: var(--bg-surface); border: 1px dashed var(--border-color); border-radius: 8px;">
                    <i data-lucide="file-spreadsheet" style="width: 38px; height: 38px; color: var(--text-secondary); margin-bottom: 8px;"></i>
                    <h4 style="font-size: 0.95rem; font-weight: 600; color: var(--text-primary); margin-bottom: 4px;">No Imported Datasets Yet</h4>
                    <p style="font-size: 0.82rem; color: var(--text-secondary); margin: 0;">Upload an Excel or CSV file using the box above to import village datasets.</p>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
            return;
        }

        const formatDt = (dtStr) => {
            if (!dtStr) return 'N/A';
            try {
                const d = new Date(dtStr);
                return d.toLocaleString(undefined, {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch {
                return dtStr;
            }
        };

        container.innerHTML = batches.map(b => {
            const addedCount = b.inserted_rows || b.valid_rows || 0;
            const updatedCount = b.updated_rows || 0;
            const dupsCount = b.duplicate_rows || 0;
            const invalidCount = b.invalid_rows || 0;
            const totalCount = b.total_rows || 0;
            const activeInDb = b.active_villages_count || 0;
            const assignedCount = b.assigned_count || 0;
            const completedCount = b.completed_count || 0;

            return `
            <div class="card batch-card" style="border: 1px solid var(--border-color); border-radius: 10px; padding: 18px; background: var(--bg-card); display: flex; flex-direction: column; justify-content: space-between; box-shadow: 0 2px 6px rgba(0,0,0,0.03); position: relative;">
                <div>
                    <!-- Header -->
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 12px;">
                        <div style="display: flex; align-items: center; gap: 10px; min-width: 0;">
                            <div style="width: 40px; height: 40px; border-radius: 8px; background: rgba(37, 99, 235, 0.1); color: var(--primary); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                                <i data-lucide="file-spreadsheet" style="width: 22px; height: 22px;"></i>
                            </div>
                            <div style="min-width: 0;">
                                <h4 style="font-size: 0.96rem; font-weight: 700; margin: 0; color: var(--text-primary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${b.filename}">
                                    ${b.filename}
                                </h4>
                                <div style="font-size: 0.77rem; color: var(--text-secondary); margin-top: 2px;">
                                    <i data-lucide="clock" style="width: 12px; height: 12px; vertical-align: middle; margin-right: 2px;"></i>
                                    ${formatDt(b.created_at)}
                                </div>
                            </div>
                        </div>
                        <span class="badge ${b.status === 'completed' ? 'badge-success' : 'badge-warning'}" style="font-size: 0.72rem; text-transform: uppercase;">
                            ${b.status || 'Completed'}
                        </span>
                    </div>

                    <!-- Metric Box -->
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 12px; background: var(--bg-surface); padding: 12px; border-radius: 8px; border: 1px solid var(--border-color);">
                        <div>
                            <div style="font-size: 0.72rem; color: var(--text-secondary); font-weight: 600;">Total Villages</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary);">${totalCount.toLocaleString()}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.72rem; color: #166534; font-weight: 600;">Successfully Added</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #166534;">${addedCount.toLocaleString()}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.72rem; color: #2563eb; font-weight: 600;">Updated Existing</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #2563eb;">${updatedCount.toLocaleString()}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.72rem; color: #d97706; font-weight: 600;">Duplicates / Skipped</div>
                            <div style="font-size: 1.15rem; font-weight: 700; color: #d97706;">${dupsCount.toLocaleString()}</div>
                        </div>
                        ${invalidCount > 0 ? `
                        <div style="grid-column: span 2; display: flex; justify-content: space-between; align-items: center; background: #fef2f2; padding: 6px 10px; border-radius: 6px; border: 1px solid #fecaca;">
                            <span style="font-size: 0.78rem; color: #dc2626; font-weight: 600;">Failed Records: ${invalidCount}</span>
                            ${b.error_report_name ? `<a href="/api/import/errors/${b.error_report_name}" class="btn btn-xs btn-outline-danger" style="font-size: 0.72rem; padding: 2px 8px;">Download Errors</a>` : ''}
                        </div>` : ''}
                    </div>

                    <!-- DB Status Badges -->
                    <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; font-size: 0.75rem;">
                        <span style="background: rgba(37, 99, 235, 0.08); color: var(--primary); padding: 3px 8px; border-radius: 4px; font-weight: 600;">
                            Active in DB: ${activeInDb.toLocaleString()}
                        </span>
                        ${assignedCount > 0 ? `<span style="background: rgba(99, 102, 241, 0.1); color: #4f46e5; padding: 3px 8px; border-radius: 4px; font-weight: 600;">Assigned: ${assignedCount.toLocaleString()}</span>` : ''}
                        ${completedCount > 0 ? `<span style="background: rgba(16, 185, 129, 0.1); color: #059669; padding: 3px 8px; border-radius: 4px; font-weight: 600;">Completed: ${completedCount.toLocaleString()}</span>` : ''}
                    </div>
                </div>

                <!-- Actions Footer -->
                <div style="display: flex; gap: 8px; border-top: 1px solid var(--border-color); padding-top: 12px; justify-content: flex-end; align-items: center;">
                    <button type="button" class="btn btn-outline btn-sm" onclick="ImportManager.openReviewModal(${b.id})" title="Review villages in this batch" style="display: flex; align-items: center; gap: 5px; font-size: 0.8rem;">
                        <i data-lucide="list" style="width: 14px; height: 14px;"></i>
                        <span>Review</span>
                    </button>
                    <button type="button" class="btn btn-secondary btn-sm" onclick="ImportManager.openEditModal(${b.id}, 'upload')" title="Upload corrected sheet or update village details" style="display: flex; align-items: center; gap: 5px; font-size: 0.8rem;">
                        <i data-lucide="edit-3" style="width: 14px; height: 14px;"></i>
                        <span>Edit</span>
                    </button>
                    <button type="button" class="btn btn-danger btn-sm" onclick="ImportManager.openDeleteModal(${b.id})" title="Delete this batch dataset" style="display: flex; align-items: center; gap: 5px; font-size: 0.8rem;">
                        <i data-lucide="trash-2" style="width: 14px; height: 14px;"></i>
                        <span>Delete</span>
                    </button>
                </div>
            </div>
            `;
        }).join('');

        if (window.lucide) lucide.createIcons();
    },

    openReviewModal(batchId) {
        this.openEditModal(batchId, 'review');
    },

    openEditModal(batchId, tab = 'upload') {
        const numId = parseInt(batchId, 10);
        let batch = this.batches.find(b => b.id == batchId || b.id == numId);
        if (!batch) {
            batch = { id: batchId, filename: `Dataset #${batchId}`, total_rows: 0, active_villages_count: 0 };
        }

        this.currentBatchId = batch.id;
        this.correctionFile = null;

        const titleEl = document.getElementById('editBatchTitleFileName');
        if (titleEl) titleEl.textContent = batch.filename || `Dataset #${batch.id}`;

        const subEl = document.getElementById('editBatchMetaSubtitle');
        if (subEl) {
            const totalR = batch.total_rows || 0;
            const activeV = batch.active_villages_count !== undefined ? batch.active_villages_count : 0;
            subEl.textContent = `Batch #${batch.id} • Total Rows: ${totalR.toLocaleString()} • Active in DB: ${activeV.toLocaleString()}`;
        }

        // Reset inputs
        const correctInput = document.getElementById('batchCorrectFileInput');
        if (correctInput) correctInput.value = '';
        const infoBox = document.getElementById('batchCorrectFileInfo');
        if (infoBox) infoBox.style.display = 'none';

        this.switchEditTab(tab);
        if (tab === 'review') {
            this.resetBatchFilters();
        }

        App.openModal('editBatchModal');
        if (window.lucide) lucide.createIcons();
    },

    switchEditTab(tabName) {
        const tabReview = document.getElementById('tabContentReview');
        const tabUpload = document.getElementById('tabContentUpload');
        const btnReview = document.getElementById('tabBtnReviewVillages');
        const btnUpload = document.getElementById('tabBtnUploadCorrection');

        if (tabName === 'review') {
            if (tabReview) tabReview.style.display = 'flex';
            if (tabUpload) tabUpload.style.display = 'none';
            if (btnReview) {
                btnReview.className = 'btn btn-sm btn-primary';
            }
            if (btnUpload) {
                btnUpload.className = 'btn btn-sm btn-outline';
            }
        } else {
            if (tabReview) tabReview.style.display = 'none';
            if (tabUpload) tabUpload.style.display = 'block';
            if (btnReview) {
                btnReview.className = 'btn btn-sm btn-outline';
            }
            if (btnUpload) {
                btnUpload.className = 'btn btn-sm btn-primary';
            }
        }
        if (window.lucide) lucide.createIcons();
    },

    resetBatchFilters() {
        const s = document.getElementById('batchVillageSearchInput');
        if (s) s.value = '';
        const d = document.getElementById('batchDistrictFilter');
        if (d) d.value = '';
        const t = document.getElementById('batchTalukaFilter');
        if (t) t.value = '';
        this.loadBatchVillages(1);
    },

    async loadBatchVillages(page = 1) {
        if (!this.currentBatchId) return;

        this.batchVillagesPage = page;
        const tbody = document.getElementById('batchVillagesTableBody');
        if (tbody) {
            tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 24px; color: var(--text-secondary);"><div class="spinner" style="margin: 0 auto 8px auto;"></div>Loading villages...</td></tr>`;
        }

        const search = document.getElementById('batchVillageSearchInput')?.value.trim() || '';
        const district = document.getElementById('batchDistrictFilter')?.value.trim() || '';
        const taluka = document.getElementById('batchTalukaFilter')?.value.trim() || '';

        try {
            const url = `/api/import/batch/${this.currentBatchId}/villages?page=${page}&page_size=${this.batchVillagesPageSize}&search=${encodeURIComponent(search)}&district=${encodeURIComponent(district)}&taluka=${encodeURIComponent(taluka)}`;
            const resp = await fetch(url);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            const result = data.data;
            this.currentBatchVillages = result.items || [];
            this.batchVillagesTotalPages = result.total_pages || 1;

            this.renderBatchVillages(result);
        } catch (e) {
            if (tbody) {
                tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 20px; color: #ef4444;">Failed to load villages: ${e.message}</td></tr>`;
            }
        }
    },

    renderBatchVillages(result) {
        const tbody = document.getElementById('batchVillagesTableBody');
        const countSummary = document.getElementById('batchVillagesCountSummary');
        const paginationInfo = document.getElementById('batchPaginationInfo');
        const prevBtn = document.getElementById('btnBatchPrevPage');
        const nextBtn = document.getElementById('btnBatchNextPage');

        const items = result.items || [];
        const total = result.total_count || 0;
        const page = result.current_page || 1;
        const pageSize = result.page_size || 20;

        const from = total === 0 ? 0 : (page - 1) * pageSize + 1;
        const to = Math.min(page * pageSize, total);

        if (countSummary) {
            countSummary.textContent = `Showing ${from.toLocaleString()} - ${to.toLocaleString()} of ${total.toLocaleString()} villages in this batch`;
        }

        if (paginationInfo) {
            paginationInfo.textContent = `Page ${page} of ${result.total_pages || 1}`;
        }

        if (prevBtn) prevBtn.disabled = (page <= 1);
        if (nextBtn) nextBtn.disabled = (page >= result.total_pages);

        if (items.length === 0) {
            if (tbody) tbody.innerHTML = `<tr><td colspan="10" style="text-align: center; padding: 24px; color: var(--text-secondary);">No villages matched the filter in this batch.</td></tr>`;
            return;
        }

        if (tbody) {
            tbody.innerHTML = items.map(v => {
                const isDone = (v.work_status === 'Done' || ['Done', 'Verified', 'Marking Completed', 'Finalized'].includes(v.kml_status));
                const wellsBreakdown = `${v.electric_kuva || 0} / ${v.electric_bor || 0} / ${v.solar_bor_kuva || 0}`;
                return `
                <tr>
                    <td><code style="font-weight: 600; color: var(--primary);">${v.village_code}</code></td>
                    <td><strong>${v.village_name}</strong></td>
                    <td>${v.district_name}</td>
                    <td>${v.subdistrict_name}</td>
                    <td>${v.zone || '-'}</td>
                    <td>${v.geb_connection || '-'}</td>
                    <td style="text-align: center;" title="Kuva / Bor / Solar">${wellsBreakdown}</td>
                    <td style="text-align: center; font-weight: 700;">${v.total_wells || 0}</td>
                    <td style="text-align: center;">
                        <span class="badge ${isDone ? 'badge-success' : 'badge-neutral'}" style="font-size: 0.72rem;">
                            ${isDone ? 'Completed' : 'Pending'}
                        </span>
                    </td>
                    <td style="text-align: center;">
                        <button type="button" class="btn btn-outline btn-xs" onclick="ImportManager.openQuickEditVillage(${v.id})" title="Edit village details" style="padding: 3px 8px; font-size: 0.74rem;">
                            <i data-lucide="edit-2" style="width: 12px; height: 12px;"></i>
                            <span>Edit</span>
                        </button>
                    </td>
                </tr>
                `;
            }).join('');
        }

        if (window.lucide) lucide.createIcons();
    },

    changeBatchPage(delta) {
        const newPage = this.batchVillagesPage + delta;
        if (newPage >= 1 && newPage <= this.batchVillagesTotalPages) {
            this.loadBatchVillages(newPage);
        }
    },

    openQuickEditVillage(villageId) {
        const v = this.currentBatchVillages.find(x => x.id == villageId);
        if (!v) return;

        document.getElementById('quickEditVillageId').value = v.id;
        document.getElementById('quickEditVillageCode').textContent = v.village_code;
        document.getElementById('quickEditVillageName').value = v.village_name || '';
        document.getElementById('quickEditDistrictName').value = v.district_name || '';
        document.getElementById('quickEditSubdistrictName').value = v.subdistrict_name || '';
        document.getElementById('quickEditZone').value = v.zone || '';
        document.getElementById('quickEditGeb').value = v.geb_connection || '';
        document.getElementById('quickEditElectricKuva').value = v.electric_kuva || 0;
        document.getElementById('quickEditElectricBor').value = v.electric_bor || 0;
        document.getElementById('quickEditSolarBorKuva').value = v.solar_bor_kuva || 0;
        document.getElementById('quickEditTotalWells').value = v.total_wells || 0;
        document.getElementById('quickEditRemark').value = v.remark || '';

        App.openModal('quickEditVillageModal');
        if (window.lucide) lucide.createIcons();
    },

    calcQuickEditWells() {
        const kuva = parseInt(document.getElementById('quickEditElectricKuva')?.value) || 0;
        const bor = parseInt(document.getElementById('quickEditElectricBor')?.value) || 0;
        const solar = parseInt(document.getElementById('quickEditSolarBorKuva')?.value) || 0;
        const total = kuva + bor + solar;
        const totalEl = document.getElementById('quickEditTotalWells');
        if (totalEl) totalEl.value = total;
    },

    async saveQuickEditVillage(e) {
        e.preventDefault();
        const villageId = document.getElementById('quickEditVillageId')?.value;
        if (!villageId || !this.currentBatchId) return;

        const btn = document.getElementById('btnSaveQuickEditVillage');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span>Saving...</span>';
        }

        const payload = {
            village_id: parseInt(villageId),
            village_name: document.getElementById('quickEditVillageName').value.trim(),
            district_name: document.getElementById('quickEditDistrictName').value.trim(),
            subdistrict_name: document.getElementById('quickEditSubdistrictName').value.trim(),
            zone: document.getElementById('quickEditZone').value.trim(),
            geb_connection: document.getElementById('quickEditGeb').value.trim(),
            electric_kuva: parseInt(document.getElementById('quickEditElectricKuva').value) || 0,
            electric_bor: parseInt(document.getElementById('quickEditElectricBor').value) || 0,
            solar_bor_kuva: parseInt(document.getElementById('quickEditSolarBorKuva').value) || 0,
            total_wells: parseInt(document.getElementById('quickEditTotalWells').value) || 0,
            remark: document.getElementById('quickEditRemark').value.trim()
        };

        try {
            const resp = await fetch(`/api/import/batch/${this.currentBatchId}/update-village`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast('Village updated successfully!', 'success');
            App.closeModal('quickEditVillageModal');
            this.loadBatchVillages(this.batchVillagesPage);
            DashboardManager.load();
        } catch (err) {
            App.toast(`Failed to update village: ${err.message}`, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="check"></i><span>Save Changes</span>';
                if (window.lucide) lucide.createIcons();
            }
        }
    },

    handleCorrectionFileSelected(file) {
        if (!file) return;
        this.correctionFile = file;
        const infoBox = document.getElementById('batchCorrectFileInfo');
        const nameEl = document.getElementById('batchCorrectSelectedName');
        if (infoBox && nameEl) {
            infoBox.style.display = 'flex';
            nameEl.textContent = file.name;
        }
    },

    async submitBatchCorrection() {
        if (!this.correctionFile || !this.currentBatchId) {
            App.toast('Please select an Excel or CSV file first.', 'warning');
            return;
        }

        const btn = document.getElementById('btnSubmitBatchCorrection');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span>Updating batch records...</span>';
        }

        const formData = new FormData();
        formData.append('file', this.correctionFile);

        try {
            const resp = await fetch(`/api/import/batch/${this.currentBatchId}/correct`, {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            const res = data.result;
            App.toast(`Batch updated: ${res.updated_count} villages updated, ${res.inserted_count} added.`, 'success');

            // Reset and switch to review tab
            this.correctionFile = null;
            document.getElementById('batchCorrectFileInput').value = '';
            document.getElementById('batchCorrectFileInfo').style.display = 'none';

            this.switchEditTab('review');
            this.loadBatches();
            this.loadBatchVillages(1);
            DashboardManager.load();
            if (typeof PersonManager !== 'undefined') PersonManager.load();
        } catch (err) {
            App.toast(`Batch correction error: ${err.message}`, 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '<i data-lucide="check"></i><span>Apply Corrections & Update</span>';
                if (window.lucide) lucide.createIcons();
            }
        }
    },

    async openDeleteModal(batchId) {
        const numId = parseInt(batchId, 10);
        let batch = this.batches.find(b => b.id == batchId || b.id == numId);
        if (!batch) {
            batch = { id: batchId, filename: `Dataset #${batchId}`, total_rows: 0, active_villages_count: 0 };
        }

        this.currentBatchId = batch.id;
        const deleteIdInput = document.getElementById('deleteBatchId');
        if (deleteIdInput) deleteIdInput.value = batch.id;

        const countEl = document.getElementById('deleteBatchCount');
        const count = batch.active_villages_count !== undefined ? batch.active_villages_count : (batch.total_rows || 0);
        if (countEl) countEl.textContent = Number(count).toLocaleString();

        const fileEl = document.getElementById('deleteBatchFileText');
        if (fileEl) {
            fileEl.textContent = `File: ${batch.filename} • Batch ID #${batch.id}`;
        }

        const warningBanner = document.getElementById('deleteBatchWarningBanner');
        const warningDetails = document.getElementById('deleteBatchWarningDetails');
        const confirmCheckbox = document.getElementById('deleteBatchConfirmCheckbox');
        const deleteBtn = document.getElementById('btnConfirmDeleteBatch');
        const deleteBtnText = document.getElementById('btnConfirmDeleteBatchText');

        // Reset button and state immediately
        if (deleteBtn) deleteBtn.disabled = false;
        if (deleteBtnText) deleteBtnText.textContent = 'Delete Dataset';
        if (warningBanner) warningBanner.style.display = 'none';
        if (confirmCheckbox) confirmCheckbox.checked = true;

        // Open confirmation modal immediately so the user gets instant visual feedback
        App.openModal('deleteBatchModal');
        if (window.lucide) lucide.createIcons();

        // Check safety asynchronously
        try {
            const resp = await fetch(`/api/import/batch/${batch.id}/check-delete`);
            const data = await resp.json();
            const safety = data.safety || {};

            if (safety.total_villages !== undefined && countEl) {
                countEl.textContent = Number(safety.total_villages).toLocaleString();
            }

            if (!safety.is_safe && (safety.assigned_villages > 0 || safety.completed_villages > 0)) {
                if (warningBanner) warningBanner.style.display = 'block';
                if (warningDetails) {
                    warningDetails.innerHTML = `This dataset contains <strong>${safety.assigned_villages} assigned</strong> and <strong>${safety.completed_villages} completed/marked</strong> villages. Deleting will permanently remove this surveyor progress!`;
                }
                if (confirmCheckbox) confirmCheckbox.checked = false;
                if (deleteBtn) deleteBtn.disabled = true;
            } else {
                if (warningBanner) warningBanner.style.display = 'none';
                if (confirmCheckbox) confirmCheckbox.checked = true;
                if (deleteBtn) deleteBtn.disabled = false;
            }
            if (window.lucide) lucide.createIcons();
        } catch (e) {
            console.warn('Safety check notice:', e);
            if (warningBanner) warningBanner.style.display = 'none';
            if (deleteBtn) deleteBtn.disabled = false;
        }
    },

    toggleDeleteConfirm() {
        const cb = document.getElementById('deleteBatchConfirmCheckbox');
        const btn = document.getElementById('btnConfirmDeleteBatch');
        if (btn && cb) {
            btn.disabled = !cb.checked;
        }
    },

    async executeDeleteBatch() {
        if (!this.currentBatchId) {
            App.toast('No dataset selected for deletion.', 'warning');
            return;
        }

        const warningBanner = document.getElementById('deleteBatchWarningBanner');
        const isWarningVisible = warningBanner && warningBanner.style.display !== 'none';
        const confirmCheckbox = document.getElementById('deleteBatchConfirmCheckbox');

        if (isWarningVisible && (!confirmCheckbox || !confirmCheckbox.checked)) {
            App.toast('Please check the confirmation box to confirm removing active surveyor work.', 'warning');
            return;
        }

        const btn = document.getElementById('btnConfirmDeleteBatch');
        const btnText = document.getElementById('btnConfirmDeleteBatchText');
        if (btn) btn.disabled = true;
        if (btnText) btnText.textContent = 'Deleting dataset...';

        try {
            const resp = await fetch(`/api/import/batch/${this.currentBatchId}/delete`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ force: isWarningVisible ? confirmCheckbox.checked : true })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error || data.warning || 'Failed to delete dataset.');

            const deletedCount = data.deleted_villages !== undefined ? Number(data.deleted_villages) : 0;
            const protectedCount = data.protected_villages !== undefined ? Number(data.protected_villages) : 0;
            let successMsg = `Dataset "${data.filename || ''}" deleted successfully.`;
            if (deletedCount > 0 && protectedCount > 0) {
                successMsg += ` (${deletedCount.toLocaleString()} villages removed, ${protectedCount.toLocaleString()} active/completed villages protected).`;
            } else if (deletedCount > 0) {
                successMsg += ` (${deletedCount.toLocaleString()} active villages removed).`;
            } else if (protectedCount > 0) {
                successMsg += ` (${protectedCount.toLocaleString()} active villages preserved).`;
            }

            App.toast(successMsg, 'success');
            App.closeModal('deleteBatchModal');
            this.currentBatchId = null;

            // Immediate reactive update of all dependent UI
            await this.loadBatches();
            if (typeof DashboardManager !== 'undefined' && DashboardManager.load) {
                DashboardManager.load();
            }
            if (typeof PersonManager !== 'undefined' && PersonManager.load) {
                PersonManager.load();
            }
            if (typeof VillagesManager !== 'undefined' && VillagesManager.load) {
                VillagesManager.load();
            }
        } catch (err) {
            App.toast(`Failed to delete dataset: ${err.message}`, 'error');
        } finally {
            if (btn) btn.disabled = false;
            if (btnText) btnText.textContent = 'Delete Dataset';
            if (window.lucide) lucide.createIcons();
        }
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    },

    async handleFile(file) {
        this.selectedFile = file;
        const formData = new FormData();
        formData.append('file', file);

        App.toast(`Reading ${file.name}...`, 'info');

        try {
            const resp = await fetch('/api/import/preview', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.previewData = data.preview;
            this.renderPreview(data.preview);
        } catch (e) {
            App.toast(`File preview error: ${e.message}`, 'error');
        }
    },

    renderPreview(preview) {
        document.getElementById('excelDropzone').style.display = 'none';
        document.getElementById('importConfigSection').style.display = 'block';
        document.getElementById('importResultCard').style.display = 'none';

        document.getElementById('previewFileName').textContent = preview.filename;
        document.getElementById('previewRowCount').textContent = `Detected ~${preview.total_estimated_rows} rows`;

<<<<<<< HEAD
=======
        // Canonical fields target list
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        const canonicalOptions = [
            { id: 'zone', label: 'Zone' },
            { id: 'district_name', label: 'District Name *' },
            { id: 'subdistrict_name', label: 'Subdistrict Name *' },
            { id: 'village_name', label: 'Village Name *' },
            { id: 'village_code', label: 'Village Code *' },
            { id: 'geb_connection', label: 'Geb Connection' },
            { id: 'google_search_orig_nos', label: 'Google Search Original Nos' },
            { id: 'google_edited_nos', label: 'Google Edited Nos and Final KML' },
            { id: 'total_wells', label: 'Total' },
            { id: 'dugwells', label: 'Dugwells' },
            { id: 'bores', label: 'Bores' },
            { id: 'kml_status', label: 'KML Status' },
            { id: 'remark', label: 'Remark' }
        ];

<<<<<<< HEAD
=======
        // Render Column Mapping Controls
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        const grid = document.getElementById('columnMappingGrid');
        grid.innerHTML = preview.headers.map(header => {
            const suggested = preview.suggested_mappings[header] || '';
            const opts = canonicalOptions.map(opt => `
                <option value="${opt.id}" ${opt.id === suggested ? 'selected' : ''}>
                    ${opt.label}
                </option>
            `).join('');

            return `
                <div style="background: #ffffff; padding: 12px; border: 1px solid #e2e8f0; border-radius: 6px;">
                    <div style="font-size: 0.8rem; font-weight: 600; color: #475569; margin-bottom: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${header}">
                        File Column: <strong>"${header}"</strong>
                    </div>
                    <select class="form-control mapping-select" data-actual-header="${header}" style="font-size: 0.82rem;">
                        <option value="">-- Ignore Column --</option>
                        ${opts}
                    </select>
                </div>
            `;
        }).join('');

<<<<<<< HEAD
=======
        // Render Sample Table
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        const thead = document.getElementById('previewTableHead');
        const tbody = document.getElementById('previewTableBody');

        thead.innerHTML = `<tr>${preview.headers.map(h => `<th>${h}</th>`).join('')}</tr>`;
        tbody.innerHTML = preview.preview_rows.map(row => `
            <tr>${preview.headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>
        `).join('');

        lucide.createIcons();
    },

    async executeImport() {
        if (!this.selectedFile) return;

<<<<<<< HEAD
=======
        // Gather column mappings
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        const mappings = {};
        document.querySelectorAll('.mapping-select').forEach(sel => {
            const actual = sel.getAttribute('data-actual-header');
            const val = sel.value;
            if (actual && val) mappings[actual] = val;
        });

        const dupMode = document.querySelector('input[name="dupMode"]:checked')?.value || 'skip';

        const btn = document.getElementById('startImportBtn');
        btn.disabled = true;
<<<<<<< HEAD
        btn.innerHTML = '<span>Importing dataset...</span>';
=======
        btn.innerHTML = '<span>Importing data...</span>';
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('duplicate_mode', dupMode);
        formData.append('column_mappings', JSON.stringify(mappings));

        try {
            const resp = await fetch('/api/import/process', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.showResult(data.result);
            App.toast('Batch import successfully completed!', 'success');
<<<<<<< HEAD

            // Immediately refresh batches, dashboard, person managers
            this.loadBatches();
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            DashboardManager.load();
            if (typeof PersonManager !== 'undefined') {
                PersonManager.load();
            }
        } catch (e) {
            App.toast(`Import failed: ${e.message}`, 'error');
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="check-check"></i><span>Confirm & Import Data</span>';
            lucide.createIcons();
        }
    },

    showResult(res) {
        document.getElementById('importConfigSection').style.display = 'none';
        const card = document.getElementById('importResultCard');
        card.style.display = 'block';

<<<<<<< HEAD
        document.getElementById('resTotal').textContent = (res.total_rows || 0).toLocaleString();
        document.getElementById('resInserted').textContent = (res.inserted_count || 0).toLocaleString();
        document.getElementById('resUpdated').textContent = (res.updated_count || 0).toLocaleString();
        document.getElementById('resDuplicates').textContent = (res.duplicates_detected || 0).toLocaleString();
        document.getElementById('resInvalid').textContent = (res.invalid_rows || 0).toLocaleString();
=======
        document.getElementById('resTotal').textContent = res.total_rows;
        document.getElementById('resInserted').textContent = res.inserted_count;
        document.getElementById('resUpdated').textContent = res.updated_count;
        document.getElementById('resDuplicates').textContent = res.duplicates_detected;
        document.getElementById('resInvalid').textContent = res.invalid_rows;
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

        const errContainer = document.getElementById('errorDownloadContainer');
        const errLink = document.getElementById('errorReportLink');
        if (res.has_errors && res.error_report_filename) {
            errContainer.style.display = 'block';
            errLink.href = `/api/import/errors/${res.error_report_filename}`;
        } else {
            errContainer.style.display = 'none';
        }
    },

    reset() {
        this.selectedFile = null;
        this.previewData = null;
        document.getElementById('excelFileInput').value = '';
        document.getElementById('excelDropzone').style.display = 'block';
        document.getElementById('importConfigSection').style.display = 'none';
        document.getElementById('importResultCard').style.display = 'none';
        const btn = document.getElementById('startImportBtn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="check-check"></i><span>Confirm & Import Data</span>';
        }
    }
};
<<<<<<< HEAD
window.ImportManager = ImportManager;
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

/* =========================================================================
   3. ALL VILLAGES MANAGER
   ========================================================================= */
const VillagesManager = {
    currentPage: 1,
    pageSize: 20,
    selectedIds: new Set(),
    sortBy: 'district_name',
    sortDir: 'asc',
<<<<<<< HEAD
    currentZone: '',
    currentStatus: 'all',
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

    init() {
        const searchInput = document.getElementById('villageSearchInput');
        if (searchInput) {
            let timeout = null;
            searchInput.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.currentPage = 1;
                    this.load();
                }, 300);
            });
        }

<<<<<<< HEAD
        const zoneSelect = document.getElementById('filterZone');
        if (zoneSelect) {
            zoneSelect.addEventListener('change', (e) => {
                this.currentZone = e.target.value;
                this.currentPage = 1;
                this.updateScopeHeader();
                this.loadScopeMetrics();
                this.load();
            });
        }

        ['filterDistrict', 'filterSubdistrict', 'filterAssignedPerson'].forEach(id => {
=======
        ['filterDistrict', 'filterSubdistrict', 'filterZone', 'filterStatus'].forEach(id => {
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', () => {
                this.currentPage = 1;
                this.load();
            });
        });

<<<<<<< HEAD
        const statusSelect = document.getElementById('filterStatus');
        if (statusSelect) {
            statusSelect.addEventListener('change', (e) => {
                const val = e.target.value;
                const tab = val || 'all';
                this.currentStatus = tab;
                ['all', 'pending', 'assigned', 'completed'].forEach(t => {
                    const btn = document.getElementById(`pillStatus${t.charAt(0).toUpperCase() + t.slice(1)}`);
                    if (btn) {
                        if (t === tab) btn.classList.add('active');
                        else btn.classList.remove('active');
                    }
                });
                this.currentPage = 1;
                this.load();
            });
        }

        const resetBtn = document.getElementById('resetFiltersBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                const sIn = document.getElementById('villageSearchInput');
                if (sIn) sIn.value = '';
                const fD = document.getElementById('filterDistrict');
                if (fD) fD.value = '';
                const fS = document.getElementById('filterSubdistrict');
                if (fS) fS.value = '';
                const fP = document.getElementById('filterAssignedPerson');
                if (fP) fP.value = '';
                const fZ = document.getElementById('filterZone');
                if (fZ) fZ.value = '';
                const fSt = document.getElementById('filterStatus');
                if (fSt) fSt.value = '';

                this.currentZone = '';
                this.currentStatus = 'all';
                this.setStatusTab('all');
                this.loadScopeMetrics();
=======
        const resetBtn = document.getElementById('resetFiltersBtn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                document.getElementById('villageSearchInput').value = '';
                document.getElementById('filterDistrict').value = '';
                document.getElementById('filterSubdistrict').value = '';
                document.getElementById('filterZone').value = '';
                document.getElementById('filterStatus').value = '';
                this.currentPage = 1;
                this.load();
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            });
        }

        // Pagination buttons
        document.getElementById('prevPageBtn')?.addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage--;
                this.load();
            }
        });
        document.getElementById('nextPageBtn')?.addEventListener('click', () => {
            this.currentPage++;
            this.load();
        });
        document.getElementById('pageSizeSelect')?.addEventListener('change', (e) => {
            this.pageSize = parseInt(e.target.value);
            this.currentPage = 1;
            this.load();
        });

        // Select All Checkbox
        document.getElementById('selectAllCheckbox')?.addEventListener('change', (e) => {
            const checked = e.target.checked;
            document.querySelectorAll('.village-row-checkbox').forEach(cb => {
                cb.checked = checked;
                const id = parseInt(cb.value);
                if (checked) this.selectedIds.add(id);
                else this.selectedIds.delete(id);
            });
            this.updateBulkActionBar();
        });

        // Bulk status
        document.getElementById('applyBulkStatusBtn')?.addEventListener('click', () => this.applyBulkStatus());
        document.getElementById('clearSelectionBtn')?.addEventListener('click', () => {
            this.selectedIds.clear();
            document.querySelectorAll('.village-row-checkbox').forEach(cb => cb.checked = false);
            const selectAll = document.getElementById('selectAllCheckbox');
            if (selectAll) selectAll.checked = false;
            this.updateBulkActionBar();
        });
        document.getElementById('exportSelectedBtn')?.addEventListener('click', () => this.exportSelected());

        // Village Edit Form
        document.getElementById('villageEditForm')?.addEventListener('submit', (e) => this.saveVillageEdit(e));

        this.loadFilters();
    },

<<<<<<< HEAD
    updateScopeHeader() {
        const titleEl = document.getElementById('villagesViewTitle');
        const subtitleEl = document.getElementById('villagesViewSubtitle');
        const zone = this.currentZone;
        const status = this.currentStatus;

        if (zone) {
            if (titleEl) titleEl.innerHTML = `<i data-lucide="layers" style="color: #2563eb;"></i> <span>Zone: ${escapeQuotes(zone)} — Village Records</span>`;
            if (subtitleEl) subtitleEl.textContent = `Displaying village records, live status, and metrics scoped to ${zone} zone.`;
        } else if (status === 'pending') {
            if (titleEl) titleEl.innerHTML = `<i data-lucide="clock" style="color: #d97706;"></i> <span>Pending Villages — Work Incomplete</span>`;
            if (subtitleEl) subtitleEl.textContent = `All active villages across all zones where marking or verification is still pending.`;
        } else if (status === 'completed') {
            if (titleEl) titleEl.innerHTML = `<i data-lucide="check-circle-2" style="color: #059669;"></i> <span>Completed Villages — Verified &amp; Done</span>`;
            if (subtitleEl) subtitleEl.textContent = `All active villages across all zones with work status completed and verified.`;
        } else if (status === 'assigned') {
            if (titleEl) titleEl.innerHTML = `<i data-lucide="user-check" style="color: #4f46e5;"></i> <span>Assigned Villages — Allocated</span>`;
            if (subtitleEl) subtitleEl.textContent = `All villages currently allocated to field surveyors and staff.`;
        } else {
            if (titleEl) titleEl.innerHTML = `<i data-lucide="database" style="color: #2563eb;"></i> <span>All Village Records &amp; Intelligence</span>`;
            if (subtitleEl) subtitleEl.textContent = `Complete database records with live search, filters, pagination, and assignment status.`;
        }
        lucide.createIcons();
    },

    async loadScopeMetrics() {
        try {
            const url = this.currentZone 
                ? `/api/dashboard/metrics?zone=${encodeURIComponent(this.currentZone)}`
                : '/api/dashboard/metrics';
            const resp = await fetch(url);
            const data = await resp.json();
            if (!data.success) return;

            const m = data.data.summary || {};
            const total = m.total_villages || 0;
            const pending = m.pending_villages || 0;
            const assigned = m.assigned_villages || 0;
            const completed = m.completed_villages || 0;
            const pct = m.progress_percentage || 0;

            if (document.getElementById('villagesStatTotal')) {
                document.getElementById('villagesStatTotal').textContent = total.toLocaleString();
            }
            if (document.getElementById('villagesStatPending')) {
                document.getElementById('villagesStatPending').textContent = pending.toLocaleString();
            }
            if (document.getElementById('villagesStatAssigned')) {
                document.getElementById('villagesStatAssigned').textContent = assigned.toLocaleString();
            }
            if (document.getElementById('villagesStatCompleted')) {
                document.getElementById('villagesStatCompleted').textContent = completed.toLocaleString();
            }
            if (document.getElementById('villagesStatProgress')) {
                document.getElementById('villagesStatProgress').textContent = `${pct}%`;
            }
            if (document.getElementById('villagesProgressBar')) {
                document.getElementById('villagesProgressBar').style.width = `${Math.min(pct, 100)}%`;
            }

            // Quick status pills count badges
            if (document.getElementById('pillCountAll')) {
                document.getElementById('pillCountAll').textContent = total.toLocaleString();
            }
            if (document.getElementById('pillCountPending')) {
                document.getElementById('pillCountPending').textContent = pending.toLocaleString();
            }
            if (document.getElementById('pillCountAssigned')) {
                document.getElementById('pillCountAssigned').textContent = assigned.toLocaleString();
            }
            if (document.getElementById('pillCountCompleted')) {
                document.getElementById('pillCountCompleted').textContent = completed.toLocaleString();
            }
        } catch (e) {
            console.warn('Could not load scope metrics:', e);
        }
    },

    openWithFilters({ zone = '', status = 'all' } = {}) {
        this.currentZone = zone || '';
        this.currentStatus = status || 'all';

        const zoneSel = document.getElementById('filterZone');
        if (zoneSel) zoneSel.value = this.currentZone;

        const statusSel = document.getElementById('filterStatus');
        if (statusSel) statusSel.value = (this.currentStatus === 'all') ? '' : this.currentStatus;

        // Reset text search, district, subdistrict, person
        const searchInput = document.getElementById('villageSearchInput');
        if (searchInput) searchInput.value = '';
        const distSel = document.getElementById('filterDistrict');
        if (distSel) distSel.value = '';
        const subSel = document.getElementById('filterSubdistrict');
        if (subSel) subSel.value = '';
        const personSel = document.getElementById('filterAssignedPerson');
        if (personSel) personSel.value = '';

        // Update pill button active states
        ['all', 'pending', 'assigned', 'completed'].forEach(t => {
            const btn = document.getElementById(`pillStatus${t.charAt(0).toUpperCase() + t.slice(1)}`);
            if (btn) {
                if (t === this.currentStatus) btn.classList.add('active');
                else btn.classList.remove('active');
            }
        });

        this.updateScopeHeader();
        this.loadScopeMetrics();
        this.currentPage = 1;
        this.load();
    },

    setStatusTab(tab) {
        this.currentStatus = tab || 'all';

        // Update pill buttons active state
        ['all', 'pending', 'assigned', 'completed'].forEach(t => {
            const btn = document.getElementById(`pillStatus${t.charAt(0).toUpperCase() + t.slice(1)}`);
            if (btn) {
                if (t === this.currentStatus) btn.classList.add('active');
                else btn.classList.remove('active');
            }
        });

        // Sync status dropdown
        const filterStatus = document.getElementById('filterStatus');
        if (filterStatus) {
            filterStatus.value = (this.currentStatus === 'all') ? '' : this.currentStatus;
        }

        this.updateScopeHeader();
        this.currentPage = 1;
        this.load();
    },

=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    async loadFilters() {
        try {
            const resp = await fetch('/api/villages/filters');
            const data = await resp.json();
            if (data.success) {
                const distSel = document.getElementById('filterDistrict');
                if (distSel) {
<<<<<<< HEAD
                    const currentDist = distSel.value;
                    distSel.innerHTML = '<option value="">All Districts</option>' + 
                        (data.districts || []).map(d => `<option value="${escapeQuotes(d)}" ${d === currentDist ? 'selected' : ''}>${d}</option>`).join('');
                }
                const subSel = document.getElementById('filterSubdistrict');
                if (subSel) {
                    const currentSub = subSel.value;
                    subSel.innerHTML = '<option value="">All Talukas</option>' + 
                        (data.subdistricts || []).map(s => `<option value="${escapeQuotes(s)}" ${s === currentSub ? 'selected' : ''}>${s}</option>`).join('');
                }
                const zoneSel = document.getElementById('filterZone');
                if (zoneSel) {
                    const currentZone = this.currentZone || zoneSel.value;
                    const zones = data.zones && data.zones.length > 0 ? data.zones : ['GPIC', 'KPIC', 'VPIC', 'RPIC'];
                    let zoneHtml = '<option value="">All Zones</option>';
                    zones.forEach(z => {
                        zoneHtml += `<option value="${escapeQuotes(z)}" ${z === currentZone ? 'selected' : ''}>${z}</option>`;
                    });
                    zoneSel.innerHTML = zoneHtml;
                }
                const personSel = document.getElementById('filterAssignedPerson');
                if (personSel) {
                    const currentP = personSel.value;
                    let personHtml = '<option value="">All Surveyors</option><option value="unassigned">Unassigned</option>';
                    if (data.persons && data.persons.length > 0) {
                        data.persons.forEach(p => {
                            personHtml += `<option value="${p.id}" ${p.id == currentP ? 'selected' : ''}>${p.name || p.full_name || p.username}</option>`;
                        });
                    }
                    personSel.innerHTML = personHtml;
=======
                    distSel.innerHTML = '<option value="">All Districts</option>' + 
                        data.districts.map(d => `<option value="${d}">${d}</option>`).join('');
                }
                const subSel = document.getElementById('filterSubdistrict');
                if (subSel) {
                    subSel.innerHTML = '<option value="">All Subdistricts</option>' + 
                        data.subdistricts.map(s => `<option value="${s}">${s}</option>`).join('');
                }
                const zoneSel = document.getElementById('filterZone');
                if (zoneSel) {
                    zoneSel.innerHTML = '<option value="">All Zones</option>' + 
                        data.zones.map(z => `<option value="${z}">${z}</option>`).join('');
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
                }
            }
        } catch (e) {
            console.warn('Could not load filters:', e);
        }
    },

    async load() {
        const search = document.getElementById('villageSearchInput')?.value || '';
<<<<<<< HEAD
        const zone = document.getElementById('filterZone')?.value || '';
        const district = document.getElementById('filterDistrict')?.value || '';
        const subdistrict = document.getElementById('filterSubdistrict')?.value || '';
        const person = document.getElementById('filterAssignedPerson')?.value || '';
        const status = document.getElementById('filterStatus')?.value || '';

        // If zone filter dropdown changed, synchronize scope
        if (zone !== this.currentZone) {
            this.currentZone = zone;
            this.updateScopeHeader();
            this.loadScopeMetrics();
        }

=======
        const district = document.getElementById('filterDistrict')?.value || '';
        const subdistrict = document.getElementById('filterSubdistrict')?.value || '';
        const zone = document.getElementById('filterZone')?.value || '';
        const status = document.getElementById('filterStatus')?.value || '';

>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        const params = new URLSearchParams({
            page: this.currentPage,
            page_size: this.pageSize,
            search,
            district,
            subdistrict,
            zone,
<<<<<<< HEAD
=======
            status,
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            sort_by: this.sortBy,
            sort_dir: this.sortDir
        });

<<<<<<< HEAD
        if (person === 'unassigned') {
            params.append('assignment_status', 'unassigned');
        } else if (person) {
            params.append('person_id', person);
        }

        if (status) {
            params.append('status', status);
        }

=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        try {
            const resp = await fetch(`/api/villages?${params.toString()}`);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.renderTable(data.data);
        } catch (e) {
            App.toast('Failed to load villages from database.', 'error');
        }
    },

    renderTable(data) {
        const tbody = document.getElementById('villagesTableBody');
        if (!tbody) return;

<<<<<<< HEAD
        if (!data.items || data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 36px; color: #94a3b8;">No matching villages found in database.</td></tr>';
=======
        if (data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="16" style="text-align: center; padding: 36px; color: #94a3b8;">No matching villages found.</td></tr>';
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            this.updatePagination(0, 0, 1, 1);
            return;
        }

        tbody.innerHTML = data.items.map(v => {
            const isChecked = this.selectedIds.has(v.id) ? 'checked' : '';
<<<<<<< HEAD
            const isCorrection = (v.work_status === 'Correction Required' || v.kml_status === 'Correction Required');
            const isDone = !isCorrection && (v.work_status === 'Done' || ['Done', 'Verified', 'Marking Completed', 'Finalized'].includes(v.kml_status));
            
            let statusBadge = '';
            if (isCorrection) {
                statusBadge = `
                    <span class="badge" style="background:#fff1f2; color:#e11d48; border:1px solid #fecdd3; font-weight:700; display:inline-flex; align-items:center; gap:3px;">
                        <i data-lucide="alert-circle" style="width:12px;height:12px;"></i> Correction Required
                    </span>
                    ${v.correction_reason ? `<div style="font-size:0.72rem; color:#be123c; margin-top:2px; max-width:200px; white-space:normal; line-height:1.2;" title="${escapeQuotes(v.correction_reason)}">Reason: ${escapeQuotes(v.correction_reason)}</div>` : ''}
                `;
            } else if (isDone) {
                const compDateStr = v.completion_date || (v.updated_at ? new Date(v.updated_at).toLocaleDateString() : '');
                statusBadge = `
                    <span class="badge" style="background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; font-weight:700; display:inline-flex; align-items:center; gap:3px;">
                        <i data-lucide="check-circle-2" style="width:12px;height:12px;"></i> Completed
                    </span>
                    ${compDateStr ? `<div style="font-size:0.72rem; color:#059669; font-weight:600; margin-top:2px;">Completed: ${compDateStr}</div>` : ''}
                `;
            } else if (v.assigned_person_name) {
                statusBadge = `
                    <span class="badge" style="background:#fef3c7; color:#b45309; border:1px solid #fde68a; font-weight:600; display:inline-flex; align-items:center; gap:3px;">
                        <i data-lucide="clock" style="width:12px;height:12px;"></i> Pending
                    </span>
                `;
            } else {
                statusBadge = `
                    <span class="badge" style="background:#f1f5f9; color:#64748b; border:1px solid #e2e8f0; font-weight:600; display:inline-flex; align-items:center; gap:3px;">
                        <i data-lucide="circle-dashed" style="width:12px;height:12px;"></i> Pending (Unassigned)
                    </span>
                `;
            }

            let personCol = '';
            if (v.assigned_person_name) {
                personCol = `
                    <div style="font-weight:600; color:#1e293b; font-size:0.86rem; display:flex; align-items:center; gap:4px;">
                        <i data-lucide="user" style="width:13px;height:13px; color:#4f46e5;"></i>
                        <span>${v.assigned_person_name}</span>
                    </div>
                `;
            } else {
                personCol = `<span style="color:#94a3b8; font-size:0.8rem; font-style:italic;">Unassigned</span>`;
            }

            const kmlButton = v.kml_id 
                ? `<button class="btn btn-secondary btn-sm" onclick="VillagesManager.previewMap(${v.id}, '${escapeQuotes(v.village_name)}')" title="GIS Map Preview"><i data-lucide="map" style="width:13px;height:13px;"></i></button>`
                : '';

            const openWorkBtn = `<button class="btn btn-sm btn-primary" onclick="VillagesManager.openVillageWork(${v.id}, '${escapeQuotes(v.generated_review_url || '')}', this)" style="padding: 4px 9px; font-size: 0.78rem; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; margin-right: 2px;" title="Open village in Village Wells marking portal">
                <i data-lucide="external-link" style="width: 12px; height: 12px;"></i> <span>Open Village Work</span>
            </button>`;

            const reassignBtn = `<button class="btn btn-sm btn-secondary" onclick="VillagesManager.promptReassignVillage(${v.id}, '${escapeQuotes(v.village_name)}', '${escapeQuotes(v.village_code)}', ${v.assigned_person_id || 'null'}, '${escapeQuotes(v.assigned_person_name || '')}')" style="padding: 4px 8px; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 4px; margin-right: 2px; color: #4338ca; border-color: #c7d2fe;" title="Reassign to another surveyor">
                <i data-lucide="user-plus" style="width: 12px; height: 12px;"></i> <span>Reassign</span>
            </button>`;

            const historyBtn = `<button class="btn btn-sm btn-secondary" onclick="VillagesManager.showAssignmentHistory(${v.id}, '${escapeQuotes(v.village_name)}', '${escapeQuotes(v.village_code)}')" style="padding: 4px 8px; font-size: 0.78rem; display: inline-flex; align-items: center; gap: 3px; margin-right: 2px;" title="View Assignment &amp; Correction History">
                <i data-lucide="history" style="width: 12px; height: 12px;"></i> <span>History</span>
            </button>`;

            const reopenButton = isDone
                ? `<button class="btn btn-secondary btn-sm" style="color:#d97706; border-color:#fde68a; margin-right:2px; padding: 4px 8px; font-size: 0.78rem;" onclick="VillagesManager.promptReopenVillage(${v.id}, '${escapeQuotes(v.village_name)}', '${escapeQuotes(v.village_code)}', ${v.assigned_person_id || 'null'}, '${escapeQuotes(v.assigned_person_name || '')}')" title="Reopen &amp; Send for Correction">
                    <i data-lucide="rotate-ccw" style="width:12px;height:12px;"></i> Reopen
                   </button>`
                : '';
=======
            const kmlLink = v.kml_id 
                ? `<a href="/api/kml/download/${v.kml_id}" class="badge badge-kml" style="text-decoration:none;" title="Download KML"><i data-lucide="download" style="width:12px;height:12px;"></i> KML v${v.kml_version}</a>`
                : `<span style="color:#94a3b8; font-size:0.75rem;">None</span>`;
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

            return `
                <tr>
                    <td><input type="checkbox" class="village-row-checkbox" value="${v.id}" ${isChecked} onchange="VillagesManager.toggleRow(${v.id}, this.checked)"></td>
<<<<<<< HEAD
                    <td><span class="badge" style="background:#f8fafc; border:1px solid #e2e8f0; font-weight:700; color:#334155;">${v.zone || '-'}</span></td>
                    <td><strong>${v.district_name || '-'}</strong></td>
                    <td>${v.subdistrict_name || '-'}</td>
                    <td><strong style="color:#0f172a;">${v.village_name}</strong></td>
                    <td><code style="font-weight:600; color:#1e293b; background:#f1f5f9; padding:2px 6px; border-radius:4px;">${v.village_code}</code></td>
                    <td>${personCol}</td>
                    <td>
                        <div style="font-size:0.82rem; color:#334155; font-weight:500;">${v.geb_connection || '-'}</div>
                        <div style="font-size:0.73rem; color:#64748b;">Total: <strong>${v.total_wells || 0}</strong> (B:${v.bores || 0} / D:${v.dugwells || 0})</div>
                    </td>
                    <td>${statusBadge}</td>
                    <td style="text-align:right; white-space:nowrap;">
                        ${openWorkBtn}
                        ${reassignBtn}
                        ${historyBtn}
                        ${reopenButton}
                        <button class="btn btn-secondary btn-sm" onclick="QueueManager.openVillage(${v.id})" title="Process in Queue">
                            <i data-lucide="play" style="width:13px; height:13px;"></i>
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="VillagesManager.openEditModal(${v.id})" title="Edit Details">
                            <i data-lucide="edit" style="width:13px; height:13px;"></i>
                        </button>
                        ${kmlButton}
                        <button class="btn btn-outline btn-sm" style="color: #ef4444; border-color: #fca5a5; margin-left: 2px;" onclick="VillagesManager.confirmDelete(${v.id}, '${escapeQuotes(v.village_name)}', '${escapeQuotes(v.village_code)}')" title="Remove Village">
                            <i data-lucide="trash-2" style="width:13px; height:13px;"></i>
=======
                    <td>${v.zone || ''}</td>
                    <td><strong>${v.district_name}</strong></td>
                    <td>${v.subdistrict_name}</td>
                    <td><strong>${v.village_name}</strong></td>
                    <td><code style="font-weight:600; color:#1e293b;">${v.village_code}</code></td>
                    <td>${v.geb_connection || ''}</td>
                    <td style="text-align:right;">${v.google_search_orig_nos || 0}</td>
                    <td style="text-align:right;">${v.google_edited_nos || 0}</td>
                    <td style="text-align:right;"><strong>${v.total_wells || 0}</strong></td>
                    <td style="text-align:right;">${v.dugwells || 0}</td>
                    <td style="text-align:right;">${v.bores || 0}</td>
                    <td>${kmlLink}</td>
                    <td>
                        ${(v.work_status === 'Done' || v.kml_status === 'Done') ? `
                            <span class="badge" style="background:#ecfdf5; color:#059669; border:1px solid #a7f3d0; font-weight:700; display:inline-flex; align-items:center; gap:3px;">
                                <i data-lucide="check-circle-2" style="width:12px;height:12px;"></i> Done
                            </span>
                            ${v.assigned_person_name ? `<div style="font-size:0.72rem; color:#059669; font-weight:500; margin-top:2px;">by ${v.assigned_person_name}</div>` : ''}
                            ${v.updated_at ? `<div style="font-size:0.70rem; color:#64748b;">${new Date(v.updated_at).toLocaleDateString()}</div>` : ''}
                        ` : (v.assigned_person_name ? `
                            <span class="badge" style="background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; font-weight:600;">Assigned</span>
                            <div style="font-size:0.72rem; color:#1e293b; font-weight:500; margin-top:2px;">to ${v.assigned_person_name}</div>
                            <div style="font-size:0.70rem; color:#d97706; font-weight:600;">Pending</div>
                        ` : `
                            <span class="badge ${getStatusBadgeClass(v.kml_status)}">${v.kml_status || 'Pending'}</span>
                        `)}
                    </td>
                    <td style="max-width:140px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;" title="${v.remark||''}">${v.remark || ''}</td>
                    <td style="text-align:right; white-space:nowrap;">
                        <button class="btn btn-secondary btn-sm" onclick="QueueManager.openVillage(${v.id})" title="Process in Queue">
                            <i data-lucide="play" style="width:14px; height:14px;"></i>
                        </button>
                        <button class="btn btn-secondary btn-sm" onclick="VillagesManager.openEditModal(${v.id})" title="Edit Details">
                            <i data-lucide="edit" style="width:14px; height:14px;"></i>
                        </button>
                        ${v.kml_id ? `<button class="btn btn-secondary btn-sm" onclick="VillagesManager.previewMap(${v.id}, '${escapeQuotes(v.village_name)}')" title="GIS Map Preview"><i data-lucide="map" style="width:14px;height:14px;"></i></button>` : ''}
                        <button class="btn btn-outline btn-sm" style="color: #ef4444; border-color: #fca5a5; margin-left: 4px;" onclick="VillagesManager.confirmDelete(${v.id}, '${escapeQuotes(v.village_name)}', '${escapeQuotes(v.village_code)}')" title="Remove Village">
                            <i data-lucide="trash-2" style="width:14px; height:14px;"></i>
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        this.updatePagination(data.total_count, data.items.length, data.current_page, data.total_pages);
        lucide.createIcons();
    },

<<<<<<< HEAD
    async openVillageWork(villageId, existingUrl, btnEl) {
        if (existingUrl && existingUrl.trim().startsWith('http')) {
            window.open(existingUrl.trim(), '_blank');
            return;
        }

        if (btnEl) {
            btnEl.disabled = true;
            btnEl.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 12px; height: 12px;"></i> Opening...';
            lucide.createIcons();
        }

        try {
            const checkResp = await fetch(`/api/villages/${villageId}/review-url`);
            const checkData = await checkResp.json();
            if (checkData.success && checkData.review_url && checkData.review_url.startsWith('http')) {
                window.open(checkData.review_url, '_blank');
                return;
            }

            const genResp = await fetch(`/api/user/villages/${villageId}/ensure-link`, { method: 'POST' });
            const genData = await genResp.json();
            if (!genData.success || !genData.link) {
                throw new Error(genData.error || 'No review link recorded for this village');
            }

            window.open(genData.link, '_blank');
            await this.load();
        } catch (err) {
            App.toast(`Review link notice: ${err.message}`, 'warning');
        } finally {
            if (btnEl) {
                btnEl.disabled = false;
                btnEl.innerHTML = '<i data-lucide="external-link" style="width: 12px; height: 12px;"></i> <span>Open Village Work</span>';
                lucide.createIcons();
            }
        }
    },

    async promptReassignVillage(villageId, villageName, villageCode, assignedPersonId, assignedPersonName) {
        const modal = document.getElementById('reassignVillageModal');
        if (!modal) return;

        document.getElementById('reassignVillageId').value = villageId;
        document.getElementById('reassignVillageDisplayName').textContent = villageName || 'Village';
        document.getElementById('reassignVillageDisplayCode').textContent = villageCode || '-';
        document.getElementById('reassignVillageDisplayPerson').textContent = assignedPersonName || 'Unassigned';
        document.getElementById('reassignNote').value = '';

        const select = document.getElementById('reassignTargetPersonSelect');
        if (select) {
            select.innerHTML = '<option value="">Loading surveyors...</option>';
            try {
                const resp = await fetch('/api/persons');
                const data = await resp.json();
                let options = '<option value="">-- Choose Field Surveyor --</option>';
                (data.persons || []).forEach(p => {
                    const pid = p.id;
                    const pname = p.name || `Surveyor #${pid}`;
                    const isCurrent = (assignedPersonId && pid == assignedPersonId);
                    options += `<option value="${pid}" ${isCurrent ? 'disabled' : ''}>${escapeQuotes(pname)} ${isCurrent ? '(Current Assignee)' : ''}</option>`;
                });
                select.innerHTML = options;
            } catch (err) {
                select.innerHTML = '<option value="">Error loading surveyors</option>';
            }
        }

        App.openModal('reassignVillageModal');
        lucide.createIcons();
    },

    async executeReassignVillage(e) {
        if (e) e.preventDefault();

        const villageId = parseInt(document.getElementById('reassignVillageId').value);
        const personSelect = document.getElementById('reassignTargetPersonSelect');
        const newPersonId = personSelect && personSelect.value ? parseInt(personSelect.value) : null;
        const note = (document.getElementById('reassignNote').value || '').trim();

        if (!villageId) {
            App.toast('Invalid village ID', 'error');
            return;
        }
        if (!newPersonId) {
            App.toast('Please select a target surveyor to reassign', 'warning');
            return;
        }

        const submitBtn = document.getElementById('reassignSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Reassigning...';
            lucide.createIcons();
        }

        try {
            const resp = await fetch(`/api/villages/${villageId}/reassign`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ person_id: newPersonId, reason: note })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.closeModal('reassignVillageModal');
            App.toast(`Village successfully reassigned to ${data.data?.new_person || 'surveyor'}!`, 'success');

            await this.load();
            await this.loadScopeMetrics();
            if (typeof DashboardManager !== 'undefined' && DashboardManager.load) {
                DashboardManager.load();
            }
            if (typeof PersonManager !== 'undefined' && PersonManager.load) {
                PersonManager.load();
            }
        } catch (err) {
            App.toast(`Reassignment error: ${err.message}`, 'error');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i data-lucide="user-check"></i> <span>Confirm Reassignment</span>';
                lucide.createIcons();
            }
        }
    },

    async showAssignmentHistory(villageId, villageName, villageCode) {
        const modal = document.getElementById('assignmentHistoryModal');
        if (!modal) return;

        document.getElementById('historyModalVillageName').textContent = villageName || 'Village';
        document.getElementById('historyModalVillageCode').textContent = villageCode || '-';
        const container = document.getElementById('historyModalTimelineContainer');
        const linkBox = document.getElementById('historyModalReviewLinkBox');
        const linkEl = document.getElementById('historyModalReviewLink');
        const statusBox = document.getElementById('historyModalStatusBadges');

        container.innerHTML = '<div style="text-align: center; color: #94a3b8; padding: 24px;"><i data-lucide="loader-2" class="spin" style="width: 24px; height: 24px; margin-bottom: 8px; display: inline-block;"></i><div>Loading assignment history...</div></div>';
        App.openModal('assignmentHistoryModal');
        lucide.createIcons();

        try {
            const resp = await fetch(`/api/villages/${villageId}/assignment-history`);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            const d = data.data || {};
            const v = d.village || {};
            document.getElementById('historyModalVillageLocation').textContent = `${v.zone || ''} • ${v.district_name || ''} • ${v.subdistrict_name || ''}`;

            if (statusBox) {
                statusBox.innerHTML = `
                    <span class="badge" style="background:#f1f5f9; color:#1e293b; border:1px solid #cbd5e1; font-weight:700;">${v.work_status || 'Pending'}</span>
                    <span class="badge" style="background:#e0e7ff; color:#3730a3; font-weight:700;">${v.assigned_person_name || 'Unassigned'}</span>
                `;
            }

            if (v.generated_review_url && linkBox && linkEl) {
                linkBox.style.display = 'block';
                linkEl.href = v.generated_review_url;
                linkEl.textContent = v.generated_review_url;
            } else if (linkBox) {
                linkBox.style.display = 'none';
            }

            const events = [];
            (d.assignments || []).forEach(a => {
                events.push({
                    type: 'assignment',
                    title: `Assigned to ${a.person_name || 'Surveyor'}`,
                    detail: `Status: ${a.status} • Assigned by: ${a.assigned_by || 'Admin'} ${a.unassigned_at ? ' • Unassigned: ' + a.unassigned_at : ''}`,
                    date: a.assigned_at,
                    badge: a.status === 'Active' ? 'Active' : 'Previous',
                    badgeColor: a.status === 'Active' ? '#10b981' : '#64748b'
                });
            });

            (d.corrections || []).forEach(c => {
                events.push({
                    type: 'correction',
                    title: `Correction Reopen: ${c.correction_reason || 'Reopened'}`,
                    detail: `Reopened by: ${c.reopened_by || 'Admin'} • Reassigned to: ${c.new_person_name || 'Same Surveyor'} ${c.resolved_at ? ' • Resolved: ' + c.resolved_at : ' • Pending Correction'}`,
                    date: c.reopened_at,
                    badge: c.status || 'Pending',
                    badgeColor: c.status === 'Resolved' ? '#10b981' : '#d97706'
                });
            });

            (d.processing || []).forEach(p => {
                events.push({
                    type: 'processing',
                    title: `Status: ${p.new_status}`,
                    detail: `${p.action_note || ''} (by ${p.changed_by || 'System'})`,
                    date: p.created_at,
                    badge: p.new_status,
                    badgeColor: '#2563eb'
                });
            });

            events.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0));

            if (events.length === 0) {
                container.innerHTML = '<div style="text-align: center; color: #94a3b8; padding: 24px;">No assignment or audit records found for this village.</div>';
                return;
            }

            container.innerHTML = `
                <div style="display: flex; flex-direction: column; gap: 12px;">
                    ${events.map(ev => `
                        <div style="border-left: 3px solid ${ev.badgeColor}; background: #ffffff; border: 1px solid #e2e8f0; border-left-width: 4px; border-left-color: ${ev.badgeColor}; border-radius: 6px; padding: 12px 16px;">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; flex-wrap: wrap; gap: 6px;">
                                <strong style="color: #0f172a; font-size: 0.88rem;">${ev.title}</strong>
                                <span class="badge" style="font-size: 0.72rem; padding: 2px 8px; border-radius: 12px; background: ${ev.badgeColor}15; color: ${ev.badgeColor}; font-weight: 700;">
                                    ${ev.badge}
                                </span>
                            </div>
                            <div style="font-size: 0.8rem; color: #475569; margin-bottom: 4px;">${ev.detail}</div>
                            <div style="font-size: 0.72rem; color: #94a3b8;">${ev.date ? new Date(ev.date).toLocaleString() : '-'}</div>
                        </div>
                    `).join('')}
                </div>
            `;
            lucide.createIcons();
        } catch (err) {
            container.innerHTML = `<div style="text-align: center; color: #ef4444; padding: 24px;">Failed to load history: ${err.message}</div>`;
        }
    },

    warnMissingReviewLink(villageName, villageCode) {
        App.toast(`Warning: No genuine review URL recorded in database for village "${villageName}" (${villageCode}). Generating fake URLs is strictly prohibited.`, 'warning');
    },

=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    toggleRow(id, isChecked) {
        if (isChecked) this.selectedIds.add(id);
        else this.selectedIds.delete(id);
        this.updateBulkActionBar();
    },

    updateBulkActionBar() {
        const bar = document.getElementById('bulkActionBar');
        const badge = document.getElementById('selectedCountBadge');
        if (!bar || !badge) return;

        if (this.selectedIds.size > 0) {
            bar.style.display = 'flex';
            badge.textContent = `${this.selectedIds.size} Selected`;
        } else {
            bar.style.display = 'none';
        }
    },

    async applyBulkStatus() {
        const select = document.getElementById('bulkStatusSelect');
        const status = select.value;
        if (!status) {
            App.toast('Please select a status to apply.', 'warning');
            return;
        }

        try {
            const resp = await fetch('/api/villages/bulk-status', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    village_ids: Array.from(this.selectedIds),
                    status: status,
                    action_note: `Bulk updated to ${status}`
                })
            });
            const data = await resp.json();
            if (data.success) {
                App.toast(`Successfully updated ${data.updated_count} villages.`, 'success');
                this.selectedIds.clear();
                this.updateBulkActionBar();
                this.load();
            } else {
                throw new Error(data.error);
            }
        } catch (e) {
            App.toast(`Bulk update failed: ${e.message}`, 'error');
        }
    },

    exportSelected() {
        if (this.selectedIds.size === 0) return;
        const ids = Array.from(this.selectedIds).join(',');
        window.location.href = `/api/export/excel?selected_ids=${ids}`;
    },

    updatePagination(totalCount, currentCount, page, totalPages) {
        const info = document.getElementById('paginationInfo');
        const pageSpan = document.getElementById('currentPageSpan');
        const prevBtn = document.getElementById('prevPageBtn');
        const nextBtn = document.getElementById('nextPageBtn');

        const start = totalCount === 0 ? 0 : (page - 1) * this.pageSize + 1;
        const end = Math.min(start + currentCount - 1, totalCount);

        if (info) info.textContent = `Showing ${start} to ${end} of ${totalCount.toLocaleString()} villages`;
        if (pageSpan) pageSpan.textContent = `Page ${page} of ${totalPages || 1}`;
        if (prevBtn) prevBtn.disabled = page <= 1;
        if (nextBtn) nextBtn.disabled = page >= totalPages;
    },

    async openEditModal(villageId) {
        try {
            const resp = await fetch(`/api/villages/${villageId}`);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            const v = data.village;
            document.getElementById('editVillageId').value = v.id;
            document.getElementById('editVillageName').value = v.village_name;
            document.getElementById('editVillageCode').value = v.village_code;
            document.getElementById('editDistrictName').value = v.district_name;
            document.getElementById('editSubdistrictName').value = v.subdistrict_name;
            document.getElementById('editZone').value = v.zone || '';
            document.getElementById('editGeb').value = v.geb_connection || '';
            document.getElementById('editDugwells').value = v.dugwells || 0;
            document.getElementById('editBores').value = v.bores || 0;
            document.getElementById('editTotalWells').value = v.total_wells || 0;
            document.getElementById('editOrigNos').value = v.google_search_orig_nos || 0;
            document.getElementById('editEditedNos').value = v.google_edited_nos || 0;
            document.getElementById('editStatus').value = v.kml_status || 'Pending';
            document.getElementById('editRemark').value = v.remark || '';

            App.openModal('villageEditModal');
        } catch (e) {
            App.toast(`Could not load village details: ${e.message}`, 'error');
        }
    },

    async saveVillageEdit(e) {
        e.preventDefault();
        const id = document.getElementById('editVillageId').value;
        const payload = {
            village_name: document.getElementById('editVillageName').value.trim(),
            district_name: document.getElementById('editDistrictName').value.trim(),
            subdistrict_name: document.getElementById('editSubdistrictName').value.trim(),
            zone: document.getElementById('editZone').value.trim(),
            geb_connection: document.getElementById('editGeb').value.trim(),
            dugwells: parseInt(document.getElementById('editDugwells').value) || 0,
            bores: parseInt(document.getElementById('editBores').value) || 0,
            total_wells: parseInt(document.getElementById('editTotalWells').value) || 0,
            google_search_orig_nos: parseInt(document.getElementById('editOrigNos').value) || 0,
            google_edited_nos: parseInt(document.getElementById('editEditedNos').value) || 0,
            kml_status: document.getElementById('editStatus').value,
            remark: document.getElementById('editRemark').value.trim()
        };

        try {
            const resp = await fetch(`/api/villages/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.closeModal('villageEditModal');
            App.toast('Village updated successfully!', 'success');
            this.load();
        } catch (err) {
            App.toast(`Failed to update village: ${err.message}`, 'error');
        }
    },

    async previewMap(villageId, villageName) {
        document.getElementById('mapModalTitle').textContent = `GIS Preview - ${villageName}`;
        App.openModal('mapPreviewModal');

        setTimeout(async () => {
            try {
                const resp = await fetch(`/api/kml/geojson/${villageId}`);
                const data = await resp.json();
                if (!data.success) throw new Error(data.error);

                renderLeafletMap('modalLeafletMap', data.geojson, data.bounds);
            } catch (e) {
                App.toast('Could not render GIS map.', 'error');
            }
        }, 200);
    },

<<<<<<< HEAD
    async promptReopenVillage(villageId, villageName, villageCode, assignedPersonId, assignedPersonName) {
        const modal = document.getElementById('reopenVillageModal');
        if (!modal) return;

        document.getElementById('reopenVillageId').value = villageId;
        document.getElementById('reopenVillageDisplayName').textContent = villageName || 'Village';
        document.getElementById('reopenVillageDisplayCode').textContent = villageCode || '—';
        document.getElementById('reopenVillageDisplayPerson').textContent = assignedPersonName || 'Unassigned';
        document.getElementById('reopenCorrectionReason').value = '';

        // Populate person dropdown
        const select = document.getElementById('reopenTargetPersonSelect');
        if (select) {
            select.innerHTML = '<option value="">Loading surveyors...</option>';
            try {
                const resp = await fetch('/api/persons');
                const data = await resp.json();
                const persons = data.persons || data.data || [];
                let options = '<option value="">-- Choose Field Surveyor (or keep unassigned) --</option>';
                persons.forEach(p => {
                    const pid = p.id;
                    const pname = p.name || p.full_name || p.username;
                    const isSelected = (assignedPersonId && pid == assignedPersonId) ? 'selected' : '';
                    options += `<option value="${pid}" ${isSelected}>${escapeQuotes(pname)}</option>`;
                });
                select.innerHTML = options;
            } catch (err) {
                console.error('Error loading persons for reopen modal:', err);
                select.innerHTML = '<option value="">Failed to load surveyors</option>';
            }
        }

        const submitBtn = document.getElementById('reopenSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i data-lucide="rotate-ccw"></i> <span>Confirm Reopen &amp; Reassign</span>';
        }

        App.openModal('reopenVillageModal');
        if (window.lucide) lucide.createIcons();
    },

    async executeReopenVillage(e) {
        if (e) e.preventDefault();

        const villageId = parseInt(document.getElementById('reopenVillageId').value);
        const reason = (document.getElementById('reopenCorrectionReason').value || '').trim();
        const personSelect = document.getElementById('reopenTargetPersonSelect');
        const newPersonId = personSelect && personSelect.value ? parseInt(personSelect.value) : null;

        if (!villageId) {
            App.toast('Invalid village ID', 'error');
            return;
        }

        if (!reason) {
            App.toast('Please provide a correction reason.', 'warning');
            document.getElementById('reopenCorrectionReason').focus();
            return;
        }

        const submitBtn = document.getElementById('reopenSubmitBtn');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> <span>Reopening...</span>';
            if (window.lucide) lucide.createIcons();
        }

        try {
            const resp = await fetch(`/api/villages/${villageId}/reopen`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    reason: reason,
                    new_person_id: newPersonId
                })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error || 'Failed to reopen village');

            App.closeModal('reopenVillageModal');
            App.toast(`Village reopened and marked for correction: ${data.message || ''}`, 'success');

            // Refresh village table and metrics
            await this.load();
            await this.loadScopeMetrics();

            // Also reload Dashboard if DashboardManager exists
            if (typeof DashboardManager !== 'undefined' && DashboardManager.load) {
                DashboardManager.load();
            }
        } catch (err) {
            App.toast(`Reopen error: ${err.message}`, 'error');
        } finally {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i data-lucide="rotate-ccw"></i> <span>Confirm Reopen &amp; Reassign</span>';
                if (window.lucide) lucide.createIcons();
            }
        }
    },

=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    confirmDelete(id, name, code) {
        App.promptDeleteVillage(id, name, code);
    }
};

/* =========================================================================
   4. PROCESSING QUEUE WORKBENCH
   ========================================================================= */
const QueueManager = {
    currentVillage: null,
    prevId: null,
    nextId: null,

    init() {
        document.getElementById('qPrevBtn')?.addEventListener('click', () => {
            if (this.prevId) this.openVillage(this.prevId);
            else App.toast('No previous village in queue.', 'info');
        });

        document.getElementById('qNextBtn')?.addEventListener('click', () => {
            if (this.nextId) this.openVillage(this.nextId);
            else App.toast('No next pending village available.', 'info');
        });

        // Copy details button
        document.getElementById('qCopyDetailsBtn')?.addEventListener('click', () => this.copyDetails());

        // Counts form submit
        document.getElementById('qCountsForm')?.addEventListener('submit', (e) => this.saveCounts(e));

        // Mark Done & Next Pending button
        document.getElementById('qMarkDoneNextBtn')?.addEventListener('click', () => this.markDoneAndNext());

        // Auto calculate total wells when bores or dugwells change
        ['qDugwells', 'qBores'].forEach(id => {
            document.getElementById(id)?.addEventListener('input', () => {
                const d = parseInt(document.getElementById('qDugwells').value) || 0;
                const b = parseInt(document.getElementById('qBores').value) || 0;
                document.getElementById('qTotalWells').value = d + b;
            });
        });

        // Setup Dropzone for Village KML
        const dropzone = document.getElementById('villageKmlDropzone');
        const fileInput = document.getElementById('villageKmlFileInput');
        if (dropzone && fileInput) {
            dropzone.addEventListener('click', () => fileInput.click());
            dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('drag-over'); });
            dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.classList.remove('drag-over');
                if (e.dataTransfer.files.length) this.uploadKML(e.dataTransfer.files[0]);
            });
            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length) this.uploadKML(e.target.files[0]);
            });
        }
    },

    async load(villageId = null) {
        const url = villageId ? `/api/villages/queue/next?current_id=${villageId}` : '/api/villages/queue/next';
        try {
            const resp = await fetch(url);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            const nav = data.data;
            this.prevId = nav.prev_village_id;
            this.nextId = nav.next_village_id;

            document.getElementById('qPendingCount').textContent = nav.pending_count;
            document.getElementById('qCompletedCount').textContent = nav.completed_count;
            document.getElementById('qTotalCount').textContent = nav.total_count;

            if (nav.current_village) {
                this.renderVillage(nav.current_village);
            } else {
                this.renderEmptyState();
            }
        } catch (e) {
            App.toast('Failed to load queue state from database.', 'error');
        }
    },

    openVillage(villageId) {
        App.navigate('processing');
        this.load(villageId);
    },

    renderVillage(v) {
        this.currentVillage = v;

        document.getElementById('qVillageName').textContent = v.village_name;
        document.getElementById('qVillageCode').textContent = v.village_code;
        document.getElementById('qDistrict').textContent = v.district_name;
        document.getElementById('qSubdistrict').textContent = v.subdistrict_name;
        document.getElementById('qZone').textContent = v.zone || 'None';
        document.getElementById('qGeb').textContent = v.geb_connection || 'None';

        const badge = document.getElementById('qStatusBadge');
        badge.className = `badge ${getStatusBadgeClass(v.kml_status)}`;
        badge.textContent = v.kml_status;

        // Form fields
        document.getElementById('qOrigNos').value = v.google_search_orig_nos || 0;
        document.getElementById('qEditedNos').value = v.google_edited_nos || 0;
        document.getElementById('qDugwells').value = v.dugwells || 0;
        document.getElementById('qBores').value = v.bores || 0;
        document.getElementById('qTotalWells').value = v.total_wells || (v.dugwells + v.bores);
        document.getElementById('qStatusSelect').value = v.kml_status || 'Pending';
        document.getElementById('qRemark').value = v.remark || '';

        // KML metrics
        document.getElementById('kmlPointsVal').textContent = v.kml_points || 0;
        document.getElementById('kmlPolysVal').textContent = v.kml_polygons || 0;
        document.getElementById('kmlTotalVal').textContent = v.kml_total_placemarks || 0;
        document.getElementById('kmlVersionVal').textContent = v.kml_version ? `v${v.kml_version}` : 'None';

        // Download link
        const slot = document.getElementById('kmlDownloadSlot');
        if (v.kml_id) {
            slot.innerHTML = `<a href="/api/kml/download/${v.kml_id}" class="btn btn-secondary btn-sm"><i data-lucide="download"></i> Download KML</a>`;
        } else {
            slot.innerHTML = '';
        }

        // Render Map
        if (v.kml_geojson) {
            try {
                const geojson = JSON.parse(v.kml_geojson);
                const bounds = v.kml_bounds ? JSON.parse(v.kml_bounds) : null;
                renderLeafletMap('queueLeafletMap', geojson, bounds);
            } catch (err) {
                console.warn('Map parse error:', err);
            }
        } else {
            resetLeafletMap('queueLeafletMap');
        }

        lucide.createIcons();
    },

    renderEmptyState() {
        document.getElementById('qVillageName').textContent = 'All Villages Completed!';
        document.getElementById('qVillageCode').textContent = '-';
        document.getElementById('qDistrict').textContent = '-';
        document.getElementById('qSubdistrict').textContent = '-';
        document.getElementById('qZone').textContent = '-';
        document.getElementById('qGeb').textContent = '-';
        resetLeafletMap('queueLeafletMap');
        App.toast('All pending villages in the queue are completed!', 'success');
    },

    async copyDetails() {
        if (!this.currentVillage) return;
        const v = this.currentVillage;
        const textToCopy = `${v.village_name} ${v.village_code}`.trim();

        try {
            await navigator.clipboard.writeText(textToCopy);
            App.toast(`Copied: "${textToCopy}" to clipboard!`, 'success');
        } catch (e) {
            // Fallback
            const el = document.createElement('textarea');
            el.value = textToCopy;
            document.body.appendChild(el);
            el.select();
            document.execCommand('copy');
            document.body.removeChild(el);
            App.toast(`Copied: "${textToCopy}"`, 'success');
        }
    },

    async uploadKML(file) {
        if (!this.currentVillage) {
            App.toast('No active village selected.', 'warning');
            return;
        }

        App.toast(`Uploading & parsing ${file.name}...`, 'info');
        const formData = new FormData();
        formData.append('file', file);

        try {
            const resp = await fetch(`/api/kml/upload/${this.currentVillage.id}`, {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast('KML uploaded and verified successfully!', 'success');
            
            // Auto update bores count recommendation if point count detected
            const pointCount = data.data.point_count || 0;
            if (pointCount > 0 && parseInt(document.getElementById('qBores').value) === 0) {
                document.getElementById('qBores').value = pointCount;
                document.getElementById('qTotalWells').value = pointCount + (parseInt(document.getElementById('qDugwells').value) || 0);
                App.toast(`Detected ${pointCount} points in KML. Pre-filled borewell counts for your verification.`, 'info');
            }

            // Reload village queue state
            this.load(this.currentVillage.id);
        } catch (e) {
            App.toast(`KML upload failed: ${e.message}`, 'error');
        }
    },

    async saveCounts(e) {
        if (e) e.preventDefault();
        if (!this.currentVillage) return;

        const payload = {
            google_search_orig_nos: parseInt(document.getElementById('qOrigNos').value) || 0,
            google_edited_nos: parseInt(document.getElementById('qEditedNos').value) || 0,
            dugwells: parseInt(document.getElementById('qDugwells').value) || 0,
            bores: parseInt(document.getElementById('qBores').value) || 0,
            total_wells: parseInt(document.getElementById('qTotalWells').value) || 0,
            kml_status: document.getElementById('qStatusSelect').value,
            remark: document.getElementById('qRemark').value.trim()
        };

        try {
            const resp = await fetch(`/api/villages/${this.currentVillage.id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast('Village progress saved successfully!', 'success');
            this.renderVillage(data.village);
            return true;
        } catch (err) {
            App.toast(`Save failed: ${err.message}`, 'error');
            return false;
        }
    },

    async markDoneAndNext() {
        if (!this.currentVillage) return;

        // Safety check for KML presence
        if (!this.currentVillage.kml_id) {
            const confirmOverride = confirm(
                "Warning: No KML file has been uploaded for this village yet.\n\n" +
                "Are you sure you want to mark this village as Done without a KML file?"
            );
            if (!confirmOverride) return;
        }

        document.getElementById('qStatusSelect').value = 'Done';
        const saved = await this.saveCounts();
        if (saved) {
            App.toast(`Marked "${this.currentVillage.village_name}" as Done!`, 'success');
            if (this.nextId) {
                this.openVillage(this.nextId);
            } else {
                this.load();
            }
        }
    }
};

/* =========================================================================
   5. KML MANAGEMENT
   ========================================================================= */
const KmlManager = {
    async load() {
        const search = document.getElementById('kmlSearchInput')?.value || '';
        try {
            const resp = await fetch(`/api/kml/list?search=${encodeURIComponent(search)}`);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.renderTable(data.files);
        } catch (e) {
            App.toast('Could not load KML library.', 'error');
        }
    },

    init() {
        const searchInput = document.getElementById('kmlSearchInput');
        if (searchInput) {
            let timeout = null;
            searchInput.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => this.load(), 300);
            });
        }
    },

    renderTable(files) {
        const tbody = document.getElementById('kmlManagementTable');
        if (!tbody) return;

        if (!files || files.length === 0) {
            tbody.innerHTML = '<tr><td colspan="11" style="text-align: center; padding: 36px; color: #94a3b8;">No KML files found.</td></tr>';
            return;
        }

        tbody.innerHTML = files.map(f => {
            const sizeKB = (f.file_size / 1024).toFixed(1);
            return `
                <tr>
                    <td><strong>${f.village_name}</strong></td>
                    <td><code>${f.village_code}</code></td>
                    <td>${f.district_name}</td>
                    <td style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${f.original_filename}">${f.original_filename}</td>
                    <td>${sizeKB} KB</td>
                    <td><span class="badge badge-kml">${f.point_count || 0}</span></td>
                    <td>${f.polygon_count || 0}</td>
                    <td><strong>${f.total_placemarks || 0}</strong></td>
                    <td>v${f.version}</td>
                    <td>${f.created_at ? f.created_at.split('T')[0] : ''}</td>
                    <td style="text-align: right;">
                        <a href="/api/kml/download/${f.id}" class="btn btn-secondary btn-sm" title="Download">
                            <i data-lucide="download" style="width:14px; height:14px;"></i>
                        </a>
                        <button class="btn btn-secondary btn-sm" onclick="VillagesManager.previewMap(${f.village_id}, '${f.village_name}')" title="GIS Map Preview">
                            <i data-lucide="map" style="width:14px; height:14px;"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
        lucide.createIcons();
    }
};

function escapeQuotes(str) {
    return (str || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

/* =========================================================================
   5.5. PERSON MANAGEMENT & VILLAGE ASSIGNMENT
   ========================================================================= */
const PersonManager = {
    persons: [],
    currentTab: 'unassigned',
    unassignedPage: 1,
    unassignedPageSize: 20,
    unassignedTotalPages: 1,
    selectedUnassignedIds: new Set(),
    
    assignedPage: 1,
    assignedPageSize: 20,
    assignedTotalPages: 1,
    selectedAssignedIds: new Set(),

    async load() {
        this.selectedUnassignedIds.clear();
        this.selectedAssignedIds.clear();
        this.updateUnassignedSelectedBadge();
        this.updateAssignedSelectedBadge();

        await Promise.all([
            this.loadPersons(),
            this.loadUnassignedVillages(),
            this.loadAssignedVillages()
        ]);
        this.loadFilters();
    },

    async loadFilters() {
        try {
            const resp = await fetch('/api/villages/filters');
            const data = await resp.json();
            if (data.success) {
                const zoneSel1 = document.getElementById('unassignedZoneFilter');
                if (zoneSel1 && !zoneSel1._bound) {
                    zoneSel1._bound = true;
                    zoneSel1.innerHTML = '<option value="">All Zones</option>' + 
                        (data.zones || []).map(z => `<option value="${z}">${z}</option>`).join('');
                    zoneSel1.onchange = () => { this.unassignedPage = 1; this.loadUnassignedVillages(); };
                }
                const distSel1 = document.getElementById('unassignedDistrictFilter');
                if (distSel1 && !distSel1._bound) {
                    distSel1._bound = true;
                    distSel1.innerHTML = '<option value="">All Districts</option>' + 
                        data.districts.map(d => `<option value="${d}">${d}</option>`).join('');
                    distSel1.onchange = () => { this.unassignedPage = 1; this.loadUnassignedVillages(); };
                }
                const subSel1 = document.getElementById('unassignedSubdistrictFilter');
                if (subSel1 && !subSel1._bound) {
                    subSel1._bound = true;
                    subSel1.innerHTML = '<option value="">All Subdistricts</option>' + 
                        data.subdistricts.map(s => `<option value="${s}">${s}</option>`).join('');
                    subSel1.onchange = () => { this.unassignedPage = 1; this.loadUnassignedVillages(); };
                }

                const zoneSel2 = document.getElementById('assignedZoneFilter');
                if (zoneSel2 && !zoneSel2._bound) {
                    zoneSel2._bound = true;
                    zoneSel2.innerHTML = '<option value="">All Zones</option>' + 
                        (data.zones || []).map(z => `<option value="${z}">${z}</option>`).join('');
                    zoneSel2.onchange = () => { this.assignedPage = 1; this.loadAssignedVillages(); };
                }
                const distSel2 = document.getElementById('assignedDistrictFilter');
                if (distSel2 && !distSel2._bound) {
                    distSel2._bound = true;
                    distSel2.innerHTML = '<option value="">All Districts</option>' + 
                        data.districts.map(d => `<option value="${d}">${d}</option>`).join('');
                    distSel2.onchange = () => { this.assignedPage = 1; this.loadAssignedVillages(); };
                }
                const subSel2 = document.getElementById('assignedSubdistrictFilter');
                if (subSel2 && !subSel2._bound) {
                    subSel2._bound = true;
                    subSel2.innerHTML = '<option value="">All Subdistricts</option>' + 
                        data.subdistricts.map(s => `<option value="${s}">${s}</option>`).join('');
                    subSel2.onchange = () => { this.assignedPage = 1; this.loadAssignedVillages(); };
                }
            }
        } catch (e) {
            console.warn('Could not load filters for person assignment:', e);
        }

        const unSearch = document.getElementById('unassignedSearchInput');
        if (unSearch && !unSearch._bound) {
            unSearch._bound = true;
            let timeout = null;
            unSearch.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.unassignedPage = 1;
                    this.loadUnassignedVillages();
                }, 300);
            });
        }

        const asSearch = document.getElementById('assignedSearchInput');
        if (asSearch && !asSearch._bound) {
            asSearch._bound = true;
            let timeout = null;
            asSearch.addEventListener('input', () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    this.assignedPage = 1;
                    this.loadAssignedVillages();
                }, 300);
            });
        }
    },

    async loadPersons() {
        try {
            const resp = await fetch('/api/persons');
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.persons = data.persons || [];
            
            // Update KPI counters
            const kpiEl = document.getElementById('assignKpiPersons');
            if (kpiEl) kpiEl.textContent = this.persons.length.toLocaleString();

            const badgeEl = document.getElementById('rosterCountBadge');
            if (badgeEl) badgeEl.textContent = `${this.persons.length} Persons`;

            // Populate Target Person Dropdown
            const targetSelect = document.getElementById('assignTargetPersonSelect');
            if (targetSelect) {
                targetSelect.innerHTML = '<option value="">-- Choose Person --</option>' + 
                    this.persons.map(p => `<option value="${p.id}">${p.name} (${p.assigned_count || 0} villages)</option>`).join('');
            }

            // Populate Assigned Person Filter Dropdown
            const filterSelect = document.getElementById('assignedPersonFilter');
            if (filterSelect) {
                const curVal = filterSelect.value;
                filterSelect.innerHTML = '<option value="">All Assigned Persons</option>' + 
                    this.persons.map(p => `<option value="${p.id}" ${String(p.id) === String(curVal) ? 'selected' : ''}>${p.name} (${p.assigned_count || 0})</option>`).join('');
            }

            // Populate Export View Person Dropdown
            const exportSelect = document.getElementById('exportPersonSelect');
            if (exportSelect) {
                exportSelect.innerHTML = '<option value="">-- Choose Person --</option>' + 
                    this.persons.map(p => `<option value="${p.id}">${p.name} (${p.assigned_count || 0} villages)</option>`).join('');
            }

            // Render Roster
            this.renderPersonsRoster();
        } catch (e) {
            console.error('Error loading persons:', e);
            App.toast('Failed to load surveyors roster.', 'error');
        }
    },

    renderPersonsRoster() {
        const container = document.getElementById('personsRosterList');
        if (!container) return;

        if (this.persons.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 28px 16px; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px;">
                    <i data-lucide="user-x" style="width: 28px; height: 28px; color: #94a3b8; margin: 0 auto 8px auto;"></i>
                    <div style="font-weight: 600; font-size: 0.88rem; color: #475569;">No surveyors registered</div>
                    <div style="font-size: 0.78rem; color: #64748b; margin-top: 4px;">Click "+ Add New Person" above to create surveyor profiles.</div>
                </div>
            `;
            lucide.createIcons();
            return;
        }

        container.innerHTML = this.persons.map(p => {
            const count = p.assigned_count || 0;
            const phoneStr = p.phone ? `<span style="font-size: 0.75rem; color: #64748b;"><i data-lucide="phone" style="width: 11px; height: 11px; vertical-align: middle;"></i> ${p.phone}</span>` : '';
            const emailStr = p.email ? `<span style="font-size: 0.75rem; color: #64748b;"><i data-lucide="mail" style="width: 11px; height: 11px; vertical-align: middle;"></i> ${p.email}</span>` : '';
            
            return `
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; transition: all 0.2s ease; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                        <div>
                            <div style="font-weight: 700; font-size: 0.92rem; color: #1e293b;">${p.name}</div>
                            <div style="font-size: 0.75rem; color: #64748b;">${p.role || 'Field Surveyor'}</div>
                        </div>
                        <span class="badge ${count > 0 ? 'badge-primary' : 'badge-secondary'}" style="font-size: 0.76rem; font-weight: 700;">
                            ${count} ${count === 1 ? 'village' : 'villages'}
                        </span>
                    </div>

                    ${(phoneStr || emailStr) ? `
                        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 8px;">
                            ${phoneStr}
                            ${emailStr}
                        </div>
                    ` : ''}

                    <div style="display: flex; gap: 6px; margin-top: 8px; border-top: 1px solid #f1f5f9; padding-top: 8px;">
                        <button class="btn btn-secondary btn-sm" style="flex: 1; padding: 4px 8px; font-size: 0.75rem;" onclick="PersonManager.filterByPerson(${p.id}, '${escapeQuotes(p.name)}')">
                            <i data-lucide="eye" style="width: 12px; height: 12px;"></i> View
                        </button>
                        <button class="btn btn-outline btn-sm" style="padding: 4px 8px; font-size: 0.75rem;" onclick="PersonManager.exportPerson(${p.id})" title="Export Assigned Excel">
                            <i data-lucide="download" style="width: 12px; height: 12px;"></i> Excel
                        </button>
                        <button class="btn btn-outline-danger btn-sm" style="padding: 4px 8px; font-size: 0.75rem;" onclick="PersonManager.deletePerson(${p.id}, '${escapeQuotes(p.name)}')" title="Delete Person">
                            <i data-lucide="trash-2" style="width: 12px; height: 12px;"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        lucide.createIcons();
    },

    switchTab(tab) {
        this.currentTab = tab;
        const btnUnassigned = document.getElementById('tabBtnUnassigned');
        const btnAssigned = document.getElementById('tabBtnAssigned');
        const panelUnassigned = document.getElementById('tabPanelUnassigned');
        const panelAssigned = document.getElementById('tabPanelAssigned');

        if (tab === 'unassigned') {
            if (btnUnassigned) btnUnassigned.className = 'btn btn-sm btn-primary';
            if (btnAssigned) btnAssigned.className = 'btn btn-sm btn-secondary';
            if (panelUnassigned) panelUnassigned.style.display = 'block';
            if (panelAssigned) panelAssigned.style.display = 'none';
        } else {
            if (btnUnassigned) btnUnassigned.className = 'btn btn-sm btn-secondary';
            if (btnAssigned) btnAssigned.className = 'btn btn-sm btn-primary';
            if (panelUnassigned) panelUnassigned.style.display = 'none';
            if (panelAssigned) panelAssigned.style.display = 'block';
        }
        lucide.createIcons();
    },

    async loadUnassignedVillages() {
        const search = document.getElementById('unassignedSearchInput')?.value || '';
        const zone = document.getElementById('unassignedZoneFilter')?.value || '';
        const district = document.getElementById('unassignedDistrictFilter')?.value || '';
        const subdistrict = document.getElementById('unassignedSubdistrictFilter')?.value || '';

        const params = new URLSearchParams({
            page: this.unassignedPage,
            page_size: this.unassignedPageSize,
            search,
            zone,
            district,
            subdistrict
        });

        try {
            const resp = await fetch(`/api/villages/unassigned?${params.toString()}`);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.unassignedTotalPages = data.total_pages || 1;
            
            const countBadge = document.getElementById('tabUnassignedCount');
            if (countBadge) countBadge.textContent = (data.total_count || 0).toLocaleString();

            const kpiEl = document.getElementById('assignKpiUnassigned');
            if (kpiEl) kpiEl.textContent = (data.total_count || 0).toLocaleString();

            const infoEl = document.getElementById('unassignedPaginationInfo');
            if (infoEl) {
                const start = Math.min((this.unassignedPage - 1) * this.unassignedPageSize + 1, data.total_count);
                const end = Math.min(this.unassignedPage * this.unassignedPageSize, data.total_count);
                infoEl.textContent = `Showing ${start}-${end} of ${data.total_count} unassigned villages`;
            }

            this.renderUnassignedTable(data.items || []);
        } catch (e) {
            console.error('Error loading unassigned villages:', e);
            App.toast('Failed to load unassigned villages.', 'error');
        }
    },

    renderUnassignedTable(items) {
        const tbody = document.getElementById('unassignedVillagesTableBody');
        if (!tbody) return;

        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 32px; color: #94a3b8;">No unassigned villages found.</td></tr>';
            return;
        }

        tbody.innerHTML = items.map(v => {
            const isChecked = this.selectedUnassignedIds.has(Number(v.id)) ? 'checked' : '';
            return `
                <tr>
                    <td>
                        <input type="checkbox" class="unassigned-row-cb" value="${v.id}" ${isChecked} onchange="PersonManager.toggleUnassignedRow(${v.id}, this.checked)">
                    </td>
                    <td><strong>${v.village_name}</strong></td>
                    <td><code>${v.village_code}</code></td>
                    <td>${v.district_name || ''}</td>
                    <td>${v.subdistrict_name || ''}</td>
                    <td>${v.zone || ''}</td>
                    <td style="text-align: right;"><strong>${v.total_wells || 0}</strong></td>
                    <td style="text-align: right; color: #64748b; font-size: 0.8rem;">
                        ${v.electric_kuva ? `K:${v.electric_kuva}` : ''} ${v.electric_bor ? `B:${v.electric_bor}` : ''}
                    </td>
                    <td style="text-align: right; white-space: nowrap;">
                        <button class="btn btn-outline btn-xs" style="color: #ef4444; border-color: #fca5a5; padding: 3px 7px;" onclick="PersonManager.confirmDeleteVillage(${v.id}, '${escapeQuotes(v.village_name)}', '${escapeQuotes(v.village_code)}')" title="Remove Village">
                            <i data-lucide="trash-2" style="width: 13px; height: 13px;"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
        lucide.createIcons();
        this.updateUnassignedSelectedBadge();
    },

    confirmDeleteVillage(id, name, code) {
        App.promptDeleteVillage(id, name, code);
    },

    toggleUnassignedRow(id, isChecked) {
        const numId = Number(id);
        if (isChecked) this.selectedUnassignedIds.add(numId);
        else this.selectedUnassignedIds.delete(numId);
        this.updateUnassignedSelectedBadge();
    },

    toggleSelectAllUnassigned(checked) {
        document.querySelectorAll('.unassigned-row-cb').forEach(cb => {
            cb.checked = checked;
            const id = Number(cb.value);
            if (checked) this.selectedUnassignedIds.add(id);
            else this.selectedUnassignedIds.delete(id);
        });
        this.updateUnassignedSelectedBadge();
    },

    updateUnassignedSelectedBadge() {
        const count = this.selectedUnassignedIds.size;
        const badge = document.getElementById('unassignedSelectedBadge');
        if (badge) badge.textContent = `${count} Selected`;

        const btnDel = document.getElementById('btnDeleteSelectedUnassigned');
        const btnDelText = document.getElementById('btnDeleteSelectedUnassignedText');
        if (btnDel) {
            btnDel.disabled = (count === 0);
            btnDel.style.opacity = count > 0 ? '1' : '0.55';
            btnDel.style.cursor = count > 0 ? 'pointer' : 'not-allowed';
        }
        if (btnDelText) {
            btnDelText.textContent = count > 0 ? `Delete Selected (${count})` : 'Delete Selected';
        }

        // Keep Select All checkbox in sync with currently visible page checkboxes
        const cbs = document.querySelectorAll('.unassigned-row-cb');
        const selectAllCb = document.getElementById('unassignedSelectAllCheckbox');
        if (selectAllCb) {
            if (cbs.length > 0) {
                selectAllCb.checked = Array.from(cbs).every(cb => cb.checked);
            } else {
                selectAllCb.checked = false;
            }
        }
    },

    async deleteSelectedUnassignedVillages() {
        const count = this.selectedUnassignedIds.size;
        if (count === 0) {
            App.toast('Please select at least one unassigned village to delete.', 'info');
            return;
        }

        const confirmMsg = `Are you sure you want to delete the selected ${count} villages? This action cannot be undone.`;
        if (!window.confirm(confirmMsg)) {
            return;
        }

        const btn = document.getElementById('btnDeleteSelectedUnassigned');
        if (btn) {
            btn.disabled = true;
            btn.style.cursor = 'not-allowed';
            btn.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 14px; height: 14px;"></i> <span>Deleting...</span>';
            if (window.lucide) lucide.createIcons();
        }

        try {
            const villageIds = Array.from(this.selectedUnassignedIds).map(id => Number(id));
            const resp = await fetch('/api/villages/bulk-delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    village_ids: villageIds,
                    unassigned_only: false
                })
            });

            const data = await resp.json();
            if (!resp.ok && (!data.deleted_count && data.deleted_count !== 0)) {
                throw new Error(data.error || 'Failed to delete selected villages.');
            }

            if (data.deleted_count > 0 && data.failed_count === 0) {
                App.toast(`Successfully deleted ${data.deleted_count} unassigned village(s).`, 'success');
            } else if (data.deleted_count > 0 && data.failed_count > 0) {
                const failSummary = (data.failed_villages || []).map(f => `• ${f.name}: ${f.reason}`).slice(0, 3).join('\n');
                const moreText = (data.failed_villages || []).length > 3 ? `\n...and ${data.failed_villages.length - 3} more` : '';
                App.toast(`Deleted ${data.deleted_count} village(s). ${data.failed_count} village(s) could not be deleted:\n${failSummary}${moreText}`, 'warning');
            } else if (data.deleted_count === 0 && data.failed_count > 0) {
                const failSummary = (data.failed_villages || []).map(f => `• ${f.name}: ${f.reason}`).slice(0, 3).join('\n');
                App.toast(`Deletion failed for ${data.failed_count} village(s):\n${failSummary}`, 'error');
            } else {
                App.toast(data.message || 'Bulk delete completed.', 'info');
            }

            // Remove successfully deleted IDs from local selected Set
            if (data.deleted_villages && data.deleted_villages.length) {
                data.deleted_villages.forEach(d => this.selectedUnassignedIds.delete(Number(d.id)));
            }
            if (data.failed_villages && data.failed_villages.length) {
                data.failed_villages.forEach(f => {
                    if (f.reason && f.reason.toLowerCase().includes('not found')) {
                        this.selectedUnassignedIds.delete(Number(f.id));
                    }
                });
            }
            if (data.deleted_count > 0 && data.failed_count === 0) {
                this.selectedUnassignedIds.clear();
            }

            const selectAllCb = document.getElementById('unassignedSelectAllCheckbox');
            if (selectAllCb) selectAllCb.checked = false;

            this.updateUnassignedSelectedBadge();

            // Synchronize views & live KPIs immediately without full-page refresh
            await Promise.all([
                this.loadUnassignedVillages(),
                this.loadPersons(),
                typeof DashboardManager !== 'undefined' && DashboardManager.load ? DashboardManager.load() : Promise.resolve(),
                typeof VillagesManager !== 'undefined' && VillagesManager.load && App.currentView === 'villages' ? VillagesManager.load() : Promise.resolve()
            ]);

        } catch (err) {
            console.error('Bulk delete error:', err);
            App.toast(`Bulk delete failed: ${err.message}`, 'error');
        } finally {
            if (btn) {
                btn.innerHTML = '<i data-lucide="trash-2" style="width: 14px; height: 14px;"></i> <span id="btnDeleteSelectedUnassignedText">Delete Selected</span>';
                if (window.lucide) lucide.createIcons();
            }
            this.updateUnassignedSelectedBadge();
        }
    },

    async assignSelectedVillages() {
        if (this.selectedUnassignedIds.size === 0) {
            App.toast('Please select at least one village to assign.', 'warning');
            return;
        }

        const personSelect = document.getElementById('assignTargetPersonSelect');
        const personId = personSelect?.value;
        if (!personId) {
            App.toast('Please select a person from the dropdown.', 'warning');
            return;
        }

        const personObj = this.persons.find(p => String(p.id) === String(personId));
        const personName = personObj ? personObj.name : 'Target Person';

        const btn = document.getElementById('btnExecuteAssign');
        if (btn) { btn.disabled = true; btn.innerHTML = '<span>Assigning...</span>'; }

        try {
            const resp = await fetch('/api/villages/assign', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    village_ids: Array.from(this.selectedUnassignedIds),
                    person_id: parseInt(personId)
                })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast(`Successfully assigned ${data.assigned_count} villages to ${personName}!`, 'success');
            
            // Clear selection
            this.selectedUnassignedIds.clear();
            const selectAllCb = document.getElementById('unassignedSelectAllCheckbox');
            if (selectAllCb) selectAllCb.checked = false;
            this.updateUnassignedSelectedBadge();

            // Synchronize views & live KPIs
            await Promise.all([
                this.loadPersons(),
                this.loadUnassignedVillages(),
                this.loadAssignedVillages(),
                DashboardManager.load()
            ]);
        } catch (e) {
            App.toast(`Assignment failed: ${e.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.innerHTML = '<i data-lucide="check"></i><span>Assign Villages</span>'; lucide.createIcons(); }
        }
    },

    async loadAssignedVillages() {
        const personFilter = document.getElementById('assignedPersonFilter')?.value || '';
        const zone = document.getElementById('assignedZoneFilter')?.value || '';
        const district = document.getElementById('assignedDistrictFilter')?.value || '';
        const subdistrict = document.getElementById('assignedSubdistrictFilter')?.value || '';
        const search = document.getElementById('assignedSearchInput')?.value || '';

        const params = new URLSearchParams({
            page: this.assignedPage,
            page_size: this.assignedPageSize,
            search,
            zone,
            district,
            subdistrict
        });
        if (personFilter) params.append('person_id', personFilter);

        try {
            const resp = await fetch(`/api/villages/assigned?${params.toString()}`);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.assignedTotalPages = data.total_pages || 1;

            const countBadge = document.getElementById('tabAssignedCount');
            if (countBadge) countBadge.textContent = (data.total_count || 0).toLocaleString();

            const kpiEl = document.getElementById('assignKpiAssigned');
            if (kpiEl) kpiEl.textContent = (data.total_count || 0).toLocaleString();

            const infoEl = document.getElementById('assignedPaginationInfo');
            if (infoEl) {
                const start = Math.min((this.assignedPage - 1) * this.assignedPageSize + 1, data.total_count);
                const end = Math.min(this.assignedPage * this.assignedPageSize, data.total_count);
                infoEl.textContent = `Showing ${start}-${end} of ${data.total_count} assigned villages`;
            }

            this.renderAssignedTable(data.items || []);
        } catch (e) {
            console.error('Error loading assigned villages:', e);
            App.toast('Failed to load assigned villages.', 'error');
        }
    },

    renderAssignedTable(items) {
        const tbody = document.getElementById('assignedVillagesTableBody');
        if (!tbody) return;

        if (items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 32px; color: #94a3b8;">No assigned villages found.</td></tr>';
            return;
        }

        tbody.innerHTML = items.map(v => {
            const isChecked = this.selectedAssignedIds.has(v.id) ? 'checked' : '';
            const assignedDate = v.assigned_at ? new Date(v.assigned_at).toLocaleDateString() : 'Recent';
            const isDone = (v.work_status === 'Done' || v.kml_status === 'Done');
            const statusBadge = isDone 
                ? `<span class="badge" style="background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; font-weight: 700; display: inline-flex; align-items: center; gap: 4px;">
                     <i data-lucide="check-circle-2" style="width: 12px; height: 12px;"></i> Done
                   </span>
                   <div style="font-size: 0.72rem; color: #059669; margin-top: 2px;">Completed by ${v.assigned_person_name || 'User'}</div>
                   ${v.updated_at ? `<div style="font-size: 0.70rem; color: #64748b;">${new Date(v.updated_at).toLocaleString()}</div>` : ''}`
                : `<span class="badge" style="background: #fef3c7; color: #92400e; border: 1px solid #fde68a; font-weight: 600;">Pending</span>
                   <div style="font-size: 0.72rem; color: #64748b; margin-top: 2px;">In Progress</div>`;

            return `
                <tr>
                    <td>
                        <input type="checkbox" class="assigned-row-cb" value="${v.id}" ${isChecked} onchange="PersonManager.toggleAssignedRow(${v.id}, this.checked)">
                    </td>
                    <td><strong>${v.village_name}</strong></td>
                    <td><code>${v.village_code}</code></td>
                    <td>${v.district_name || ''}</td>
                    <td>${v.subdistrict_name || ''}</td>
                    <td>${v.zone || ''}</td>
                    <td>
                        <span style="font-weight: 600; color: #1e293b;">
                            <i data-lucide="user" style="width: 12px; height: 12px; vertical-align: middle;"></i>
                            ${v.assigned_person_name || 'Assigned'}
                        </span>
                    </td>
                    <td style="color: #64748b; font-size: 0.8rem;">${assignedDate}</td>
                    <td>${statusBadge}</td>
                    <td style="text-align: right; white-space: nowrap;">
                        <button class="btn btn-outline-danger btn-sm" style="padding: 3px 8px; font-size: 0.75rem;" onclick="PersonManager.unassignSingleVillage(${v.id}, '${escapeQuotes(v.village_name)}')" title="Unassign from Surveyor">
                            <i data-lucide="user-minus" style="width: 12px; height: 12px;"></i> Unassign
                        </button>
                        <button class="btn btn-outline btn-xs" style="color: #ef4444; border-color: #fca5a5; padding: 3px 7px; margin-left: 4px;" onclick="PersonManager.confirmDeleteVillage(${v.id}, '${escapeQuotes(v.village_name)}', '${escapeQuotes(v.village_code)}')" title="Remove Village">
                            <i data-lucide="trash-2" style="width: 13px; height: 13px;"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
        lucide.createIcons();
    },

    toggleAssignedRow(id, isChecked) {
        if (isChecked) this.selectedAssignedIds.add(id);
        else this.selectedAssignedIds.delete(id);
        this.updateAssignedSelectedBadge();
    },

    toggleSelectAllAssigned(checked) {
        document.querySelectorAll('.assigned-row-cb').forEach(cb => {
            cb.checked = checked;
            const id = parseInt(cb.value);
            if (checked) this.selectedAssignedIds.add(id);
            else this.selectedAssignedIds.delete(id);
        });
        this.updateAssignedSelectedBadge();
    },

    updateAssignedSelectedBadge() {
        const badge = document.getElementById('assignedSelectedBadge');
        if (badge) badge.textContent = `${this.selectedAssignedIds.size} Selected`;
    },

    onAssignedPersonFilterChange() {
        this.assignedPage = 1;
        this.loadAssignedVillages();
    },

    filterByPerson(personId, personName) {
        const filterSelect = document.getElementById('assignedPersonFilter');
        if (filterSelect) filterSelect.value = String(personId);
        this.switchTab('assigned');
        this.assignedPage = 1;
        this.loadAssignedVillages();
        App.toast(`Filtered villages assigned to ${personName}`, 'info');
    },

    async unassignSingleVillage(villageId, villageName) {
        if (!confirm(`Are you sure you want to unassign village "${villageName}"? It will return to Pending status.`)) return;

        try {
            const resp = await fetch('/api/villages/unassign', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ village_ids: [villageId] })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast(`Village "${villageName}" unassigned and returned to Pending.`, 'success');

            await Promise.all([
                this.loadPersons(),
                this.loadUnassignedVillages(),
                this.loadAssignedVillages(),
                DashboardManager.load()
            ]);
        } catch (e) {
            App.toast(`Unassign failed: ${e.message}`, 'error');
        }
    },

    async unassignSelectedVillages() {
        if (this.selectedAssignedIds.size === 0) {
            App.toast('Please select at least one assigned village to unassign.', 'warning');
            return;
        }

        if (!confirm(`Are you sure you want to unassign ${this.selectedAssignedIds.size} selected village(s)? They will return to Pending status.`)) return;

        try {
            const resp = await fetch('/api/villages/unassign', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ village_ids: Array.from(this.selectedAssignedIds) })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast(`Successfully unassigned ${data.unassigned_count} villages!`, 'success');

            this.selectedAssignedIds.clear();
            const selectAllCb = document.getElementById('assignedSelectAllCheckbox');
            if (selectAllCb) selectAllCb.checked = false;
            this.updateAssignedSelectedBadge();

            await Promise.all([
                this.loadPersons(),
                this.loadUnassignedVillages(),
                this.loadAssignedVillages(),
                DashboardManager.load()
            ]);
        } catch (e) {
            App.toast(`Unassign failed: ${e.message}`, 'error');
        }
    },

    openAddModal() {
        document.getElementById('newPersonName').value = '';
        document.getElementById('newPersonRole').value = 'Field Surveyor';
        document.getElementById('newPersonEmail').value = '';
        document.getElementById('newPersonPhone').value = '';
        document.getElementById('newPersonNotes').value = '';
        App.openModal('personAddModal');
    },

    async submitAddPerson(e) {
        e.preventDefault();
        const name = document.getElementById('newPersonName').value.trim();
        const role = document.getElementById('newPersonRole').value.trim() || 'Field Surveyor';
        const email = document.getElementById('newPersonEmail').value.trim();
        const phone = document.getElementById('newPersonPhone').value.trim();
        const notes = document.getElementById('newPersonNotes').value.trim();

        if (!name) {
            App.toast('Person name is required.', 'warning');
            return;
        }

        const btn = document.getElementById('btnSubmitAddPerson');
        if (btn) btn.disabled = true;

        try {
            const resp = await fetch('/api/persons', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, role, email, phone, notes })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast(`Person "${name}" successfully added!`, 'success');
            App.closeModal('personAddModal');
            await this.loadPersons();
            await DashboardManager.load();
        } catch (err) {
            App.toast(`Failed to add person: ${err.message}`, 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    },

    async deletePerson(personId, personName) {
        if (!confirm(`Are you sure you want to remove person "${personName}"?\nAll villages assigned to this person will automatically return to Pending status.`)) return;

        try {
            const resp = await fetch(`/api/persons/${personId}`, { method: 'DELETE' });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast(`Person "${personName}" removed. ${data.unassigned_villages_count || 0} villages unassigned.`, 'success');
            await Promise.all([
                this.loadPersons(),
                this.loadUnassignedVillages(),
                this.loadAssignedVillages(),
                DashboardManager.load()
            ]);
        } catch (e) {
            App.toast(`Failed to remove person: ${e.message}`, 'error');
        }
    },

    exportPerson(personId) {
        App.toast('Generating person-specific Excel export...', 'info');
        window.location.href = `/api/export/excel?person_id=${personId}`;
    },

    exportAllPersons() {
        App.toast('Generating all assigned persons Excel export...', 'info');
        window.location.href = `/api/export/excel?export_type=all_persons`;
    },

    prevUnassignedPage() {
        if (this.unassignedPage > 1) {
            this.unassignedPage--;
            this.loadUnassignedVillages();
        }
    },

    nextUnassignedPage() {
        if (this.unassignedPage < this.unassignedTotalPages) {
            this.unassignedPage++;
            this.loadUnassignedVillages();
        }
    },

    prevAssignedPage() {
        if (this.assignedPage > 1) {
            this.assignedPage--;
            this.loadAssignedVillages();
        }
    },

    nextAssignedPage() {
        if (this.assignedPage < this.assignedTotalPages) {
            this.assignedPage++;
            this.loadAssignedVillages();
        }
    }
};

/* =========================================================================
   6. EXCEL EXPORT
   ========================================================================= */
const ExportManager = {
    init() {
        const btn = document.getElementById('triggerExportBtn');
        if (btn) btn.onclick = () => this.download();

        // Listen for scope radio changes to toggle Person dropdown
        document.querySelectorAll('input[name="exportScope"]').forEach(radio => {
            radio.addEventListener('change', (e) => {
                const personRow = document.getElementById('exportPersonRow');
                if (personRow) {
                    personRow.style.display = (e.target.value === 'person') ? 'block' : 'none';
                }
            });
        });

        // Load persons for export selector
        fetch('/api/persons').then(r => r.json()).then(d => {
            if (d.success) {
                const sel = document.getElementById('exportPersonSelect');
                if (sel) {
                    sel.innerHTML = '<option value="">-- Choose Person --</option>' +
                        (d.persons || []).map(p => `<option value="${p.id}">${p.name} (${p.assigned_count || 0} villages)</option>`).join('');
                }
            }
        });

        // Populate district & subdistrict dropdowns
        fetch('/api/villages/filters').then(r => r.json()).then(d => {
            if (d.success) {
                const distSel = document.getElementById('exportDistrictSelect');
                if (distSel) {
                    distSel.innerHTML = '<option value="">All Districts</option>' + 
                        d.districts.map(dist => `<option value="${dist}">${dist}</option>`).join('');
                }
                const subSel = document.getElementById('exportSubdistrictSelect');
                if (subSel) {
                    subSel.innerHTML = '<option value="">All Subdistricts</option>' + 
                        d.subdistricts.map(s => `<option value="${s}">${s}</option>`).join('');
                }
                const zoneSel = document.getElementById('exportZoneSelect');
                if (zoneSel && d.zones) {
                    zoneSel.innerHTML = '<option value="">All Zones</option>' +
                        d.zones.map(z => `<option value="${z}">${z}</option>`).join('');
                }
            }
        });
    },

    download() {
        const scope = document.querySelector('input[name="exportScope"]:checked')?.value || 'all';
        const zone = document.getElementById('exportZoneSelect')?.value || '';
        const district = document.getElementById('exportDistrictSelect')?.value || '';
        const subdistrict = document.getElementById('exportSubdistrictSelect')?.value || '';

        const params = new URLSearchParams();
        if (scope === 'completed') params.append('status', 'completed');
        else if (scope === 'pending') params.append('status', 'pending');
        else if (scope === 'review') params.append('status', 'needs review');
        else if (scope === 'person') {
            const pId = document.getElementById('exportPersonSelect')?.value;
            if (!pId) {
                App.toast('Please choose a person to export.', 'warning');
                return;
            }
            params.append('person_id', pId);
        } else if (scope === 'all_persons') {
            params.append('export_type', 'all_persons');
        }

        if (zone) params.append('zone', zone);
        if (district) params.append('district', district);
        if (subdistrict) params.append('subdistrict', subdistrict);

        App.toast('Generating Excel file (.xlsx)...', 'info');
        window.location.href = `/api/export/excel?${params.toString()}`;
    }
};

/* =========================================================================
   7. IMPORT HISTORY
   ========================================================================= */
const HistoryManager = {
    async load() {
        try {
            const resp = await fetch('/api/import/history');
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.renderTable(data.batches);
        } catch (e) {
            App.toast('Could not load import history.', 'error');
        }
    },

    renderTable(batches) {
        const tbody = document.getElementById('importHistoryTable');
        if (!tbody) return;

        if (!batches || batches.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 36px; color: #94a3b8;">No import history recorded yet.</td></tr>';
            return;
        }

        tbody.innerHTML = batches.map(b => {
            const errBtn = b.invalid_rows > 0 && b.error_report_name
                ? `<a href="/api/import/errors/${b.error_report_name}" class="btn btn-danger btn-sm"><i data-lucide="download"></i> Errors (${b.invalid_rows})</a>`
                : `<span style="color:#10b981; font-size:0.8rem;">Clean (0 errors)</span>`;

            return `
                <tr>
                    <td>#${b.id}</td>
                    <td><strong>${b.filename}</strong></td>
                    <td>${b.created_at ? b.created_at.split('T')[0] : ''}</td>
                    <td>${b.total_rows}</td>
                    <td><span style="color:#166534; font-weight:600;">${b.valid_rows}</span></td>
                    <td><span style="color:#dc2626; font-weight:600;">${b.invalid_rows}</span></td>
                    <td>${b.duplicate_rows}</td>
                    <td><span class="badge badge-verified">${b.status}</span></td>
                    <td>${errBtn}</td>
                </tr>
            `;
        }).join('');
        lucide.createIcons();
    }
};

/* =========================================================================
   8. SETTINGS & DIAGNOSTICS
   ========================================================================= */
const SettingsManager = {
    async load() {
        try {
            const resp = await fetch('/api/settings');
<<<<<<< HEAD
            if (!resp.ok) {
                const errData = await resp.json().catch(() => ({}));
                throw new Error(errData.error || `HTTP ${resp.status}`);
            }
            const data = await resp.json();
            if (!data.success) throw new Error(data.error || 'API returned unsuccessful response');

            const h = data.db_health || {};
            const diagStatus = document.getElementById('diagStatus');
            if (diagStatus) {
                diagStatus.textContent = h.connected ? 'Healthy / Active' : 'Disconnected';
                diagStatus.style.color = h.connected ? '#166534' : '#dc2626';
            }
            const diagDriver = document.getElementById('diagDriver');
            if (diagDriver) diagDriver.textContent = h.driver || 'Auto';
            const diagDbName = document.getElementById('diagDbName');
            if (diagDbName) diagDbName.textContent = h.database || 'BorewellPortalDB';
            const diagTime = document.getElementById('diagTime');
            if (diagTime) diagTime.textContent = h.server_time || '-';
            const diagVersion = document.getElementById('diagVersion');
            if (diagVersion) diagVersion.textContent = h.version_summary || '-';

            const settings = data.settings || {};
            const markingUrlInput = document.getElementById('markingPortalUrlInput');
            if (markingUrlInput && settings.marking_portal_url !== undefined) {
                markingUrlInput.value = settings.marking_portal_url;
            }
        } catch (e) {
            console.error('SettingsManager.load failed:', e);
=======
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            const h = data.db_health || {};
            document.getElementById('diagStatus').textContent = h.connected ? 'Healthy / Active' : 'Disconnected';
            document.getElementById('diagStatus').style.color = h.connected ? '#166534' : '#dc2626';
            document.getElementById('diagDriver').textContent = h.driver || 'Auto';
            document.getElementById('diagDbName').textContent = h.database || 'BorewellPortalDB';
            document.getElementById('diagTime').textContent = h.server_time || '-';
            document.getElementById('diagVersion').textContent = h.version_summary || '-';

            const settings = data.settings || {};
            if (settings.marking_portal_url) {
                document.getElementById('markingPortalUrlInput').value = settings.marking_portal_url;
            }
        } catch (e) {
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            App.toast('Failed to load settings.', 'error');
        }
    },

    init() {
        document.getElementById('refreshDbHealthBtn')?.addEventListener('click', () => {
            this.load();
            App.toast('System status refreshed.', 'info');
        });

        document.getElementById('settingsForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const portalUrl = document.getElementById('markingPortalUrlInput').value.trim();

            try {
                const resp = await fetch('/api/settings', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ marking_portal_url: portalUrl })
                });
                const d = await resp.json();
                if (d.success) App.toast('Settings updated successfully!', 'success');
                else throw new Error(d.error);
            } catch (err) {
                App.toast(`Failed to save settings: ${err.message}`, 'error');
            }
        });

        document.getElementById('changePasswordForm')?.addEventListener('submit', async (e) => {
            e.preventDefault();
            const old_password = document.getElementById('currPassword').value;
            const new_password = document.getElementById('newPassword').value;
<<<<<<< HEAD
            const confirm_password = document.getElementById('confirmNewPassword')?.value;

            if (confirm_password !== undefined && new_password !== confirm_password) {
                App.toast('New password and confirm password do not match.', 'warning');
                return;
            }
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

            try {
                const resp = await fetch('/api/auth/change-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
<<<<<<< HEAD
                    body: JSON.stringify({ old_password, new_password, confirm_password })
=======
                    body: JSON.stringify({ old_password, new_password })
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
                });
                const d = await resp.json();
                if (d.success) {
                    App.toast('Password changed successfully!', 'success');
                    document.getElementById('currPassword').value = '';
                    document.getElementById('newPassword').value = '';
<<<<<<< HEAD
                    if (document.getElementById('confirmNewPassword')) {
                        document.getElementById('confirmNewPassword').value = '';
                    }
                    if (window.PasswordVisibility) {
                        PasswordVisibility.reset('currPassword');
                        PasswordVisibility.reset('newPassword');
                        PasswordVisibility.reset('confirmNewPassword');
                    }
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
                } else {
                    throw new Error(d.error);
                }
            } catch (err) {
                App.toast(`Password update failed: ${err.message}`, 'error');
            }
        });
    }
};

/* =========================================================================
   GIS LEAFLET MAP HELPER FUNCTIONS
   ========================================================================= */
function renderLeafletMap(containerId, geojson, bounds) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Destroy prior map instance on this container if exists
    if (App.mapInstances[containerId]) {
        App.mapInstances[containerId].remove();
        delete App.mapInstances[containerId];
    }

    const map = L.map(containerId).setView([23.0, 72.5], 11);
    App.mapInstances[containerId] = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    if (geojson && geojson.features && geojson.features.length > 0) {
        const layer = L.geoJSON(geojson, {
            pointToLayer: (feature, latlng) => {
                const isBore = feature.properties.candidate_type === 'Borewell';
                return L.circleMarker(latlng, {
                    radius: 7,
                    fillColor: isBore ? '#2563eb' : '#10b981',
                    color: '#ffffff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.9
                });
            },
            style: (feature) => {
                return {
                    color: '#2563eb',
                    weight: 3,
                    fillColor: '#3b82f6',
                    fillOpacity: 0.2
                };
            },
            onEachFeature: (feature, layer) => {
                const p = feature.properties || {};
                layer.bindPopup(`
                    <div style="font-family:sans-serif; font-size:12px;">
                        <strong style="color:#0f172a;">${p.name || 'Placemark'}</strong><br>
                        <span style="color:#64748b;">Type: ${p.candidate_type || p.geometry_type}</span>
                        ${p.description ? `<p style="margin-top:4px;color:#334155;">${p.description}</p>` : ''}
                    </div>
                `);
            }
        }).addTo(map);

        map.fitBounds(layer.getBounds(), { padding: [30, 30] });
    } else if (bounds && bounds.length === 4) {
        map.fitBounds([[bounds[0], bounds[1]], [bounds[2], bounds[3]]]);
    }

    setTimeout(() => map.invalidateSize(), 150);
}

function resetLeafletMap(containerId) {
    if (App.mapInstances[containerId]) {
        App.mapInstances[containerId].remove();
        delete App.mapInstances[containerId];
    }
    const container = document.getElementById(containerId);
    if (container) {
        const map = L.map(containerId).setView([23.0, 72.5], 6);
        App.mapInstances[containerId] = map;
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap'
        }).addTo(map);
        setTimeout(() => map.invalidateSize(), 150);
    }
}

/* =========================================================================
   8. VILLAGE AUTOMATION WORKFLOW MANAGER
   ========================================================================= */
const AutomationManager = {
    selectedFile: null,
    pollTimer: null,
    currentJobId: null,

    init() {
        const dropzone = document.getElementById('automationDropzone');
        const fileInput = document.getElementById('automationFileInput');
        const startBtn = document.getElementById('autoStartBtn');
        const pauseBtn = document.getElementById('autoPauseBtn');
        const resumeBtn = document.getElementById('autoResumeBtn');
        const stopBtn = document.getElementById('autoStopBtn');
        const downloadBtn = document.getElementById('autoDownloadBtn');

        if (!dropzone || !fileInput) return;

        dropzone.addEventListener('click', () => fileInput.click());
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('drag-over');
        });
        dropzone.addEventListener('dragleave', () => dropzone.classList.remove('drag-over'));
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('drag-over');
            if (e.dataTransfer.files.length) {
                this.handleFileSelected(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                this.handleFileSelected(e.target.files[0]);
            }
        });

        startBtn?.addEventListener('click', () => this.startAutomation());
        pauseBtn?.addEventListener('click', () => this.pauseAutomation());
        resumeBtn?.addEventListener('click', () => this.resumeAutomation());
        stopBtn?.addEventListener('click', () => this.stopAutomation());
        downloadBtn?.addEventListener('click', () => this.downloadOutputExcel());
    },

    handleFileSelected(file) {
        this.selectedFile = file;
        const box = document.getElementById('automationSelectedFileBox');
        const nameEl = document.getElementById('autoSelectedFileName');
        const sizeEl = document.getElementById('autoSelectedFileSize');
        const startBtn = document.getElementById('autoStartBtn');

        if (box && nameEl && sizeEl) {
            nameEl.textContent = file.name;
            sizeEl.textContent = `${(file.size / 1024).toFixed(1)} KB`;
            box.style.display = 'block';
        }
        if (startBtn) startBtn.disabled = false;
        App.toast(`File selected: ${file.name}`, 'info');
    },

    async load() {
        await this.checkStatus();
    },

    async startAutomation() {
        if (!this.selectedFile) {
            App.toast('Please select an Excel file first.', 'warning');
            return;
        }

        const startBtn = document.getElementById('autoStartBtn');
        const pauseBtn = document.getElementById('autoPauseBtn');
        const resumeBtn = document.getElementById('autoResumeBtn');
        const stopBtn = document.getElementById('autoStopBtn');
        const workersSelect = document.getElementById('autoWorkersSelect');
        if (startBtn) startBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', this.selectedFile);
        if (workersSelect) {
            formData.append('concurrency', workersSelect.value);
        }
        const reviewCorrectCheck = document.getElementById('autoReviewCorrectCheck');
        if (reviewCorrectCheck) {
            formData.append('auto_review_correct', reviewCorrectCheck.checked ? 'true' : 'false');
        }

        try {
            App.toast('Starting automation workflow...', 'info');
            const resp = await fetch('/api/automation/start', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();

            if (!data.success) throw new Error(data.error || 'Failed to start automation');

            this.currentJobId = data.data.job_id;
            App.toast(`Automation started for ${data.data.total_villages} villages with ${data.data.workers_count || 3} workers.`, 'success');

            if (startBtn) startBtn.style.display = 'none';
            if (pauseBtn) {
                pauseBtn.style.display = 'inline-flex';
                pauseBtn.disabled = false;
            }
            if (resumeBtn) resumeBtn.style.display = 'none';
            if (stopBtn) {
                stopBtn.style.display = 'inline-flex';
                stopBtn.disabled = false;
            }

            this.startPolling();
        } catch (err) {
            App.toast(`Failed to start: ${err.message}`, 'error');
            if (startBtn) startBtn.disabled = false;
        }
    },

    async pauseAutomation() {
        const pauseBtn = document.getElementById('autoPauseBtn');
        if (pauseBtn) pauseBtn.disabled = true;

        try {
            App.toast('Pausing automation...', 'info');
            const resp = await fetch('/api/automation/pause', { method: 'POST' });
            const data = await resp.json();
            if (data.success) {
                App.toast('Automation PAUSED. In-progress generation will complete safely.', 'warning');
                await this.checkStatus();
            } else {
                App.toast(data.error || 'Failed to pause automation', 'error');
            }
        } catch (err) {
            App.toast(`Error pausing: ${err.message}`, 'error');
        } finally {
            if (pauseBtn) pauseBtn.disabled = false;
        }
    },

    async resumeAutomation() {
        const resumeBtn = document.getElementById('autoResumeBtn');
        if (resumeBtn) resumeBtn.disabled = true;

        try {
            App.toast('Resuming automation...', 'info');
            const resp = await fetch('/api/automation/resume', { method: 'POST' });
            const data = await resp.json();
            if (data.success) {
                App.toast('Automation RESUMED at maximum speed.', 'success');
                if (!this.pollTimer) this.startPolling();
                await this.checkStatus();
            } else {
                App.toast(data.error || 'Failed to resume automation', 'error');
            }
        } catch (err) {
            App.toast(`Error resuming: ${err.message}`, 'error');
        } finally {
            if (resumeBtn) resumeBtn.disabled = false;
        }
    },

    async stopAutomation() {
        const stopBtn = document.getElementById('autoStopBtn');
        if (stopBtn) stopBtn.disabled = true;

        try {
            const resp = await fetch('/api/automation/stop', { method: 'POST' });
            const data = await resp.json();
            if (data.success) {
                App.toast('Stop signal sent. Halting after current village...', 'info');
            } else {
                App.toast(data.error, 'error');
            }
        } catch (err) {
            App.toast(`Error stopping: ${err.message}`, 'error');
        }
    },

    startPolling() {
        if (this.pollTimer) clearInterval(this.pollTimer);
        this.pollTimer = setInterval(() => this.checkStatus(), 1500);
        this.checkStatus();
    },

    stopPolling() {
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    },

    async checkStatus() {
        try {
            const resp = await fetch('/api/automation/status');
            const data = await resp.json();
            if (!data.success) return;

            const st = data.data;
            this.renderStatus(st);

            if (st.status === 'running' || st.status === 'paused') {
                if (!this.pollTimer) this.startPolling();
            } else {
                if (st.status === 'completed' || st.status === 'stopped' || st.status === 'failed') {
                    this.stopPolling();
                }
            }
        } catch (err) {
            console.error('Error fetching automation status:', err);
        }
    },

    renderStatus(st) {
        if (st.job_id) this.currentJobId = st.job_id;

        // Metric cards (9 KPIs: Total, Processed, Remaining, Successful, Failed, Workers, Avg Speed, Throughput, ETA)
        const totalEl = document.getElementById('autoStatTotal');
        const compEl = document.getElementById('autoStatCompleted');
        const procEl = document.getElementById('autoStatProcessed') || document.getElementById('autoStatProcessing');
        const failEl = document.getElementById('autoStatFailed');
        const remEl = document.getElementById('autoStatRemaining');
        const workersEl = document.getElementById('autoStatWorkers');
        const speedEl = document.getElementById('autoAvgSpeed');
        const throughputEl = document.getElementById('autoStatThroughput');
        const etaEl = document.getElementById('autoStatEta');

        const processedCount = (st.processed_count !== undefined) ? st.processed_count : ((st.completed_count || 0) + (st.failed_count || 0));
        const remCount = (st.remaining_count !== undefined) ? st.remaining_count : Math.max(0, (st.total_villages || 0) - (st.completed_count || 0) - (st.failed_count || 0));

        if (totalEl) totalEl.textContent = st.total_villages || 0;
        if (procEl) procEl.textContent = processedCount;
        if (compEl) compEl.textContent = st.completed_count || 0;
        if (failEl) failEl.textContent = st.failed_count || 0;
        if (remEl) remEl.textContent = remCount;
        if (workersEl) workersEl.textContent = st.workers_count || 5;
        if (speedEl) {
            const spd = st.avg_speed_seconds;
            speedEl.textContent = (spd !== undefined && spd > 0) ? `${spd}s/vil` : '-';
        }
        if (throughputEl) {
            if (st.throughput_str && st.throughput_str !== '-') {
                throughputEl.textContent = st.throughput_str;
            } else if (st.throughput_vpm && st.throughput_vpm > 0) {
                throughputEl.textContent = `${st.throughput_vpm} vil/m`;
            } else {
                throughputEl.textContent = '-';
            }
        }
        if (etaEl) {
            etaEl.textContent = st.estimated_remaining_time || '-';
        }

        // Current village & status
        const vEl = document.getElementById('autoCurrentVillage');
        const sEl = document.getElementById('autoCurrentStatus');
        if (vEl) vEl.textContent = st.current_village || (st.status === 'completed' ? 'All Villages Completed' : '-');
        if (sEl) sEl.textContent = st.current_status || 'Ready';

        // Progress bar & count
        const pct = st.progress_percentage || 0;
        const barEl = document.getElementById('autoProgressBar');
        const pctEl = document.getElementById('autoProgressPct');
        const countEl = document.getElementById('autoProgressCount');
        if (barEl) barEl.style.width = `${pct}%`;
        if (pctEl) pctEl.textContent = `${pct}%`;
        if (countEl) countEl.textContent = `${processedCount} / ${st.total_villages || 0}`;

        // Badge
        const badge = document.getElementById('autoStatusBadge');
        if (badge) {
            if (st.status === 'running') {
                badge.className = 'badge badge-inprogress';
                badge.textContent = 'RUNNING';
            } else if (st.status === 'paused') {
                badge.className = 'badge badge-paused';
                badge.textContent = 'PAUSED';
            } else if (st.status === 'completed') {
                badge.className = 'badge badge-done';
                badge.textContent = 'COMPLETED';
            } else if (st.status === 'stopped') {
                badge.className = 'badge badge-pending';
                badge.textContent = 'STOPPED';
            } else if (st.status === 'failed') {
                badge.className = 'badge badge-failed';
                badge.textContent = 'FAILED';
            } else {
                badge.className = 'badge badge-pending';
                badge.textContent = 'IDLE';
            }
        }

        // Action Buttons: START, PAUSE, RESUME, STOP
        const startBtn = document.getElementById('autoStartBtn');
        const pauseBtn = document.getElementById('autoPauseBtn');
        const resumeBtn = document.getElementById('autoResumeBtn');
        const stopBtn = document.getElementById('autoStopBtn');
        const downloadBtn = document.getElementById('autoDownloadBtn');

        if (st.status === 'running') {
            if (startBtn) startBtn.style.display = 'none';
            if (pauseBtn) {
                pauseBtn.style.display = 'inline-flex';
                pauseBtn.disabled = false;
            }
            if (resumeBtn) resumeBtn.style.display = 'none';
            if (stopBtn) {
                stopBtn.style.display = 'inline-flex';
                stopBtn.disabled = false;
            }
        } else if (st.status === 'paused') {
            if (startBtn) startBtn.style.display = 'none';
            if (pauseBtn) pauseBtn.style.display = 'none';
            if (resumeBtn) {
                resumeBtn.style.display = 'inline-flex';
                resumeBtn.disabled = false;
            }
            if (stopBtn) {
                stopBtn.style.display = 'inline-flex';
                stopBtn.disabled = false;
            }
        } else {
            // idle, completed, stopped, failed
            if (startBtn) {
                startBtn.style.display = 'inline-flex';
                startBtn.disabled = !this.selectedFile;
            }
            if (pauseBtn) pauseBtn.style.display = 'none';
            if (resumeBtn) resumeBtn.style.display = 'none';
            if (stopBtn) stopBtn.style.display = 'none';
        }

        if (downloadBtn) {
            downloadBtn.disabled = !st.output_ready && (!st.results || st.results.length === 0);
        }

        // Results table
        this.renderResultsTable(st.results || []);
    },

    renderResultsTable(results) {
        const tbody = document.getElementById('autoResultsTableBody');
        if (!tbody) return;

        if (!results || results.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" style="text-align: center; color: #94a3b8; padding: 24px;">
                        No village links generated yet. Upload an Excel file above and click "START GENERATION".
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = results.map((r, idx) => {
            const rawStatus = (r.status || '').toUpperCase();
            const isSuccess = rawStatus.includes('SUCCESS');
            const isSkipped = rawStatus.includes('SKIP');
            const badgeClass = isSuccess ? 'badge-done' : (isSkipped ? 'badge-pending' : 'badge-failed');
            const pageLink = r.generated_link || r.generated_page_link || r.review_url || r.kpi_link;
            const pageLinkHtml = (isSuccess && pageLink && pageLink.startsWith('http')) 
                ? `<a href="${pageLink}" target="_blank" rel="noopener noreferrer" style="color: #2563eb; font-weight: 500; text-decoration: underline; word-break: break-all; display: inline-flex; align-items: center; gap: 4px;"><i data-lucide="external-link" style="width: 14px; height: 14px; flex-shrink: 0;"></i><span>${pageLink}</span></a>`
                : `<span style="color: #94a3b8;">-</span>`;
            const villageCodeText = r.village_code ? `<code style="background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: 0.82rem; color: #334155;">${r.village_code}</code>` : `<span style="color: #94a3b8;">-</span>`;

            return `
                <tr>
                    <td style="color: #64748b; font-weight: 500;">${idx + 1}</td>
                    <td style="font-weight: 600; color: #1e293b;">${r.village_name}</td>
                    <td>${villageCodeText}</td>
                    <td>${pageLinkHtml}</td>
                    <td><span class="badge ${badgeClass}">${r.status || (isSuccess ? 'SUCCESS' : 'FAILED')}</span></td>
                    <td style="font-size: 0.82rem; color: ${isSuccess ? '#166534' : '#b91c1c'};">${r.error || r.message || (isSuccess ? 'Generated successfully' : '')}</td>
                </tr>
            `;
        }).join('');

        if (window.lucide) {
            lucide.createIcons();
        }
    },

    downloadOutputExcel() {
        if (!this.currentJobId) {
            App.toast('No output file available yet.', 'warning');
            return;
        }
        window.location.href = `/api/automation/download/${this.currentJobId}`;
    }
};

const UserSettingsManager = {
    users: [],

    async load() {
        const tbody = document.getElementById('userTableBody');
        if (!tbody) return;
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #94a3b8; padding: 24px;">Loading users...</td></tr>';

        try {
            const resp = await fetch('/api/admin/users');
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.users = data.data || [];
            this.renderTable();
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #ef4444; padding: 20px;">Error loading users: ${err.message}</td></tr>`;
        }
    },

    renderTable() {
        const tbody = document.getElementById('userTableBody');
        if (!tbody) return;

        if (!this.users.length) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #94a3b8; padding: 24px;">No users found. Click "Add User" above.</td></tr>';
            return;
        }

        tbody.innerHTML = this.users.map((u, idx) => {
            const isAdmin = u.role === 'admin';
            const roleBadge = isAdmin 
                ? '<span class="badge" style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe;">Administrator</span>'
                : '<span class="badge" style="background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0;">Field Surveyor</span>';
            const statusBadge = u.is_active 
                ? '<span class="badge" style="background: #ecfdf5; color: #047857;">Active</span>'
                : '<span class="badge" style="background: #fef2f2; color: #b91c1c;">Inactive</span>';
            
            const assignedCount = u.total_assigned_count || 0;
            const assignedText = assignedCount > 0 
                ? `<span class="badge" style="background: #e0e7ff; color: #3730a3; font-weight: 600;">${assignedCount} villages</span>`
                : `<span style="color: #94a3b8; font-size: 0.85rem;">0 villages</span>`;

            const createdDate = u.created_at ? new Date(u.created_at).toLocaleDateString() : '—';

            return `
                <tr>
                    <td style="color: #64748b; font-weight: 500;">${idx + 1}</td>
                    <td style="font-weight: 600; color: #1e293b;">${u.full_name || u.username}</td>
                    <td style="font-family: monospace; color: #475569;">${u.username}</td>
                    <td>${roleBadge}</td>
                    <td>${assignedText}</td>
                    <td>${statusBadge}</td>
                    <td style="font-size: 0.85rem; color: #64748b;">${createdDate}</td>
                    <td style="text-align: right; white-space: nowrap;">
                        <button class="btn btn-outline btn-xs" style="margin-right: 4px;" onclick="UserSettingsManager.openEditModal(${u.id})">
                            <i data-lucide="edit-2" style="width: 13px; height: 13px;"></i> Edit
                        </button>
                        <button class="btn btn-outline btn-xs" style="margin-right: 4px;" onclick="UserSettingsManager.toggleStatus(${u.id}, ${u.is_active})">
                            <i data-lucide="${u.is_active ? 'user-x' : 'user-check'}" style="width: 13px; height: 13px;"></i> ${u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                        ${u.id !== 1 && u.username.toLowerCase() !== 'admin' ? `
                            <button class="btn btn-outline btn-xs" style="color: #ef4444; border-color: #fca5a5;" onclick="UserSettingsManager.deleteUser(${u.id}, '${u.username}')">
                                <i data-lucide="trash-2" style="width: 13px; height: 13px;"></i>
                            </button>
                        ` : ''}
                    </td>
                </tr>
            `;
        }).join('');

        lucide.createIcons();
    },

    openAddModal() {
        document.getElementById('userForm').reset();
        document.getElementById('formUserId').value = '';
        document.getElementById('userModalTitle').textContent = 'Add New User';
        document.getElementById('pwRequiredMarker').style.display = 'inline';
        document.getElementById('formUserPassword').required = true;
        document.getElementById('pwHelpText').textContent = 'Minimum 4 characters. Will be used for user login.';
<<<<<<< HEAD
        if (window.PasswordVisibility) {
            PasswordVisibility.reset('formUserPassword');
        }
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        App.openModal('userAddModal');
    },

    openEditModal(userId) {
        const u = this.users.find(x => x.id === userId);
        if (!u) return;

        document.getElementById('formUserId').value = u.id;
        document.getElementById('formUserFullName').value = u.full_name || '';
        document.getElementById('formUserUsername').value = u.username || '';
        document.getElementById('formUserRole').value = u.role || 'user';
        document.getElementById('formUserActive').value = u.is_active ? '1' : '0';
        document.getElementById('formUserPassword').value = '';
        document.getElementById('formUserPassword').required = false;
        document.getElementById('pwRequiredMarker').style.display = 'none';
        document.getElementById('pwHelpText').textContent = 'Leave blank to keep existing password unchanged.';
        document.getElementById('userModalTitle').textContent = `Edit User: ${u.username}`;
<<<<<<< HEAD
        if (window.PasswordVisibility) {
            PasswordVisibility.reset('formUserPassword');
        }
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

        App.openModal('userAddModal');
    },

    async submitUserForm(e) {
        e.preventDefault();
        const userId = document.getElementById('formUserId').value;
        const fullName = document.getElementById('formUserFullName').value.trim();
        const username = document.getElementById('formUserUsername').value.trim();
        const password = document.getElementById('formUserPassword').value.trim();
        const role = document.getElementById('formUserRole').value;
        const isActive = document.getElementById('formUserActive').value === '1';

        const submitBtn = document.getElementById('btnSubmitUser');
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';

        try {
            const payload = {
                full_name: fullName,
                username: username,
                role: role,
                is_active: isActive
            };
            if (password) payload.password = password;

            let url = '/api/admin/users';
            let method = 'POST';
            if (userId) {
                url = `/api/admin/users/${userId}`;
                method = 'PUT';
            }

            const resp = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const resData = await resp.json();
            if (!resData.success) throw new Error(resData.error);

            App.closeModal('userAddModal');
<<<<<<< HEAD
            if (window.PasswordVisibility) {
                PasswordVisibility.reset('formUserPassword');
            }
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            App.toast(resData.message || 'User saved successfully.', 'success');
            await this.load();
            if (typeof PersonManager !== 'undefined' && PersonManager.load) {
                PersonManager.load(); // keep Assign Person synced
            }
        } catch (err) {
            App.toast(err.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save User';
        }
    },

    async toggleStatus(userId, currentStatus) {
        try {
            const nextStatus = !currentStatus;
            const resp = await fetch(`/api/admin/users/${userId}/toggle-status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: nextStatus })
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast(data.message || 'User status updated.', 'success');
            await this.load();
            if (typeof PersonManager !== 'undefined' && PersonManager.load) {
                PersonManager.load();
            }
        } catch (err) {
            App.toast(err.message, 'error');
        }
    },

    async deleteUser(userId, username) {
        if (!confirm(`Are you sure you want to delete user "${username}"?\nAny villages currently assigned to this user will be unassigned and returned to Pending.`)) {
            return;
        }

        try {
            const resp = await fetch(`/api/admin/users/${userId}`, { method: 'DELETE' });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast(data.message || 'User removed successfully.', 'success');
            await this.load();
            if (typeof PersonManager !== 'undefined' && PersonManager.load) {
                PersonManager.load();
            }
        } catch (err) {
            App.toast(err.message, 'error');
        }
    }
};

const UserWorkManager = {
    villages: [],
<<<<<<< HEAD
    history: [],
    pollTimer: null,
    searchDebounce: null,
    _focusBound: false,
=======
    pollTimer: null,
    searchDebounce: null,
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

    init() {
        this.loadDashboard();
        this.loadAssignedVillages();
<<<<<<< HEAD
        this.loadHistory();
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        // Start background polling every 10 seconds to detect remote completion automatically
        if (this.pollTimer) clearInterval(this.pollTimer);
        this.pollTimer = setInterval(() => {
            this.syncAndCheckCompletions(true);
        }, 10000);
<<<<<<< HEAD

        // Window focus event listener: instant sync when returning from marking portal tab
        if (!this._focusBound) {
            this._focusBound = true;
            window.addEventListener('focus', () => {
                const role = document.body.getAttribute('data-user-role');
                if (role && role !== 'admin') {
                    this.syncAndCheckCompletions(true);
                    this.loadHistory();
                }
            });
        }
    },

    escapeText(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    },

    async loadHistory() {
        const dashList = document.getElementById('userDashboardHistoryList');
        const fullList = document.getElementById('userFullHistoryList');
        const badge = document.getElementById('userDashboardHistoryBadge');

        try {
            const resp = await fetch('/api/user/history');
            const data = await resp.json();
            if (!data.success) return;

            const items = data.items || [];
            this.history = items;

            if (badge) {
                badge.textContent = `${items.length} completed`;
            }

            const renderItemsHtml = (listItems) => {
                if (!listItems.length) {
                    return `
                        <div style="color: #94a3b8; font-size: 0.9rem; padding: 12px 0; text-align: center;">
                            No completed villages yet. Complete village well markings to see your history here.
                        </div>
                    `;
                }

                return listItems.map(item => `
                    <div class="history-item" style="display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; transition: background 0.15s ease;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="width: 7px; height: 7px; border-radius: 50%; background: #10b981; display: inline-block; flex-shrink: 0;"></span>
                            <span style="font-weight: 600; color: #1e293b; font-size: 0.92rem;">${this.escapeText(item.village_name)}</span>
                            <span style="color: #94a3b8; font-weight: 500;">—</span>
                            <span style="color: #475569; font-size: 0.88rem; font-weight: 500;">${this.escapeText(item.completion_date)}</span>
                        </div>
                    </div>
                `).join('');
            };

            if (dashList) {
                dashList.innerHTML = renderItemsHtml(items.slice(0, 10));
            }

            if (fullList) {
                fullList.innerHTML = renderItemsHtml(items);
            }
        } catch (err) {
            console.error('Error loading user history:', err);
            if (dashList && !this.history.length) {
                dashList.innerHTML = `<div style="color: #ef4444; font-size: 0.85rem; padding: 8px 0;">Error loading history: ${err.message}</div>`;
            }
            if (fullList && !this.history.length) {
                fullList.innerHTML = `<div style="color: #ef4444; font-size: 0.85rem; padding: 8px 0;">Error loading history: ${err.message}</div>`;
            }
        }
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    },

    async loadDashboard() {
        try {
            const resp = await fetch('/api/user/metrics');
            const data = await resp.json();
            if (!data.success) return;

            const m = data.data;
            if (document.getElementById('userStatAssigned')) {
                document.getElementById('userStatAssigned').textContent = (m.assigned_villages || 0).toLocaleString();
            }
            if (document.getElementById('userStatPending')) {
                document.getElementById('userStatPending').textContent = (m.pending_villages || 0).toLocaleString();
            }
            if (m.person_name && document.getElementById('userGreetingName')) {
                document.getElementById('userGreetingName').textContent = m.person_name;
            }
        } catch (e) {
            console.error('Error loading user dashboard metrics:', e);
        }
    },

    async loadAssignedVillages() {
        const tbody = document.getElementById('userWorkTableBody');
        if (!tbody) return;

        const searchVal = document.getElementById('userWorkSearchInput') ? document.getElementById('userWorkSearchInput').value.trim() : '';

        try {
            const resp = await fetch(`/api/user/assigned-villages?search=${encodeURIComponent(searchVal)}`);
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            this.villages = data.items || [];
            this.renderTable();
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: #ef4444; padding: 24px;">Error loading assigned villages: ${err.message}</td></tr>`;
        }
    },

    renderTable() {
        const tbody = document.getElementById('userWorkTableBody');
        if (!tbody) return;

        if (!this.villages.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" style="text-align: center; color: #64748b; padding: 36px 20px;">
                        <i data-lucide="check-circle" style="width: 36px; height: 36px; color: #10b981; margin-bottom: 8px; display: inline-block;"></i>
                        <div style="font-weight: 600; font-size: 1rem; color: #1e293b; margin-bottom: 4px;">No Pending Assigned Villages</div>
                        <div style="font-size: 0.85rem; color: #94a3b8;">All assigned villages are completed, or Admin has not assigned any villages to your account yet.</div>
                    </td>
                </tr>
            `;
            lucide.createIcons();
            return;
        }

        tbody.innerHTML = this.villages.map((v, idx) => {
            const dateStr = v.assigned_at ? new Date(v.assigned_at).toLocaleDateString() : '—';
<<<<<<< HEAD
            const isCorrection = (v.work_status === 'Correction Required' || v.kml_status === 'Correction Required');
            let workStatusBadge = '';
            if (isCorrection) {
                workStatusBadge = `
                    <span class="badge" style="background: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; font-weight: 700; display: inline-flex; align-items: center; gap: 3px;">
                        <i data-lucide="alert-circle" style="width: 12px; height: 12px;"></i> Correction Required
                    </span>
                    ${v.correction_reason ? `<div style="font-size: 0.72rem; color: #be123c; margin-top: 3px; max-width: 180px; white-space: normal;" title="${this.escapeText(v.correction_reason)}"><strong>Note:</strong> ${this.escapeText(v.correction_reason)}</div>` : ''}
                `;
            } else {
                workStatusBadge = '<span class="badge" style="background: #fef3c7; color: #92400e; border: 1px solid #fde68a; font-weight: 600;">Not Done</span>';
            }
=======
            const workStatusBadge = '<span class="badge" style="background: #fef3c7; color: #92400e; border: 1px solid #fde68a; font-weight: 600;">Not Done</span>';
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1

            const saveBtnHtml = `
                <button class="btn btn-sm js-save-${v.id}" onclick="UserWorkManager.openSurveyModal(${v.id})" title="Complete survey and save findings" style="padding: 5px 11px; font-size: 0.82rem; background: #10b981; border: 1px solid #059669; color: #ffffff; display: inline-flex; align-items: center; gap: 5px; cursor: pointer; border-radius: 6px;">
                    <i data-lucide="check-circle-2" style="width: 14px; height: 14px;"></i> Save
                </button>
            `;

            let actionHtml = '';
            if (v.generated_review_url) {
                actionHtml = `
                    <div style="display: inline-flex; gap: 6px; align-items: center; justify-content: center;">
                        <a href="${v.generated_review_url}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-primary" style="padding: 5px 12px; font-size: 0.82rem; text-decoration: none; display: inline-flex; align-items: center; gap: 6px;">
                            <i data-lucide="external-link" style="width: 14px; height: 14px;"></i> Open / Review
                        </a>
                        ${saveBtnHtml}
                        <button class="btn btn-sm btn-outline js-check-${v.id}" onclick="UserWorkManager.checkSingle(${v.id}, this)" title="Check if finalized on external portal" style="padding: 5px 8px; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 4px;">
                            <i data-lucide="refresh-cw" style="width: 13px; height: 13px; color: #059669;"></i>
                        </button>
                    </div>
                `;
            } else {
                actionHtml = `
                    <div style="display: inline-flex; gap: 6px; align-items: center; justify-content: center;">
<<<<<<< HEAD
                        <button class="btn btn-sm btn-primary js-open-review-${v.id}" onclick="UserWorkManager.openReviewLink(${v.id}, this)" style="padding: 5px 12px; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 6px;" title="Open authentic review page on Village Wells marking portal">
                            <i data-lucide="external-link" style="width: 14px; height: 14px;"></i> Open / Review
=======
                        <button class="btn btn-sm btn-secondary js-ensure-link-${v.id}" onclick="UserWorkManager.ensureLink(${v.id}, this)" style="padding: 5px 11px; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 5px;">
                            <i data-lucide="link" style="width: 14px; height: 14px;"></i> Get Link
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
                        </button>
                        ${saveBtnHtml}
                    </div>
                `;
            }

            return `
                <tr>
                    <td style="color: #64748b; font-weight: 500;">${idx + 1}</td>
                    <td style="font-weight: 600; color: #0f172a;">${v.village_name}</td>
                    <td style="font-family: monospace; color: #475569;">${v.village_code}</td>
                    <td>${v.district_name || '—'}</td>
                    <td>${v.subdistrict_name || '—'}</td>
                    <td style="font-size: 0.84rem; color: #64748b;">${dateStr}</td>
                    <td>${workStatusBadge}</td>
                    <td style="text-align: center;">${actionHtml}</td>
                </tr>
            `;
        }).join('');

        lucide.createIcons();
    },

    openSurveyModal(villageId) {
        const v = this.villages.find(item => item.id === villageId);
        if (!v) return;

        const idEl = document.getElementById('surveyorVillageId');
        const nameEl = document.getElementById('surveyorVillageName');
        const codeEl = document.getElementById('surveyorVillageCode');
        const locEl = document.getElementById('surveyorVillageLocation');
        const dugwellsEl = document.getElementById('surveyorDugwells');
        const boresEl = document.getElementById('surveyorBores');
        const totalWellsEl = document.getElementById('surveyorTotalWells');
        const remarkEl = document.getElementById('surveyorRemark');
        const submitBtn = document.getElementById('btnSubmitSurveyorSave');

        if (idEl) idEl.value = v.id;
        if (nameEl) nameEl.textContent = v.village_name;
        if (codeEl) codeEl.textContent = v.village_code || '—';
        if (locEl) locEl.textContent = `${v.district_name || ''} ${v.subdistrict_name ? '/ ' + v.subdistrict_name : ''}`.trim() || '—';
        if (dugwellsEl) dugwellsEl.value = v.dugwells || 0;
        if (boresEl) boresEl.value = v.bores || 0;
        if (totalWellsEl) totalWellsEl.value = v.total_wells || ((v.dugwells || 0) + (v.bores || 0));
        if (remarkEl) remarkEl.value = v.remark || '';

<<<<<<< HEAD
        const noticeEl = document.getElementById('surveyorCorrectionNotice');
        const reasonEl = document.getElementById('surveyorCorrectionReasonText');
        if (noticeEl && reasonEl) {
            if (v.correction_reason) {
                reasonEl.textContent = v.correction_reason;
                noticeEl.style.display = 'block';
            } else {
                noticeEl.style.display = 'none';
            }
        }

=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i data-lucide="check" style="width: 15px; height: 15px;"></i><span>Save & Mark Done</span>';
        }

        App.openModal('surveyorCompleteModal');
        lucide.createIcons();
    },

    calcTotalWells() {
        const d = parseInt(document.getElementById('surveyorDugwells')?.value) || 0;
        const b = parseInt(document.getElementById('surveyorBores')?.value) || 0;
        const totalEl = document.getElementById('surveyorTotalWells');
        if (totalEl) totalEl.value = d + b;
    },

    async submitSurveySave(e) {
        if (e) e.preventDefault();
        const villageId = parseInt(document.getElementById('surveyorVillageId')?.value);
        if (!villageId) return;

        const submitBtn = document.getElementById('btnSubmitSurveyorSave');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 15px; height: 15px;"></i><span>Saving...</span>';
            lucide.createIcons();
        }

        const payload = {
            dugwells: parseInt(document.getElementById('surveyorDugwells')?.value) || 0,
            bores: parseInt(document.getElementById('surveyorBores')?.value) || 0,
            total_wells: parseInt(document.getElementById('surveyorTotalWells')?.value) || 0,
            remark: (document.getElementById('surveyorRemark')?.value || '').trim(),
            mark_completed: true,
            status: 'Done'
        };

        try {
            const resp = await fetch(`/api/user/villages/${villageId}/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error || 'Failed to save survey');

            App.closeModal('surveyorCompleteModal');
            App.toast(`🎉 Village "${data.village_name || ''}" survey saved and marked Done!`, 'success');

            // Optimistically update: Remove only this completed village from active table
            this.villages = this.villages.filter(item => item.id !== villageId);
            this.renderTable();

<<<<<<< HEAD
            // Immediately update Surveyor metrics and history
            await this.loadDashboard();
            await this.loadHistory();
=======
            // Immediately update Surveyor metrics
            await this.loadDashboard();
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
        } catch (err) {
            App.toast(`Save error: ${err.message}`, 'error');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i data-lucide="check" style="width: 15px; height: 15px;"></i><span>Save & Mark Done</span>';
                lucide.createIcons();
            }
        }
    },

    async checkSingle(villageId, btnEl) {
        if (btnEl) {
            btnEl.disabled = true;
            btnEl.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 14px; height: 14px;"></i> Checking...';
            lucide.createIcons();
        }
        try {
            const resp = await fetch(`/api/user/villages/${villageId}/check-completion`, { method: 'POST' });
            const data = await resp.json();
            if (data.success && data.data && data.data.completed) {
                App.toast(`🎉 Village "${data.data.village_name || ''}" is completed! Removed from active work list.`, 'success');
                await this.loadAssignedVillages();
                await this.loadDashboard();
<<<<<<< HEAD
                await this.loadHistory();
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            } else {
                App.toast('Village is still pending (status is review, not finalized).', 'info');
                if (btnEl) {
                    btnEl.disabled = false;
                    btnEl.innerHTML = '<i data-lucide="check-circle" style="width: 14px; height: 14px; color: #059669;"></i> Check';
                    lucide.createIcons();
                }
            }
        } catch (err) {
            App.toast('Check error: ' + err.message, 'warning');
            if (btnEl) {
                btnEl.disabled = false;
                btnEl.innerHTML = '<i data-lucide="check-circle" style="width: 14px; height: 14px; color: #059669;"></i> Check';
                lucide.createIcons();
            }
        }
    },

<<<<<<< HEAD
    async openReviewLink(villageId, btnEl) {
        // Pre-open a tab synchronously on user click to avoid browser popup blockers
        const newTab = window.open('about:blank', '_blank');
        if (btnEl) {
            btnEl.disabled = true;
            btnEl.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 14px; height: 14px;"></i> Preparing...';
=======
    async ensureLink(villageId, btnEl) {
        if (btnEl) {
            btnEl.disabled = true;
            btnEl.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 14px; height: 14px;"></i> Generating...';
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            lucide.createIcons();
        }

        try {
            const resp = await fetch(`/api/user/villages/${villageId}/ensure-link`, { method: 'POST' });
            const data = await resp.json();
<<<<<<< HEAD
            if (!data.success || !data.link) throw new Error(data.error || 'Failed to prepare genuine review link');

            const v = this.villages.find(item => item.id === villageId);
            if (v) v.generated_review_url = data.link;

            if (newTab) {
                newTab.location.href = data.link;
            } else {
                window.open(data.link, '_blank');
            }
            this.renderTable();
        } catch (err) {
            if (newTab) newTab.close();
            App.toast(`Review link notice: ${err.message}`, 'error');
            if (btnEl) {
                btnEl.disabled = false;
                btnEl.innerHTML = '<i data-lucide="external-link" style="width: 14px; height: 14px;"></i> Open / Review';
=======
            if (!data.success) throw new Error(data.error);

            App.toast('Review link generated successfully!', 'success');
            await this.loadAssignedVillages();
        } catch (err) {
            App.toast(`Link generation notice: ${err.message}`, 'error');
            if (btnEl) {
                btnEl.disabled = false;
                btnEl.innerHTML = '<i data-lucide="refresh-cw" style="width: 14px; height: 14px;"></i> Retry';
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
                lucide.createIcons();
            }
        }
    },

<<<<<<< HEAD
    async ensureLink(villageId, btnEl) {
        return this.openReviewLink(villageId, btnEl);
    },

=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
    async syncAndCheckCompletions(silent = false) {
        try {
            const resp = await fetch('/api/user/check-completions', { method: 'POST' });
            const data = await resp.json();
            if (data.success && data.completed && data.completed.length > 0) {
                data.completed.forEach(c => {
                    App.toast(`🎉 Village "${c.village_name}" completed! Removed from active list.`, 'success');
                });
<<<<<<< HEAD
                // Reload table, dashboard and history
                await this.loadAssignedVillages();
                await this.loadDashboard();
                await this.loadHistory();
=======
                // Reload table and dashboard
                await this.loadAssignedVillages();
                await this.loadDashboard();
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            } else if (!silent) {
                App.toast('Checked status: No new completions detected.', 'info');
                await this.loadAssignedVillages();
                await this.loadDashboard();
<<<<<<< HEAD
                await this.loadHistory();
=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
            }
        } catch (e) {
            if (!silent) App.toast('Status check error: ' + e.message, 'warning');
        }
    },

    onSearchInput(e) {
        if (this.searchDebounce) clearTimeout(this.searchDebounce);
        this.searchDebounce = setTimeout(() => {
            this.loadAssignedVillages();
        }, 250);
    }
};

const AdminNotificationManager = {
    notifications: [],
    lastNotificationCount: 0,
    pollTimer: null,

    init() {
        this.bindEvents();
        this.poll();
        if (this.pollTimer) clearInterval(this.pollTimer);
        this.pollTimer = setInterval(() => this.poll(), 8000);
    },

    bindEvents() {
        const btn = document.getElementById('adminNotificationBtn');
        const dropdown = document.getElementById('adminNotificationDropdown');
        if (btn && dropdown) {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const isShown = dropdown.style.display === 'block';
                dropdown.style.display = isShown ? 'none' : 'block';
            });

            document.addEventListener('click', (e) => {
                if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
                    dropdown.style.display = 'none';
                }
            });
        }

        const markAllBtn = document.getElementById('markAllReadBtn');
        if (markAllBtn) {
            markAllBtn.addEventListener('click', async () => {
                try {
                    await fetch('/api/admin/notifications/mark-read', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ mark_all: true })
                    });
                    this.poll();
                } catch (e) {
                    console.error('Error marking all notifications read:', e);
                }
            });
        }
    },

    async poll() {
        try {
            const resp = await fetch('/api/admin/notifications?unread_only=true');
            const data = await resp.json();
            if (!data.success) return;

            const notifs = data.notifications || [];
            const badge = document.getElementById('adminNotificationBadge');
            const listEl = document.getElementById('adminNotificationList');

            if (badge) {
                if (notifs.length > 0) {
                    badge.textContent = notifs.length;
                    badge.style.display = 'inline-block';
                } else {
                    badge.style.display = 'none';
                }
            }

            // Check if there are newly arrived notifications
            if (notifs.length > this.lastNotificationCount) {
                const diff = notifs.slice(0, notifs.length - this.lastNotificationCount);
                diff.forEach(n => {
                    App.toast(`🔔 ${n.message || (n.user_name + ' completed ' + n.village_name)}`, 'success');
                });
                // Also refresh dashboard KPIs to increment Completed and decrement Pending in real-time!
                if (typeof DashboardManager !== 'undefined' && DashboardManager.load) {
                    DashboardManager.load();
                }
            }
            this.lastNotificationCount = notifs.length;

            if (listEl) {
                if (!notifs.length) {
                    listEl.innerHTML = '<div style="font-size: 0.8rem; color: #64748b; text-align: center; padding: 16px;">No new completion notifications</div>';
                } else {
                    listEl.innerHTML = notifs.map(n => `
                        <div style="padding: 10px 12px; border-bottom: 1px solid #f1f5f9; display: flex; align-items: flex-start; gap: 10px;">
                            <div style="width: 28px; height: 28px; border-radius: 50%; background: #dcfce7; color: #16a34a; display: flex; align-items: center; justify-content: center; flex-shrink: 0; margin-top: 2px;">
                                <i data-lucide="check" style="width: 14px; height: 14px;"></i>
                            </div>
                            <div style="flex: 1;">
                                <div style="font-size: 0.83rem; font-weight: 600; color: #0f172a;">${n.user_name} completed ${n.village_name}</div>
                                <div style="font-size: 0.74rem; color: #94a3b8; margin-top: 2px;">${n.created_at ? new Date(n.created_at).toLocaleTimeString() : 'Just now'}</div>
                            </div>
                        </div>
                    `).join('');
                    lucide.createIcons();
                }
            }
        } catch (e) {
            console.error('Error polling admin notifications:', e);
        }
    }
};

const ReactiveSyncManager = {
    currentVersion: null,
    pollTimer: null,
    pollIntervalMs: 3000,
    isPolling: false,

    init() {
        if (this.pollTimer) clearInterval(this.pollTimer);
        this.poll();
        this.pollTimer = setInterval(() => this.poll(), this.pollIntervalMs);
    },

    isUserBusy() {
        // If a modal is open or active
        const modal = document.querySelector('.modal-backdrop[style*="display: flex"], .modal-backdrop[style*="display: block"], .modal.active, .modal[style*="display: block"], .modal[style*="display: flex"]');
        if (modal) return true;

        // If an input, textarea or select currently has focus
        const active = document.activeElement;
        if (active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.tagName === 'SELECT')) {
            return true;
        }

        return false;
    },

    async poll() {
        if (this.isPolling) return;
        this.isPolling = true;

        try {
            const vParam = this.currentVersion !== null ? this.currentVersion : 0;
            const resp = await fetch(`/api/system/heartbeat?version=${vParam}`);
            if (!resp.ok) return;
            const data = await resp.json();
            if (!data.success) return;

            const isFirst = (this.currentVersion === null);
            const hasChanged = data.has_changed;
            this.currentVersion = data.server_version;

            if (isFirst) {
                return;
            }

            if (hasChanged) {
                const role = document.body.getAttribute('data-user-role') || 'admin';

                if (role === 'admin') {
                    // Update admin dashboard KPIs and live pie chart
                    if (App.currentView === 'dashboard') {
                        DashboardManager.load();
                    } else if (App.currentView === 'villages' && !this.isUserBusy()) {
                        VillagesManager.load();
                    } else if (App.currentView === 'assign-person' && !this.isUserBusy()) {
                        PersonManager.load();
                    }

                    // Refresh notification badge/popup
                    if (typeof AdminNotificationManager !== 'undefined' && AdminNotificationManager.poll) {
                        AdminNotificationManager.poll();
                    }
                } else if (role === 'user') {
                    // Instantly sync Surveyor KPI numbers
                    if (data.user_metrics) {
                        const m = data.user_metrics;
                        const assignedEl = document.getElementById('userStatAssigned');
                        const pendingEl = document.getElementById('userStatPending');
                        if (assignedEl && m.assigned_villages !== undefined) {
                            assignedEl.textContent = Number(m.assigned_villages).toLocaleString();
                        }
                        if (pendingEl && m.pending_villages !== undefined) {
                            pendingEl.textContent = Number(m.pending_villages).toLocaleString();
                        }
                    }

                    if (App.currentView === 'user-dashboard') {
                        UserWorkManager.loadDashboard();
<<<<<<< HEAD
                        UserWorkManager.loadHistory();
                    } else if (App.currentView === 'user-excel-files' && !this.isUserBusy()) {
                        UserWorkManager.loadAssignedVillages();
                    } else if (App.currentView === 'user-history') {
                        UserWorkManager.loadHistory();
=======
                    } else if (App.currentView === 'user-excel-files' && !this.isUserBusy()) {
                        UserWorkManager.loadAssignedVillages();
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
                    }
                }
            }
        } catch (e) {
            // Heartbeat network hiccups ignored
        } finally {
            this.isPolling = false;
        }
    }
};

function getStatusBadgeClass(status) {
    switch (status) {
        case 'Pending': return 'badge-pending';
        case 'Ready to Process': return 'badge-ready';
        case 'In Progress': return 'badge-inprogress';
        case 'Marking Completed': return 'badge-marking';
        case 'KML Downloaded': return 'badge-kml';
        case 'Verified': return 'badge-verified';
        case 'Done': return 'badge-done';
        case 'Needs Review': return 'badge-review';
        case 'Failed': return 'badge-failed';
        default: return 'badge-pending';
    }
}


<<<<<<< HEAD
// Global Window Scope Bindings
window.App = App;
window.ImportManager = ImportManager;
if (typeof DashboardManager !== 'undefined') window.DashboardManager = DashboardManager;
if (typeof VillagesManager !== 'undefined') window.VillagesManager = VillagesManager;
if (typeof PersonManager !== 'undefined') window.PersonManager = PersonManager;
if (typeof UserSettingsManager !== 'undefined') window.UserSettingsManager = UserSettingsManager;
if (typeof QueueManager !== 'undefined') window.QueueManager = QueueManager;
if (typeof AutomationManager !== 'undefined') window.AutomationManager = AutomationManager;
if (typeof SettingsManager !== 'undefined') window.SettingsManager = SettingsManager;
if (typeof UserWorkManager !== 'undefined') window.UserWorkManager = UserWorkManager;
if (typeof AdminNotificationManager !== 'undefined') window.AdminNotificationManager = AdminNotificationManager;

=======
>>>>>>> 960899f6400ba7a53f452028e0fb1d3f27ae62b1
// Bootstrap Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
    ImportManager.init();
    VillagesManager.init();
    QueueManager.init();
    AutomationManager.init();
    SettingsManager.init();
});
