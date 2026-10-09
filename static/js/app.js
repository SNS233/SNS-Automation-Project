/**
 * MASTER BOREWELL & TUBEWELL MANAGEMENT PORTAL
 * Core Frontend Application Script
 */

/* =========================================================================
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
            'user-excel-files': 'Excel Files — Assigned Villages'
        };
        const titleEl = document.getElementById('pageTitle');
        if (titleEl) titleEl.textContent = titles[viewName] || 'Portal';

        this.currentView = viewName;
        window.scrollTo({ top: 0, behavior: 'smooth' });

        // Load data for specific view
        if (viewName === 'dashboard') DashboardManager.load();
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
        else if (viewName === 'user-dashboard') UserWorkManager.loadDashboard();
        else if (viewName === 'user-excel-files') UserWorkManager.loadAssignedVillages();

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

/* =========================================================================
   1. DASHBOARD MANAGER (STREAMLINED FOR LARGE DATASETS)
   ========================================================================= */
const DashboardManager = {
    zoneInsights: [],
    currentZoneSort: { column: 'total_villages', dir: 'desc' },
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

            const pct = m.progress_percentage || 0;
            if (document.getElementById('progressText')) {
                document.getElementById('progressText').textContent = `${pct}%`;
            }
            if (document.getElementById('progressBar')) {
                document.getElementById('progressBar').style.width = `${Math.min(pct, 100)}%`;
            }

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

            lucide.createIcons();
        } catch (e) {
            console.error('Error loading dashboard:', e);
            App.toast('Failed to load dashboard metrics.', 'error');
        }
    },

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

        const isDark = document.body.classList.contains('dark-theme');
        const textColor = isDark ? '#f1f5f9' : '#0f172a';
        const borderColor = isDark ? '#1e293b' : '#ffffff';

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
    }
};

/* =========================================================================
   2. IMPORT MANAGER (Excel / CSV)
   ========================================================================= */
const ImportManager = {
    selectedFile: null,
    previewData: null,

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

        // Canonical fields target list
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

        // Render Column Mapping Controls
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

        // Render Sample Table
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

        // Gather column mappings
        const mappings = {};
        document.querySelectorAll('.mapping-select').forEach(sel => {
            const actual = sel.getAttribute('data-actual-header');
            const val = sel.value;
            if (actual && val) mappings[actual] = val;
        });

        const dupMode = document.querySelector('input[name="dupMode"]:checked')?.value || 'skip';

        const btn = document.getElementById('startImportBtn');
        btn.disabled = true;
        btn.innerHTML = '<span>Importing data...</span>';

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

        document.getElementById('resTotal').textContent = res.total_rows;
        document.getElementById('resInserted').textContent = res.inserted_count;
        document.getElementById('resUpdated').textContent = res.updated_count;
        document.getElementById('resDuplicates').textContent = res.duplicates_detected;
        document.getElementById('resInvalid').textContent = res.invalid_rows;

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

/* =========================================================================
   3. ALL VILLAGES MANAGER
   ========================================================================= */
const VillagesManager = {
    currentPage: 1,
    pageSize: 20,
    selectedIds: new Set(),
    sortBy: 'district_name',
    sortDir: 'asc',

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

        ['filterDistrict', 'filterSubdistrict', 'filterZone', 'filterStatus'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', () => {
                this.currentPage = 1;
                this.load();
            });
        });

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

    async loadFilters() {
        try {
            const resp = await fetch('/api/villages/filters');
            const data = await resp.json();
            if (data.success) {
                const distSel = document.getElementById('filterDistrict');
                if (distSel) {
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
                }
            }
        } catch (e) {
            console.warn('Could not load filters:', e);
        }
    },

    async load() {
        const search = document.getElementById('villageSearchInput')?.value || '';
        const district = document.getElementById('filterDistrict')?.value || '';
        const subdistrict = document.getElementById('filterSubdistrict')?.value || '';
        const zone = document.getElementById('filterZone')?.value || '';
        const status = document.getElementById('filterStatus')?.value || '';

        const params = new URLSearchParams({
            page: this.currentPage,
            page_size: this.pageSize,
            search,
            district,
            subdistrict,
            zone,
            status,
            sort_by: this.sortBy,
            sort_dir: this.sortDir
        });

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

        if (data.items.length === 0) {
            tbody.innerHTML = '<tr><td colspan="16" style="text-align: center; padding: 36px; color: #94a3b8;">No matching villages found.</td></tr>';
            this.updatePagination(0, 0, 1, 1);
            return;
        }

        tbody.innerHTML = data.items.map(v => {
            const isChecked = this.selectedIds.has(v.id) ? 'checked' : '';
            const kmlLink = v.kml_id 
                ? `<a href="/api/kml/download/${v.kml_id}" class="badge badge-kml" style="text-decoration:none;" title="Download KML"><i data-lucide="download" style="width:12px;height:12px;"></i> KML v${v.kml_version}</a>`
                : `<span style="color:#94a3b8; font-size:0.75rem;">None</span>`;

            return `
                <tr>
                    <td><input type="checkbox" class="village-row-checkbox" value="${v.id}" ${isChecked} onchange="VillagesManager.toggleRow(${v.id}, this.checked)"></td>
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
                        </button>
                    </td>
                </tr>
            `;
        }).join('');

        this.updatePagination(data.total_count, data.items.length, data.current_page, data.total_pages);
        lucide.createIcons();
    },

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

            try {
                const resp = await fetch('/api/auth/change-password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_password, new_password })
                });
                const d = await resp.json();
                if (d.success) {
                    App.toast('Password changed successfully!', 'success');
                    document.getElementById('currPassword').value = '';
                    document.getElementById('newPassword').value = '';
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
    pollTimer: null,
    searchDebounce: null,

    init() {
        this.loadDashboard();
        this.loadAssignedVillages();
        // Start background polling every 10 seconds to detect remote completion automatically
        if (this.pollTimer) clearInterval(this.pollTimer);
        this.pollTimer = setInterval(() => {
            this.syncAndCheckCompletions(true);
        }, 10000);
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
            const workStatusBadge = '<span class="badge" style="background: #fef3c7; color: #92400e; border: 1px solid #fde68a; font-weight: 600;">Not Done</span>';

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
                        <button class="btn btn-sm btn-secondary js-ensure-link-${v.id}" onclick="UserWorkManager.ensureLink(${v.id}, this)" style="padding: 5px 11px; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 5px;">
                            <i data-lucide="link" style="width: 14px; height: 14px;"></i> Get Link
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

            // Immediately update Surveyor metrics
            await this.loadDashboard();
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

    async ensureLink(villageId, btnEl) {
        if (btnEl) {
            btnEl.disabled = true;
            btnEl.innerHTML = '<i data-lucide="loader-2" class="spin" style="width: 14px; height: 14px;"></i> Generating...';
            lucide.createIcons();
        }

        try {
            const resp = await fetch(`/api/user/villages/${villageId}/ensure-link`, { method: 'POST' });
            const data = await resp.json();
            if (!data.success) throw new Error(data.error);

            App.toast('Review link generated successfully!', 'success');
            await this.loadAssignedVillages();
        } catch (err) {
            App.toast(`Link generation notice: ${err.message}`, 'error');
            if (btnEl) {
                btnEl.disabled = false;
                btnEl.innerHTML = '<i data-lucide="refresh-cw" style="width: 14px; height: 14px;"></i> Retry';
                lucide.createIcons();
            }
        }
    },

    async syncAndCheckCompletions(silent = false) {
        try {
            const resp = await fetch('/api/user/check-completions', { method: 'POST' });
            const data = await resp.json();
            if (data.success && data.completed && data.completed.length > 0) {
                data.completed.forEach(c => {
                    App.toast(`🎉 Village "${c.village_name}" completed! Removed from active list.`, 'success');
                });
                // Reload table and dashboard
                await this.loadAssignedVillages();
                await this.loadDashboard();
            } else if (!silent) {
                App.toast('Checked status: No new completions detected.', 'info');
                await this.loadAssignedVillages();
                await this.loadDashboard();
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
                    } else if (App.currentView === 'user-excel-files' && !this.isUserBusy()) {
                        UserWorkManager.loadAssignedVillages();
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


// Bootstrap Application on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
    App.init();
    ImportManager.init();
    VillagesManager.init();
    QueueManager.init();
    AutomationManager.init();
    SettingsManager.init();
});
