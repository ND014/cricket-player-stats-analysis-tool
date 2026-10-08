/**
 * GLOBAL T20 MATCHUP & VALUE AUDIT ENGINE - CLIENT APPLICATION
 * High-performance state management, sub-millisecond autocomplete,
 * dynamic API fetching, and interactive sports data visualizations.
 */

document.addEventListener('DOMContentLoaded', () => {
  // App State
  const state = {
    currentPlayer: 'Virat Kohli',
    currentTournament: 'ALL',
    wagonBowlerType: 'ALL',
    wagonPhase: 'ALL',
    defPhase: 'ALL',
    defHand: 'ALL',
    compP1: 'Virat Kohli',
    compP2: 'Sandeep Sharma',
    compMode: 'auto',
    compArchetype: 'ALL',
    compHand: 'ALL',
    splitsRole: 'bat',
    splitsBowlerTypes: ['LAF', 'RAF', 'LAM', 'RAM', 'OFF_SPIN', 'WRIST_SPIN', 'SLA', 'LEFT_WRIST_SPIN'],
    splitsBatterHands: ['RHB', 'LHB'],
    splitsPhases: ['Powerplay', 'Middle', 'Death'],
    currentTab: 'tab-dossier',
    censusLoaded: false,
    cache: {}
  };

  // DOM Elements
  const globalTournamentSelect = document.getElementById('globalTournamentSelect');
  const playerSearchInput = document.getElementById('playerSearchInput');
  const searchClearBtn = document.getElementById('searchClearBtn');
  const autocompleteDropdown = document.getElementById('autocompleteDropdown');
  const loadingOverlay = document.getElementById('loadingOverlay');
  const loadingText = document.getElementById('loadingText');

  // Tactical Matchup Splits Elements
  const splitsCardTitle = document.getElementById('splitsCardTitle');
  const splitsCardSubtitle = document.getElementById('splitsCardSubtitle');
  const splitsCardIcon = document.getElementById('splitsCardIcon');
  const splitsRoleToggle = document.getElementById('splitsRoleToggle');
  const splitsRoleBatBtn = document.getElementById('splitsRoleBatBtn');
  const splitsRoleBowlBtn = document.getElementById('splitsRoleBowlBtn');
  const splitsActiveCountBadge = document.getElementById('splitsActiveCountBadge');
  const batterSplitsControls = document.getElementById('batterSplitsControls');
  const bowlerSplitsControls = document.getElementById('bowlerSplitsControls');
  const batterArchetypePills = document.querySelectorAll('#batterArchetypePills .pill-btn-compact, #batterArchetypePills .pill-btn');
  const batterSplitsPresetSelect = document.getElementById('batterSplitsPresetSelect');
  const btnSplitsSelectAll = document.getElementById('btnSplitsSelectAll');
  const btnSplitsClear = document.getElementById('btnSplitsClear');
  const splitsSelectionCount = document.getElementById('splitsSelectionCount');
  const bowlerHandPills = document.querySelectorAll('#bowlerHandPills .pill-btn-compact, #bowlerHandPills .pill-btn');
  const bowlerPhasePills = document.querySelectorAll('#bowlerPhasePills .pill-btn-compact, #bowlerPhasePills .pill-btn');
  const bowlerSplitsPresetSelect = document.getElementById('bowlerSplitsPresetSelect');
  const btnBowlerSplitsReset = document.getElementById('btnBowlerSplitsReset');
  const splitsKpiGrid = document.getElementById('splitsKpiGrid');
  const splitsPhaseBars = document.getElementById('splitsPhaseBars');
  const splitsPhaseTitle = document.getElementById('splitsPhaseTitle');
  const splitsMatchupContent = document.getElementById('splitsMatchupContent');
  const splitsMatchupTitle = document.getElementById('splitsMatchupTitle');

  // Tab Buttons & Panes
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanes = document.querySelectorAll('.tab-pane');

  // Quick Pick Chips
  const quickChips = document.querySelectorAll('.chip-btn');

  // Wagon Controls
  const wagonArchetypeSelect = document.getElementById('wagonArchetypeSelect');
  const wagonPhaseSelect = document.getElementById('wagonPhaseSelect');
  const refreshWagonBtn = document.getElementById('refreshWagonBtn');

  // Defensive Controls
  const defPhaseSelect = document.getElementById('defPhaseSelect');
  const defHandSelect = document.getElementById('defHandSelect');
  const refreshDefBtn = document.getElementById('refreshDefBtn');

  // Compare Controls
  const compP1Input = document.getElementById('compPlayer1Input');
  const compP2Input = document.getElementById('compPlayer2Input');
  const launchCompareBtn = document.getElementById('launchCompareBtn');
  const compareModeSelect = document.getElementById('compareModeSelect');
  const compareArchetypeSelect = document.getElementById('compareArchetypeSelect');
  const compareHandSelect = document.getElementById('compareHandSelect');
  const comparePresetSelect = document.getElementById('comparePresetSelect');
  const compareArchetypeWrap = document.getElementById('compareArchetypeWrap');
  const compareHandWrap = document.getElementById('compareHandWrap');
  const optBatBowl = document.getElementById('optBatBowl');
  const optBowlBat = document.getElementById('optBowlBat');

  // Safe number formatter helper to guard against undefined / null .toFixed crashes
  function fmt(val, decimals = 1, fallback = '0.0') {
    if (val === null || val === undefined || isNaN(val)) return fallback;
    const num = Number(val);
    return isNaN(num) ? fallback : num.toFixed(decimals);
  }

  // ==========================================================================
  // 1. TAB SWITCHING
  // ==========================================================================
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });

  function switchTab(tabId) {
    state.currentTab = tabId;
    tabBtns.forEach(b => b.classList.toggle('active', b.getAttribute('data-tab') === tabId));
    tabPanes.forEach(p => p.classList.toggle('active', p.id === tabId));

    if (tabId === 'tab-dossier') {
      loadPlayerAudit(state.currentPlayer);
    } else if (tabId === 'tab-wagon') {
      loadWagonWheel(state.currentPlayer, state.wagonBowlerType, state.wagonPhase);
    } else if (tabId === 'tab-defensive') {
      loadDefensiveWheel(state.currentPlayer, state.defPhase, state.defHand);
    } else if (tabId === 'tab-compare') {
      loadComparison(state.compP1, state.compP2);
    } else if (tabId === 'tab-census') {
      if (!state.censusLoaded) loadCensus();
    }
  }

  // ==========================================================================
  // 2. LOADING STATE
  // ==========================================================================
  function showLoading(msg = 'Processing 2.67M ball-by-ball deliveries...') {
    loadingText.textContent = msg;
    loadingOverlay.style.display = 'flex';
  }

  function hideLoading() {
    loadingOverlay.style.display = 'none';
  }

  function showToast(msg, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = `toast-msg toast-${type}`;
    const icon = type === 'error' ? '⚠️' : (type === 'warning' ? '⚡' : (type === 'success' ? '✅' : 'ℹ️'));
    toast.innerHTML = `<span style="font-size:1.1rem;">${icon}</span><div>${msg}</div>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(50px)';
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  }

  // ==========================================================================
  // 3. TOURNAMENT SELECTOR
  // ==========================================================================
  globalTournamentSelect.addEventListener('change', (e) => {
    state.currentTournament = e.target.value;
    // Reload active tab with new tournament scope
    switchTab(state.currentTab);
  });

  // ==========================================================================
  // 4. OMNISEARCH & AUTOCOMPLETE
  // ==========================================================================
  let searchDebounceTimer = null;

  playerSearchInput.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    searchClearBtn.style.display = val ? 'flex' : 'none';

    clearTimeout(searchDebounceTimer);
    if (val.length < 2) {
      autocompleteDropdown.style.display = 'none';
      return;
    }

    searchDebounceTimer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(val)}&limit=10`);
        const list = await res.json();
        renderAutocomplete(list);
      } catch (err) {
        console.error('Autocomplete search failed:', err);
      }
    }, 150);
  });

  searchClearBtn.addEventListener('click', () => {
    playerSearchInput.value = '';
    searchClearBtn.style.display = 'none';
    autocompleteDropdown.style.display = 'none';
    playerSearchInput.focus();
  });

  function renderAutocomplete(items) {
    if (!items || items.length === 0) {
      autocompleteDropdown.style.display = 'none';
      return;
    }

    autocompleteDropdown.innerHTML = items.map(item => `
      <div class="autocomplete-item" data-cric="${item.cric_name}" data-name="${item.name}">
        <div style="display:flex; flex-direction:column; gap:2px;">
          <span class="autocomplete-name">${item.display || item.name}</span>
          <span style="font-size:0.72rem; color:var(--text-muted); font-family:var(--font-mono, monospace);">Scorecard ID: ${item.cric_name}</span>
        </div>
        <span class="autocomplete-tag">${item.deliveries ? item.deliveries.toLocaleString() + ' balls' : 'Select'}</span>
      </div>
    `).join('');

    autocompleteDropdown.style.display = 'block';

    autocompleteDropdown.querySelectorAll('.autocomplete-item').forEach(el => {
      el.addEventListener('click', () => {
        const selName = el.getAttribute('data-name');
        playerSearchInput.value = selName;
        autocompleteDropdown.style.display = 'none';
        selectPlayer(selName);
      });
    });
  }

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.search-box-card')) {
      autocompleteDropdown.style.display = 'none';
    }
  });

  // Quick Pick Chips
  quickChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const p = chip.getAttribute('data-player');
      playerSearchInput.value = p;
      selectPlayer(p);
    });
  });

  function selectPlayer(playerName) {
    state.currentPlayer = playerName;
    if (state.currentTab === 'tab-compare') {
      state.compP1 = playerName;
      compP1Input.value = playerName;
      loadComparison(state.compP1, state.compP2);
    } else {
      switchTab(state.currentTab);
    }
  }

  // ==========================================================================
  // 5. API FETCH & RENDER: TAB 1 (PLAYER DOSSIER)
  // ==========================================================================
  async function loadPlayerAudit(playerName) {
    showLoading(`Building scouting dossier for ${playerName}...`);
    try {
      const res = await fetch(`/api/player/audit?name=${encodeURIComponent(playerName)}&tournament=${state.currentTournament}`);
      if (!res.ok) throw new Error(`Could not load audit data for ${playerName}`);
      const data = await res.json();
      renderDossier(data);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      hideLoading();
    }
  }

  function renderDossier(data) {
    state.currentAuditData = data;
    const meta = data.meta || {};
    const role = meta.role || 'Batter';
    const isBowler = (role === 'Bowler');
    // Use server-computed flags (threshold: 30 deliveries bowled)
    const hasBatting = data.has_batting !== undefined ? data.has_batting : true;
    const hasBowling = data.has_bowling !== undefined ? data.has_bowling : (role === 'Bowler' || role === 'All-Rounder');
    const isAllRounder = (role === 'All-Rounder') || (hasBatting && hasBowling);

    // Determine active splitsRole
    if (role === 'Bowler') {
      state.splitsRole = 'bowl';
    } else if (!isAllRounder) {
      state.splitsRole = 'bat';
    } else if (isAllRounder) {
      if (!state.splitsRole) state.splitsRole = 'bat';
    }

    // 1. Player Bio Banner
    const resolvedFullName = data.full_name || data.player_query;
    document.getElementById('bioPlayerName').textContent = resolvedFullName;
    document.getElementById('bioCricName').textContent = (resolvedFullName.toLowerCase() !== data.cric_name.toLowerCase()) 
      ? `Scorecard ID: ${data.cric_name}` 
      : data.cric_name;
    document.getElementById('bioDeliveries').textContent = data.total_deliveries.toLocaleString();
    
    // Initials from resolved full name
    const initials = resolvedFullName.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
    document.getElementById('playerAvatarInitials').textContent = initials;

    // Badges
    const roleEl = document.getElementById('bioRole');
    roleEl.textContent = role;
    if (role === 'Bowler') roleEl.style.borderColor = 'rgba(16, 185, 129, 0.4)';
    else if (role === 'All-Rounder' || isAllRounder) roleEl.style.borderColor = 'rgba(129, 140, 248, 0.4)';
    else roleEl.style.borderColor = 'rgba(56, 189, 248, 0.4)';

    const tier = meta.market_price >= 10.0 ? 'Marquee International' : (meta.market_price >= 2.0 ? 'Franchise Core' : 'Domestic Prospect');
    document.getElementById('bioTier').textContent = tier;
    document.getElementById('bioProfile').textContent = meta.public_label || `${role} active across premier T20 competitions.`;

    // 2. Render all discipline-specific sections (Hero KPIs, Phase Efficiency, Antagonist, Alternatives, Footprint)
    renderDossierDiscipline(data);

    // 3. Interactive Tactical Matchup Splits Card
    renderTacticalSplitsCard(data);
  }

  function renderDossierDiscipline(data) {
    if (!data) return;
    const meta = data.meta || {};
    const role = meta.role || 'Batter';
    const isBowlerMode = (state.splitsRole === 'bowl') || (role === 'Bowler' && state.splitsRole !== 'bat');

    // Hero KPI metrics & stance
    renderHeroMetrics(data, isBowlerMode);

    // Column 1: Phase Efficiency Breakdown
    renderPhaseEfficiency(data, isBowlerMode);

    // Column 2: Antagonist / Kryptonite / Punishers
    renderAntagonistSection(data, isBowlerMode);

    // Column 3: Moneyball Alternatives
    renderMoneyballSection(data, isBowlerMode);

    // Global Tournament Footprint Table
    renderFootprintTable(data, isBowlerMode);
  }

  function renderHeroMetrics(data, isBowlerMode) {
    const meta = data.meta || {};
    const stanceEl = document.getElementById('bioStance');

    if (isBowlerMode) {
      const bStats = data.bowling_stats || {};
      document.getElementById('bioHeroMetric1').textContent = (bStats.total_wickets || 0).toLocaleString();
      document.getElementById('bioHeroLabel1').textContent = 'Career Wickets';
      document.getElementById('bioHeroMetric2').textContent = (bStats.overall_econ || 0).toFixed(2);
      document.getElementById('bioHeroLabel2').textContent = 'Economy Rate';
      document.getElementById('bioHeroMetric3').textContent = `${(bStats.total_overs || 0).toFixed(1)} ov`;
      document.getElementById('bioHeroLabel3').textContent = 'Overs Bowled';
      if (stanceEl) stanceEl.textContent = meta.bowling_arm || meta.hand || 'Right-Arm';
    } else {
      const batStats = data.batting_stats || {};
      document.getElementById('bioHeroMetric1').textContent = (batStats.total_runs || 0).toLocaleString();
      document.getElementById('bioHeroLabel1').textContent = 'Career Runs';
      document.getElementById('bioHeroMetric2').textContent = (batStats.overall_sr || 0).toFixed(1);
      document.getElementById('bioHeroLabel2').textContent = 'Strike Rate';
      document.getElementById('bioHeroMetric3').textContent = (batStats.overall_avg || 0).toFixed(1);
      document.getElementById('bioHeroLabel3').textContent = 'Batting Average';
      if (stanceEl) stanceEl.textContent = meta.hand || 'RHB';
    }
  }

  function renderPhaseEfficiency(data, isBowlerMode) {
    const container = document.getElementById('phaseEfficiencyBody');
    const titleEl = document.getElementById('phaseEfficiencyCardTitle');
    if (!container) return;

    if (titleEl) {
      titleEl.textContent = isBowlerMode ? 'Career Phase Efficiency (Bowling)' : 'Career Phase Efficiency (Batting)';
    }

    const phases = ['Powerplay', 'Middle', 'Death'];

    if (isBowlerMode) {
      const b = data.bowling_stats || { phases: {} };
      container.innerHTML = phases.map(ph => {
        const st = (b.phases && b.phases[ph]) || { econ: 0, dot_pct: 0, wickets: 0 };
        const meterPct = Math.min(100, Math.max(10, (12 - st.econ) * 10)); // Higher meter = tighter economy
        return `
          <div class="phase-stat-row">
            <div class="phase-label-group">
              <span class="phase-name">${ph} (Overs ${ph === 'Powerplay' ? '1–6' : (ph === 'Middle' ? '7–15' : '16–20')})</span>
              <span class="phase-metrics">Econ: <strong>${(st.econ || 0).toFixed(2)}</strong> • Dots: <strong>${(st.dot_pct || 0).toFixed(1)}%</strong> • Wkts: <strong>${st.wickets || 0}</strong></span>
            </div>
            <div class="meter-track">
              <div class="meter-fill green" style="width: ${meterPct}%"></div>
            </div>
          </div>
        `;
      }).join('');
    } else {
      const bat = data.batting_stats || { phases: {} };
      container.innerHTML = phases.map(ph => {
        const st = (bat.phases && bat.phases[ph]) || { sr: 0, dot_pct: 0, runs: 0, bnd_pct: 0 };
        const meterPct = Math.min(100, Math.max(10, (st.sr / 200) * 100));
        return `
          <div class="phase-stat-row">
            <div class="phase-label-group">
              <span class="phase-name">${ph} (Overs ${ph === 'Powerplay' ? '1–6' : (ph === 'Middle' ? '7–15' : '16–20')})</span>
              <span class="phase-metrics">SR: <strong>${(st.sr || 0).toFixed(1)}</strong> • Dots: <strong>${(st.dot_pct || 0).toFixed(1)}%</strong> • 4/6s: <strong>${(st.bnd_pct || 0).toFixed(1)}%</strong></span>
            </div>
            <div class="meter-track">
              <div class="meter-fill blue" style="width: ${meterPct}%"></div>
            </div>
          </div>
        `;
      }).join('');
    }
  }

  function renderAntagonistSection(data, isBowlerMode) {
    const container = document.getElementById('antagonistBody');
    const titleEl = document.getElementById('antagonistCardTitle');
    if (!container) return;

    let html = '';

    if (!isBowlerMode) {
      if (titleEl) titleEl.textContent = 'Primary Kryptonite & Top 3 Nemeses';
      const krypto = data.kryptonite;
      if (krypto && krypto.primary_kryptonite) {
        html += `
          <div class="kryptonite-alert-box">
            <div class="kryptonite-title">PRIMARY KRYPTONITE: ${krypto.primary_kryptonite}</div>
            <div class="kryptonite-detail">KVI Flaw Index: ${krypto.primary_kvi} / 100 • Strike Rate: ${krypto.primary_sr} vs this archetype</div>
          </div>
        `;
      }

      const nemeses = data.nemeses || [];
      if (nemeses.length > 0) {
        html += '<div style="font-size:0.78rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; margin-bottom:8px;">Top Nemesis Bowlers (Most Dismissals / Choke):</div>';
        nemeses.forEach(n => {
          html += `
            <div class="antagonist-item">
              <div>
                <div class="antagonist-name">${n.bowler_full || n.bowler} ${n.bowler_full && n.bowler_full !== n.bowler ? `<span style="font-size:0.75rem; color:var(--text-muted); font-weight:400;">(${n.bowler})</span>` : ''}</div>
                <div class="antagonist-arch">${n.bowler_archetype} • ${n.balls} balls faced</div>
              </div>
              <div class="antagonist-stats">
                <div>${n.dismissals} OUTS</div>
                <div class="antagonist-sub">${(n.sr || 0).toFixed(1)} SR • ${(n.dot_pct || 0).toFixed(1)}% Dots</div>
              </div>
            </div>
          `;
        });
      } else {
        html += '<div style="color:var(--text-secondary); font-size:0.85rem;">No severe nemesis bowlers recorded with 15+ balls.</div>';
      }
    } else {
      if (titleEl) titleEl.textContent = 'Top 3 Punisher Batters (Opponent Threats)';
      const punishers = data.punishers || [];
      if (punishers.length > 0) {
        const topP = punishers[0];
        html += `
          <div class="kryptonite-alert-box" style="border-left-color: var(--amber-gold); background: rgba(245, 158, 11, 0.08);">
            <div class="kryptonite-title" style="color: var(--amber-gold);">PRIMARY PUNISHER: ${topP.batter_full || topP.striker}</div>
            <div class="kryptonite-detail">Concedes ${(topP.sr || 0).toFixed(1)} SR • ${topP.runs} runs in ${topP.balls} balls (${topP.boundaries} Boundaries)</div>
          </div>
        `;
        html += '<div style="font-size:0.78rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; margin-bottom:8px;">Batters Who Attack This Bowler Most:</div>';
        punishers.forEach(p => {
          html += `
            <div class="antagonist-item">
              <div>
                <div class="antagonist-name">${p.batter_full || p.striker} ${p.batter_full && p.batter_full !== p.striker ? `<span style="font-size:0.75rem; color:var(--text-muted); font-weight:400;">(${p.striker})</span>` : ''}</div>
                <div class="antagonist-arch">${p.balls} balls faced • ${p.runs} runs conceded</div>
              </div>
              <div class="antagonist-stats">
                <div style="color:var(--amber-gold); font-weight:700;">${(p.sr || 0).toFixed(1)} SR</div>
                <div class="antagonist-sub">${p.boundaries} Boundaries • ${p.dismissals} Dismissals</div>
              </div>
            </div>
          `;
        });
      } else {
        html += '<div style="color:var(--text-secondary); font-size:0.85rem;">This bowler concedes low boundary damage against all batters.</div>';
      }
    }

    container.innerHTML = html;
  }

  function renderMoneyballSection(data, isBowlerMode) {
    const container = document.getElementById('moneyballBody');
    const titleEl = document.getElementById('moneyballCardTitle');
    if (!container) return;

    if (titleEl) {
      titleEl.textContent = isBowlerMode ? 'Domestic Tactical Alternatives: Bowling (SMAT)' : 'Domestic Tactical Alternatives: Batting (SMAT)';
    }

    const altsData = isBowlerMode 
      ? (data.bowling_alternatives || data.alternatives)
      : (data.batting_alternatives || data.alternatives);

    if (!altsData || !altsData.alts || altsData.alts.length === 0) {
      container.innerHTML = '<div style="color:var(--text-secondary); font-size:0.85rem; padding:10px 0;">No domestic replacement needed. Target player is already at domestic level or niche phase benchmark.</div>';
      return;
    }

    const t = altsData.target || {};
    const phaseStr = (altsData.phase || (isBowlerMode ? 'Death' : 'Middle')).toUpperCase();

    const targetMetric = (t.econ !== undefined && t.econ !== null)
      ? `${fmt(t.econ, 2)} Econ • ${fmt(t.dot_pct, 1)}% Dots (${t.b || 0} balls)`
      : `${fmt(t.sr, 1)} SR • ${fmt(t.dot_pct, 1)}% Dots (${t.b || 0} balls)`;

    let html = `
      <div style="background:rgba(11, 15, 25, 0.7); border:1px solid var(--border-subtle); border-radius:var(--radius-md); padding:10px 14px; margin-bottom:12px; font-size:0.8rem;">
        <span style="color:var(--text-muted); font-weight:700;">BENCHMARK TARGET (${phaseStr}):</span>
        <strong style="color:var(--text-primary); margin-left:6px;">${targetMetric}</strong>
      </div>
    `;

    altsData.alts.forEach(a => {
      const metricStr = (a.econ !== undefined && a.econ !== null)
        ? `${fmt(a.econ, 2)} Econ • ${fmt(a.dot_pct, 1)}% Dots`
        : `${fmt(a.sr, 1)} SR • ${fmt(a.dot_pct, 1)}% Dots`;
      html += `
        <div class="alt-item">
          <div class="alt-header-row">
            <span class="alt-player-name">${a.display_name || a.full_name || a.player}</span>
            <span class="alt-metrics-pill">${metricStr}</span>
          </div>
          <div class="alt-rationale">${a.scouting_rationale}</div>
        </div>
      `;
    });

    container.innerHTML = html;
  }

  function renderFootprintTable(data, isBowlerMode) {
    const tbody = document.getElementById('footprintTableBody');
    const countTag = document.getElementById('footprintCountTag');
    const titleEl = document.getElementById('footprintCardTitle');
    if (!tbody) return;

    if (titleEl) {
      titleEl.textContent = isBowlerMode ? 'Global Tournament Footprint (Bowling)' : 'Global Tournament Footprint (Batting)';
    }

    const footprint = isBowlerMode 
      ? (data.bowling_footprint || data.footprint || [])
      : (data.batting_footprint || data.footprint || []);

    if (countTag) {
      countTag.textContent = `${footprint.length} Competitions Covered`;
    }

    const thVol = document.getElementById('thFootprintVolume');
    const thRate = document.getElementById('thFootprintRate');
    const thSec = document.getElementById('thFootprintSec');
    if (thVol) thVol.textContent = isBowlerMode ? 'Overs' : 'Runs';
    if (thRate) thRate.textContent = isBowlerMode ? 'Economy' : 'Strike Rate';
    if (thSec) thSec.textContent = isBowlerMode ? 'Wickets' : 'Average';

    if (footprint.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--text-secondary);">No multi-tournament footprint records available.</td></tr>';
      return;
    }

    tbody.innerHTML = footprint.map(r => {
      const volume = isBowlerMode ? `${fmt(r.overs || ((r.balls || 0) / 6.0), 1)} ov` : Math.round(r.runs || 0).toLocaleString();
      const rate = isBowlerMode ? fmt(r.econ, 2) : fmt(r.sr, 1);
      const sec = isBowlerMode ? (r.wickets || 0) : fmt(r.avg, 1);

      return `
        <tr>
          <td><strong>${r.tournament}</strong></td>
          <td>${r.matches || 0}</td>
          <td>${volume}</td>
          <td><strong>${rate}</strong></td>
          <td>${sec}</td>
          <td>${fmt(r.dot_pct, 1)}%</td>
        </tr>
      `;
    }).join('');
  }

  // ==========================================================================
  // 5B. INTERACTIVE TACTICAL MATCHUP SPLITS (TAB 1 AUDIT PAGE)
  // ==========================================================================
  const ALL_BOWLER_ARCHETYPES = ['LAF', 'RAF', 'LAM', 'RAM', 'OFF_SPIN', 'WRIST_SPIN', 'SLA', 'LEFT_WRIST_SPIN'];
  const ALL_BATTER_HANDS = ['RHB', 'LHB'];
  const ALL_PHASES = ['Powerplay', 'Middle', 'Death'];

  function renderTacticalSplitsCard(auditData) {
    const role = (auditData.meta && auditData.meta.role) ? auditData.meta.role : 'Batter';
    const isBowler = (role === 'Bowler');
    // Use server-computed flags so part-time bowlers (>=30 balls) get the toggle too
    const hasBatting = auditData.has_batting !== undefined ? auditData.has_batting : true;
    const hasBowling = auditData.has_bowling !== undefined ? auditData.has_bowling : (role === 'Bowler' || role === 'All-Rounder');
    const isAllRounder = (role === 'All-Rounder') || (hasBatting && hasBowling);

    if (isAllRounder) {
      if (splitsRoleToggle) splitsRoleToggle.style.display = 'inline-flex';
    } else {
      if (splitsRoleToggle) splitsRoleToggle.style.display = 'none';
      state.splitsRole = isBowler ? 'bowl' : 'bat';
    }

    updateSplitsRoleUI();

    const initSp = auditData.initial_splits;
    if (initSp && ((initSp.active_role === state.splitsRole) || (initSp.role === state.splitsRole) || (!initSp.active_role && !initSp.role && state.splitsRole === (isBowler ? 'bowl' : 'bat')))) {
      renderSplitsDashboard(initSp);
    } else {
      fetchTacticalSplits();
    }
  }

  function updateSplitsRoleUI() {
    if (state.splitsRole === 'bat') {
      if (splitsRoleBatBtn) splitsRoleBatBtn.classList.add('active');
      if (splitsRoleBowlBtn) splitsRoleBowlBtn.classList.remove('active');
      if (batterSplitsControls) batterSplitsControls.style.display = 'flex';
      if (bowlerSplitsControls) bowlerSplitsControls.style.display = 'none';
      if (splitsCardTitle) splitsCardTitle.textContent = 'Tactical Matchup Splits: Performance vs Bowling Types';
      if (splitsCardSubtitle) splitsCardSubtitle.textContent = 'Filter batter metrics against specific bowling archetypes or multi-select styles';
      updateBatterPillUI();
    } else {
      if (splitsRoleBatBtn) splitsRoleBatBtn.classList.remove('active');
      if (splitsRoleBowlBtn) splitsRoleBowlBtn.classList.add('active');
      if (batterSplitsControls) batterSplitsControls.style.display = 'none';
      if (bowlerSplitsControls) bowlerSplitsControls.style.display = 'flex';
      if (splitsCardTitle) splitsCardTitle.textContent = 'Tactical Matchup Splits: Bowling Record vs Batter Profiles';
      if (splitsCardSubtitle) splitsCardSubtitle.textContent = 'Filter bowler metrics against batter handedness (RHB/LHB) and match phases';
      updateBowlerPillUI();
    }
  }

  if (splitsRoleBatBtn) {
    splitsRoleBatBtn.addEventListener('click', () => {
      state.splitsRole = 'bat';
      updateSplitsRoleUI();
      renderDossierDiscipline(state.currentAuditData);
      fetchTacticalSplits();
    });
  }

  if (splitsRoleBowlBtn) {
    splitsRoleBowlBtn.addEventListener('click', () => {
      state.splitsRole = 'bowl';
      updateSplitsRoleUI();
      renderDossierDiscipline(state.currentAuditData);
      fetchTacticalSplits();
    });
  }

  // --- Batter Presets and Multi-select Handlers ---
  function updateBatterPillUI() {
    batterArchetypePills.forEach(pill => {
      const type = pill.getAttribute('data-type');
      if (state.splitsBowlerTypes.includes(type)) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });

    const sel = state.splitsBowlerTypes;
    if (splitsSelectionCount) {
      splitsSelectionCount.textContent = `${sel.length}/8`;
    }

    if (batterSplitsPresetSelect) {
      if (sel.length === ALL_BOWLER_ARCHETYPES.length) {
        batterSplitsPresetSelect.value = 'all';
      } else if (sel.length === 2 && sel.includes('LAF') && sel.includes('RAF')) {
        batterSplitsPresetSelect.value = 'express';
      } else if (sel.length === 4 && sel.includes('LAF') && sel.includes('RAF') && sel.includes('LAM') && sel.includes('RAM')) {
        batterSplitsPresetSelect.value = 'pace';
      } else if (sel.length === 4 && sel.includes('SLA') && sel.includes('OFF_SPIN') && sel.includes('WRIST_SPIN') && sel.includes('LEFT_WRIST_SPIN')) {
        batterSplitsPresetSelect.value = 'spin';
      } else if (sel.length === 2 && sel.includes('SLA') && sel.includes('OFF_SPIN')) {
        batterSplitsPresetSelect.value = 'fingerspin';
      } else if (sel.length === 2 && sel.includes('WRIST_SPIN') && sel.includes('LEFT_WRIST_SPIN')) {
        batterSplitsPresetSelect.value = 'wristspin';
      } else {
        batterSplitsPresetSelect.value = 'custom';
      }
    }
  }

  if (batterSplitsPresetSelect) {
    batterSplitsPresetSelect.addEventListener('change', () => {
      const preset = batterSplitsPresetSelect.value;
      if (preset === 'all') {
        state.splitsBowlerTypes = [...ALL_BOWLER_ARCHETYPES];
      } else if (preset === 'express') {
        state.splitsBowlerTypes = ['LAF', 'RAF'];
      } else if (preset === 'pace') {
        state.splitsBowlerTypes = ['LAF', 'RAF', 'LAM', 'RAM'];
      } else if (preset === 'spin') {
        state.splitsBowlerTypes = ['SLA', 'OFF_SPIN', 'WRIST_SPIN', 'LEFT_WRIST_SPIN'];
      } else if (preset === 'fingerspin') {
        state.splitsBowlerTypes = ['SLA', 'OFF_SPIN'];
      } else if (preset === 'wristspin') {
        state.splitsBowlerTypes = ['WRIST_SPIN', 'LEFT_WRIST_SPIN'];
      }
      updateBatterPillUI();
      fetchTacticalSplits();
    });
  }

  if (btnSplitsSelectAll) {
    btnSplitsSelectAll.addEventListener('click', () => {
      state.splitsBowlerTypes = [...ALL_BOWLER_ARCHETYPES];
      updateBatterPillUI();
      fetchTacticalSplits();
    });
  }

  if (btnSplitsClear) {
    btnSplitsClear.addEventListener('click', () => {
      state.splitsBowlerTypes = ['LAF'];
      updateBatterPillUI();
      fetchTacticalSplits();
    });
  }

  batterArchetypePills.forEach(pill => {
    pill.addEventListener('click', () => {
      const type = pill.getAttribute('data-type');
      if (state.splitsBowlerTypes.length === ALL_BOWLER_ARCHETYPES.length) {
        state.splitsBowlerTypes = [type];
      } else if (state.splitsBowlerTypes.includes(type)) {
        state.splitsBowlerTypes = state.splitsBowlerTypes.filter(t => t !== type);
        if (state.splitsBowlerTypes.length === 0) {
          state.splitsBowlerTypes = [...ALL_BOWLER_ARCHETYPES];
        }
      } else {
        state.splitsBowlerTypes.push(type);
      }
      updateBatterPillUI();
      fetchTacticalSplits();
    });
  });

  // --- Bowler Presets and Multi-select Handlers ---
  function updateBowlerPillUI() {
    bowlerHandPills.forEach(pill => {
      const hand = pill.getAttribute('data-hand');
      if (state.splitsBatterHands.includes(hand)) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });

    bowlerPhasePills.forEach(pill => {
      const phase = pill.getAttribute('data-phase');
      if (state.splitsPhases.includes(phase)) {
        pill.classList.add('active');
      } else {
        pill.classList.remove('active');
      }
    });

    const isAllH = state.splitsBatterHands.length === ALL_BATTER_HANDS.length;
    const isAllP = state.splitsPhases.length === ALL_PHASES.length;

    if (bowlerSplitsPresetSelect) {
      if (isAllH && isAllP) {
        bowlerSplitsPresetSelect.value = 'all';
      } else if (state.splitsBatterHands.length === 1 && state.splitsBatterHands.includes('RHB') && isAllP) {
        bowlerSplitsPresetSelect.value = 'rhb';
      } else if (state.splitsBatterHands.length === 1 && state.splitsBatterHands.includes('LHB') && isAllP) {
        bowlerSplitsPresetSelect.value = 'lhb';
      } else if (isAllH && state.splitsPhases.length === 1 && state.splitsPhases.includes('Powerplay')) {
        bowlerSplitsPresetSelect.value = 'powerplay';
      } else if (isAllH && state.splitsPhases.length === 1 && state.splitsPhases.includes('Death')) {
        bowlerSplitsPresetSelect.value = 'death';
      } else {
        bowlerSplitsPresetSelect.value = 'custom';
      }
    }
  }

  if (bowlerSplitsPresetSelect) {
    bowlerSplitsPresetSelect.addEventListener('change', () => {
      const preset = bowlerSplitsPresetSelect.value;
      if (preset === 'all') {
        state.splitsBatterHands = [...ALL_BATTER_HANDS];
        state.splitsPhases = [...ALL_PHASES];
      } else if (preset === 'rhb') {
        state.splitsBatterHands = ['RHB'];
        state.splitsPhases = [...ALL_PHASES];
      } else if (preset === 'lhb') {
        state.splitsBatterHands = ['LHB'];
        state.splitsPhases = [...ALL_PHASES];
      } else if (preset === 'powerplay') {
        state.splitsBatterHands = [...ALL_BATTER_HANDS];
        state.splitsPhases = ['Powerplay'];
      } else if (preset === 'death') {
        state.splitsBatterHands = [...ALL_BATTER_HANDS];
        state.splitsPhases = ['Death'];
      }
      updateBowlerPillUI();
      fetchTacticalSplits();
    });
  }

  if (btnBowlerSplitsReset) {
    btnBowlerSplitsReset.addEventListener('click', () => {
      state.splitsBatterHands = [...ALL_BATTER_HANDS];
      state.splitsPhases = [...ALL_PHASES];
      updateBowlerPillUI();
      fetchTacticalSplits();
    });
  }

  bowlerHandPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const hand = pill.getAttribute('data-hand');
      if (state.splitsBatterHands.length === ALL_BATTER_HANDS.length) {
        state.splitsBatterHands = [hand];
      } else if (state.splitsBatterHands.includes(hand)) {
        state.splitsBatterHands = state.splitsBatterHands.filter(h => h !== hand);
        if (state.splitsBatterHands.length === 0) {
          state.splitsBatterHands = [...ALL_BATTER_HANDS];
        }
      } else {
        state.splitsBatterHands.push(hand);
      }
      updateBowlerPillUI();
      fetchTacticalSplits();
    });
  });

  bowlerPhasePills.forEach(pill => {
    pill.addEventListener('click', () => {
      const phase = pill.getAttribute('data-phase');
      if (state.splitsPhases.length === ALL_PHASES.length) {
        state.splitsPhases = [phase];
      } else if (state.splitsPhases.includes(phase)) {
        state.splitsPhases = state.splitsPhases.filter(p => p !== phase);
        if (state.splitsPhases.length === 0) {
          state.splitsPhases = [...ALL_PHASES];
        }
      } else {
        state.splitsPhases.push(phase);
      }
      updateBowlerPillUI();
      fetchTacticalSplits();
    });
  });

  // --- Fetch API Splits ---
  async function fetchTacticalSplits() {
    const isBat = (state.splitsRole === 'bat');
    const typesParam = isBat ? (state.splitsBowlerTypes.length === ALL_BOWLER_ARCHETYPES.length ? 'ALL' : state.splitsBowlerTypes.join(',')) : 'ALL';
    const handsParam = !isBat ? (state.splitsBatterHands.length === ALL_BATTER_HANDS.length ? 'ALL' : state.splitsBatterHands.join(',')) : 'ALL';
    const phasesParam = !isBat ? (state.splitsPhases.length === ALL_PHASES.length ? 'ALL' : state.splitsPhases.join(',')) : 'ALL';

    try {
      const url = `/api/player/splits?name=${encodeURIComponent(state.currentPlayer)}&role=${state.splitsRole}&tournament=${state.currentTournament}&types=${encodeURIComponent(typesParam)}&hands=${encodeURIComponent(handsParam)}&phases=${encodeURIComponent(phasesParam)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error('Could not fetch tactical matchup splits');
      const data = await res.json();
      renderSplitsDashboard(data);
    } catch (err) {
      console.error(err);
      showToast(err.message, 'warning');
    }
  }

  // --- Render Dashboard ---
  function renderSplitsDashboard(data) {
    const isBat = (data.role === 'Batter');
    const s = data.summary || {};

    // 1. Badge & Subtitle
    if (splitsActiveCountBadge) {
      if (isBat) {
        if (data.is_all) {
          splitsActiveCountBadge.textContent = 'All 8 Bowler Types Active';
        } else {
          splitsActiveCountBadge.textContent = `${data.selected_types.length} Types: ${data.selected_types.join(', ')}`;
        }
      } else {
        if (data.is_all) {
          splitsActiveCountBadge.textContent = 'All Batters & Phases Active';
        } else {
          splitsActiveCountBadge.textContent = `${data.selected_hands.join('+')} • ${data.selected_phases.join('+')}`;
        }
      }
    }

    // 2. 6 KPI Tiles
    if (splitsKpiGrid) {
      if (isBat) {
        splitsKpiGrid.innerHTML = `
          <div class="split-kpi-card">
            <div class="split-kpi-val highlight-blue">${(s.runs || 0).toLocaleString()}</div>
            <div class="split-kpi-lbl">Runs Scored</div>
            <div class="split-kpi-sub">in ${(s.balls || 0).toLocaleString()} balls</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val highlight-gold">${fmt(s.sr, 1)}</div>
            <div class="split-kpi-lbl">Strike Rate</div>
            <div class="split-kpi-sub">${(s.sr || 0) >= 135 ? 'Above Par (135)' : 'Below Par (135)'}</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val highlight-green">${fmt(s.avg, 1)}</div>
            <div class="split-kpi-lbl">Batting Average</div>
            <div class="split-kpi-sub">${s.dismissals || 0} Dismissals</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val">${fmt(s.dot_pct, 1)}%</div>
            <div class="split-kpi-lbl">Dot Ball %</div>
            <div class="split-kpi-sub">${(s.dots || 0).toLocaleString()} dots</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val highlight-gold">${s.boundaries || 0}</div>
            <div class="split-kpi-lbl">Boundaries</div>
            <div class="split-kpi-sub">${s.fours || 0}x4, ${s.sixes || 0}x6 (${fmt(s.boundary_pct, 1)}%)</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val">${fmt(s.bpd, 1)}</div>
            <div class="split-kpi-lbl">Balls Per Out</div>
            <div class="split-kpi-sub">${(s.dismissals || 0) > 0 ? `Out every ${fmt(s.bpd, 0, '0')}b` : 'Never Dismissed'}</div>
          </div>
        `;
      } else {
        splitsKpiGrid.innerHTML = `
          <div class="split-kpi-card">
            <div class="split-kpi-val highlight-red">${s.wickets || 0}</div>
            <div class="split-kpi-lbl">Wickets Taken</div>
            <div class="split-kpi-sub">in ${s.overs || '0.0'} ov (${s.balls || 0}b)</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val highlight-green">${fmt(s.econ, 2)}</div>
            <div class="split-kpi-lbl">Economy Rate</div>
            <div class="split-kpi-sub">${(s.econ || 0) <= 7.5 ? 'Elite Containment' : 'Runs per 6 balls'}</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val highlight-gold">${fmt(s.avg, 1)}</div>
            <div class="split-kpi-lbl">Bowling Average</div>
            <div class="split-kpi-sub">Runs conceded / wkt</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val highlight-blue">${fmt(s.sr, 1)}</div>
            <div class="split-kpi-lbl">Bowling SR</div>
            <div class="split-kpi-sub">Balls bowled / wkt</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val">${fmt(s.dot_pct, 1)}%</div>
            <div class="split-kpi-lbl">Dot Choke %</div>
            <div class="split-kpi-sub">${(s.dots || 0).toLocaleString()} dot deliveries</div>
          </div>
          <div class="split-kpi-card">
            <div class="split-kpi-val">${(s.runs || 0).toLocaleString()}</div>
            <div class="split-kpi-lbl">Runs Conceded</div>
            <div class="split-kpi-sub">${s.boundaries || 0} bnds conceded</div>
          </div>
        `;
      }
    }

    // 2.5 Comparative Visual Shootout Scorecard
    const visualCard = document.getElementById('splitsVisualCard');
    const compImg = document.getElementById('splitsComparisonImg');
    const chartTitle = document.getElementById('splitsVisualChartTitle');
    const chartTag = document.getElementById('splitsVisualTag');

    if (data.image_b64 && compImg && visualCard) {
      compImg.src = `data:image/png;base64,${data.image_b64}`;
      visualCard.style.display = 'block';

      if (isBat) {
        if (data.is_all) {
          chartTitle.textContent = `Performance Splits Across 8 Bowling Styles — ${data.cric_name}`;
          chartTag.textContent = 'All Archetypes';
        } else if (data.selected_types.length >= 2) {
          chartTitle.textContent = `Performance Splits vs ${data.selected_types.join(', ')} — ${data.cric_name}`;
          chartTag.textContent = `${data.selected_types.length} Styles Selected`;
        } else {
          chartTitle.textContent = `Phase Analysis vs ${data.selected_types.join(', ')} — ${data.cric_name}`;
          chartTag.textContent = 'Single Style Phase Analysis';
        }
      } else {
        if (data.is_all) {
          chartTitle.textContent = `Performance Splits vs RHB & LHB Batters — ${data.cric_name}`;
          chartTag.textContent = 'RHB vs LHB';
        } else {
          chartTitle.textContent = `Tactical Bowling Analysis — ${data.cric_name}`;
          chartTag.textContent = 'Tactical Splits';
        }
      }
    } else if (visualCard) {
      visualCard.style.display = 'none';
    }

    // 3. Left Panel: Phase Breakdown
    if (splitsPhaseBars) {
      const phases = ['Powerplay', 'Middle', 'Death'];
      const phClasses = { Powerplay: 'pp', Middle: 'mid', Death: 'dth' };

      if (isBat) {
        splitsPhaseTitle.textContent = 'Phase Breakdown vs Selected Bowler Types';
        splitsPhaseBars.innerHTML = phases.map(ph => {
          const p = (data.phases && data.phases[ph]) ? data.phases[ph] : { balls: 0, runs: 0, dismissals: 0, sr: 0, dot_pct: 0 };
          const fillWidth = Math.min(100, Math.max(8, ((p.sr || 0) / 200) * 100));
          return `
            <div class="splits-phase-bar-item">
              <div class="phase-bar-header">
                <span>${ph} (Overs ${ph === 'Powerplay' ? '1–6' : (ph === 'Middle' ? '7–15' : '16–20')})</span>
                <span style="font-family:var(--font-mono, monospace); color:var(--text-secondary); font-size:0.75rem;">
                  SR: <strong style="color:var(--text-primary); font-size:0.85rem;">${fmt(p.sr, 1)}</strong> • ${p.runs || 0}r (${p.balls || 0}b) • ${p.dismissals || 0} outs • ${fmt(p.dot_pct, 1)}% dots
                </span>
              </div>
              <div class="phase-bar-track">
                <div class="phase-bar-fill ${phClasses[ph]}" style="width: ${fillWidth}%"></div>
              </div>
            </div>
          `;
        }).join('');
      } else {
        splitsPhaseTitle.textContent = 'Phase Breakdown vs Selected Batter Profiles';
        splitsPhaseBars.innerHTML = phases.map(ph => {
          const p = (data.phases && data.phases[ph]) ? data.phases[ph] : { balls: 0, runs: 0, wickets: 0, econ: 0, dot_pct: 0 };
          const fillWidth = Math.min(100, Math.max(8, (12 - (p.econ || 0)) * 10));
          return `
            <div class="splits-phase-bar-item">
              <div class="phase-bar-header">
                <span>${ph} (Overs ${ph === 'Powerplay' ? '1–6' : (ph === 'Middle' ? '7–15' : '16–20')})</span>
                <span style="font-family:var(--font-mono, monospace); color:var(--text-secondary); font-size:0.75rem;">
                  Econ: <strong style="color:var(--text-primary); font-size:0.85rem;">${fmt(p.econ, 2)}</strong> • ${p.wickets || 0} wkts • ${p.runs || 0}r (${p.balls || 0}b) • ${fmt(p.dot_pct, 1)}% dots
                </span>
              </div>
              <div class="phase-bar-track">
                <div class="phase-bar-fill ${phClasses[ph]}" style="width: ${fillWidth}%"></div>
              </div>
            </div>
          `;
        }).join('');
      }
    }

    // 4. Right Panel: Matchup Breakdown & Top Opponents
    if (splitsMatchupContent) {
      if (isBat) {
        splitsMatchupTitle.textContent = 'Detailed Archetype Breakdown & Top Bowlers Faced';
        const archList = data.archetypes || [];
        const topOpp = data.top_opponents || [];

        let html = '';
        if (archList.length > 0) {
          html += `
            <table class="splits-table" style="margin-bottom: 12px;">
              <thead>
                <tr>
                  <th>Archetype</th>
                  <th>Balls</th>
                  <th>Runs</th>
                  <th>Outs</th>
                  <th>SR</th>
                  <th>Dot %</th>
                  <th>Avg</th>
                </tr>
              </thead>
              <tbody>
                ${archList.map(a => `
                  <tr>
                    <td><strong>${a.archetype}</strong></td>
                    <td>${a.balls || 0}</td>
                    <td>${a.runs || 0}</td>
                    <td>${a.dismissals || 0}</td>
                    <td><strong style="color:${(a.sr || 0) >= 135 ? 'var(--primary-blue)' : 'var(--text-secondary)'}">${fmt(a.sr, 1)}</strong></td>
                    <td>${fmt(a.dot_pct, 1)}%</td>
                    <td>${fmt(a.avg, 1)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `;
        }

        if (topOpp.length > 0) {
          html += `
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; color:var(--text-muted); margin: 8px 0 4px 0;">Top Individual Bowlers Faced in Selection:</div>
            <table class="splits-table">
              <thead>
                <tr>
                  <th>Bowler</th>
                  <th>Style</th>
                  <th>Balls</th>
                  <th>Runs</th>
                  <th>Outs</th>
                  <th>SR</th>
                </tr>
              </thead>
              <tbody>
                ${topOpp.map(o => `
                  <tr>
                    <td><strong>${o.bowler}</strong></td>
                    <td><span style="font-size:0.72rem; color:var(--text-secondary);">${o.bowler_archetype || ''}</span></td>
                    <td>${o.balls || 0}</td>
                    <td>${o.runs || 0}</td>
                    <td><strong style="color:${(o.dismissals || 0) > 0 ? '#EF4444' : 'inherit'}">${o.dismissals || 0}</strong></td>
                    <td>${fmt(o.sr, 1)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `;
        }

        splitsMatchupContent.innerHTML = html || '<div style="color:var(--text-secondary); font-size:0.8rem;">No deliveries recorded against chosen bowler types.</div>';

      } else {
        splitsMatchupTitle.textContent = 'Batter Stance Record & Top Batters Faced';
        const handsList = data.hands || [];
        const topOpp = data.top_opponents || [];

        let html = '';
        if (handsList.length > 0) {
          html += `
            <table class="splits-table" style="margin-bottom: 12px;">
              <thead>
                <tr>
                  <th>Batter Stance</th>
                  <th>Balls</th>
                  <th>Runs</th>
                  <th>Wkts</th>
                  <th>Econ</th>
                  <th>Avg</th>
                  <th>SR</th>
                  <th>Dot %</th>
                </tr>
              </thead>
              <tbody>
                ${handsList.map(h => `
                  <tr>
                    <td><strong>vs ${h.hand}</strong></td>
                    <td>${h.balls || 0}</td>
                    <td>${h.runs || 0}</td>
                    <td><strong style="color:#EF4444">${h.wickets || 0}</strong></td>
                    <td><strong>${fmt(h.econ, 2)}</strong></td>
                    <td>${fmt(h.avg, 1)}</td>
                    <td>${fmt(h.sr, 1)}</td>
                    <td>${fmt(h.dot_pct, 1)}%</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `;
        }

        if (topOpp.length > 0) {
          html += `
            <div style="font-size:0.72rem; font-weight:700; text-transform:uppercase; color:var(--text-muted); margin: 8px 0 4px 0;">Top Individual Batters Faced in Selection:</div>
            <table class="splits-table">
              <thead>
                <tr>
                  <th>Batter</th>
                  <th>Hand</th>
                  <th>Balls</th>
                  <th>Runs</th>
                  <th>Wkts</th>
                  <th>Econ</th>
                </tr>
              </thead>
              <tbody>
                ${topOpp.map(o => `
                  <tr>
                    <td><strong>${o.striker}</strong></td>
                    <td><span style="font-size:0.72rem; color:var(--text-secondary);">${o.hand || ''}</span></td>
                    <td>${o.balls || 0}</td>
                    <td>${o.runs || 0}</td>
                    <td><strong style="color:#EF4444">${o.wickets || 0}</strong></td>
                    <td>${fmt(o.econ, 2)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `;
        }

        splitsMatchupContent.innerHTML = html || '<div style="color:var(--text-secondary); font-size:0.8rem;">No deliveries recorded against chosen batter profiles.</div>';
      }
    }
  }

  // ==========================================================================
  // 6. API FETCH & RENDER: TAB 2 (BATTER WAGON WHEEL)
  // ==========================================================================
  if (wagonArchetypeSelect) {
    wagonArchetypeSelect.addEventListener('change', () => {
      state.wagonBowlerType = wagonArchetypeSelect.value;
      loadWagonWheel(state.currentPlayer, state.wagonBowlerType, state.wagonPhase);
    });
  }

  if (wagonPhaseSelect) {
    wagonPhaseSelect.addEventListener('change', () => {
      state.wagonPhase = wagonPhaseSelect.value;
      loadWagonWheel(state.currentPlayer, state.wagonBowlerType, state.wagonPhase);
    });
  }

  if (refreshWagonBtn) {
    refreshWagonBtn.addEventListener('click', () => {
      if (wagonArchetypeSelect) state.wagonBowlerType = wagonArchetypeSelect.value;
      if (wagonPhaseSelect) state.wagonPhase = wagonPhaseSelect.value;
      loadWagonWheel(state.currentPlayer, state.wagonBowlerType, state.wagonPhase);
    });
  }

  async function loadWagonWheel(playerName, bowlerType, phase = 'ALL') {
    const scopeLabel = `${bowlerType !== 'ALL' ? bowlerType : 'All Bowlers'}${phase !== 'ALL' ? ` (${phase})` : ''}`;
    showLoading(`Generating pro wagon wheel for ${playerName} vs [${scopeLabel}]...`);
    try {
      const res = await fetch(`/api/player/wagon?name=${encodeURIComponent(playerName)}&bowler_type=${encodeURIComponent(bowlerType)}&phase=${encodeURIComponent(phase)}&tournament=${encodeURIComponent(state.currentTournament)}`);
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.error || `Could not generate wagon wheel for ${playerName} vs ${scopeLabel}`);
      }
      const data = await res.json();
      renderWagonWheel(data);
    } catch (err) {
      showToast(err.message, 'warning');
    } finally {
      hideLoading();
    }
  }

  function renderWagonWheel(data) {
    // 1. Image
    const imgEl = document.getElementById('wagonImg');
    imgEl.src = `data:image/png;base64,${data.image_b64}`;

    // 2. Titles and badges
    const bowlTypeStr = (data.vs_bowler_type === 'ALL' ? 'All Bowlers' : (data.vs_bowler_type === 'PACE' ? 'All Pace' : (data.vs_bowler_type === 'SPIN' ? 'All Spin' : `vs ${data.vs_bowler_type}`)));
    const phaseStr = (data.phase && data.phase !== 'ALL') ? ` • ${data.phase} Phase` : '';
    const scopeStr = `${bowlTypeStr}${phaseStr}`;
    document.getElementById('wagonVisualTitle').textContent = `${data.cric_name} (${data.is_lhb ? 'LHB' : 'RHB'}) — Scoring Distribution (${scopeStr})`;

    if (wagonArchetypeSelect && data.vs_bowler_type) {
      wagonArchetypeSelect.value = data.vs_bowler_type;
    }
    if (wagonPhaseSelect && data.phase) {
      wagonPhaseSelect.value = data.phase;
    }

    if (data.dominant_sector) {
      document.getElementById('wagonDominantBadge').textContent = `Dominant: ${data.dominant_sector.FullName || ''} (${fmt(data.dominant_sector.Run_Pct, 1)}%)`;
    }

    // 3. Quick Stats
    document.getElementById('wStatRuns').textContent = (data.total_runs || 0).toLocaleString();
    document.getElementById('wStatBalls').textContent = (data.total_balls || 0).toLocaleString();
    document.getElementById('wStatSR').textContent = fmt(data.overall_sr, 1);
    
    const dotPct = fmt(((data.total_dots || 0) * 100) / Math.max(1, data.total_balls || 1), 1);
    const bndPct = fmt((((data.total_fours || 0) + (data.total_sixes || 0)) * 100) / Math.max(1, data.total_balls || 1), 1);
    document.getElementById('wStatDots').textContent = `${dotPct}%`;
    document.getElementById('wStatBnd').textContent = `${bndPct}%`;

    // 4. Sector Table
    const tbody = document.getElementById('wagonSectorBody');
    tbody.innerHTML = (data.summary || []).map(r => `
      <tr>
        <td>
          <span style="display:inline-block; width:10px; height:10px; border-radius:50%; background:${r.Color}; margin-right:8px;"></span>
          <strong>${r.Sector}</strong> <span style="font-size:0.75rem; color:var(--text-muted);">(${r.FullName})</span>
        </td>
        <td>${Math.round(r.Runs || 0)}</td>
        <td><strong>${fmt(r.Run_Pct, 1)}%</strong></td>
        <td>${r.Fours || 0}</td>
        <td>${r.Sixes || 0}</td>
      </tr>
    `).join('');
  }

  // ==========================================================================
  // 7. API FETCH & RENDER: TAB 3 (BOWLER DEFENSIVE RADIAL WHEEL)
  // ==========================================================================
  const defDisplayGridEl = document.querySelector('#tab-defensive .wagon-display-grid');
  const originalDefGridHTML = defDisplayGridEl ? defDisplayGridEl.innerHTML : '';

  if (defPhaseSelect) {
    defPhaseSelect.addEventListener('change', () => {
      state.defPhase = defPhaseSelect.value;
      loadDefensiveWheel(state.currentPlayer, state.defPhase, state.defHand);
    });
  }

  if (defHandSelect) {
    defHandSelect.addEventListener('change', () => {
      state.defHand = defHandSelect.value;
      loadDefensiveWheel(state.currentPlayer, state.defPhase, state.defHand);
    });
  }

  if (refreshDefBtn) {
    refreshDefBtn.addEventListener('click', () => {
      if (defPhaseSelect) state.defPhase = defPhaseSelect.value;
      if (defHandSelect) state.defHand = defHandSelect.value;
      loadDefensiveWheel(state.currentPlayer, state.defPhase, state.defHand);
    });
  }

  async function loadDefensiveWheel(playerName, phase, hand) {
    showLoading(`Computing defensive radial map for ${playerName} (${phase} overs)...`);
    try {
      const res = await fetch(`/api/player/defensive_wheel?name=${encodeURIComponent(playerName)}&phase=${phase}&hand=${hand}&tournament=${state.currentTournament}`);
      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        const msg = errJson.error || `${playerName} has no bowling records available.`;
        renderDefensiveEmptyState(playerName, msg);
        return;
      }
      const data = await res.json();
      renderDefensiveWheel(data);
    } catch (err) {
      renderDefensiveEmptyState(playerName, err.message);
    } finally {
      hideLoading();
    }
  }

  function renderDefensiveEmptyState(playerName, message) {
    if (!defDisplayGridEl) return;
    defDisplayGridEl.innerHTML = `
      <div style="grid-column: 1 / -1; background: var(--bg-surface, #0F172A); border: 1px solid var(--border-color, #1E293B); border-radius: 14px; padding: 48px 24px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.35);">
        <h3 style="color: #F8FAFC; font-size: 1.35rem; font-weight: 700; margin-bottom: 10px;">Specialist Batter — No Bowling Deliveries</h3>
        <p style="color: #94A3B8; font-size: 0.92rem; max-width: 580px; margin: 0 auto 20px; line-height: 1.6;">
          <strong>${playerName}</strong> is a specialist batter who has faced deliveries off the bat but has <strong>never bowled a single delivery</strong> in this competition.
          <br><span style="font-size: 0.82rem; color: #64748B;">Defensive Radial Maps are exclusively generated for bowlers and all-rounders to evaluate runs conceded, defensive fortresses, and wickets induced.</span>
        </p>
        <button class="action-btn" style="background: linear-gradient(135deg, #10B981, #059669); color: white; padding: 10px 22px; font-weight: 700; border-radius: 8px; border: none; cursor: pointer; display: inline-flex; align-items: center; gap: 8px;" onclick="document.querySelector('[data-tab=\\'tab-wagon\\']').click()">
          <span>View ${playerName}'s Batting Wagon Wheel</span> <span>➔</span>
        </button>
      </div>
    `;
  }

  function renderDefensiveWheel(data) {
    if (defDisplayGridEl && !document.getElementById('defImg')) {
      defDisplayGridEl.innerHTML = originalDefGridHTML;
    }

    // 1. Image
    const imgEl = document.getElementById('defImg');
    if (imgEl) imgEl.src = `data:image/png;base64,${data.image_b64}`;

    // 2. Titles and Badges
    const scopeStr = data.phase === 'ALL' ? 'All Phases' : `Phase: ${data.phase}`;
    document.getElementById('defVisualTitle').textContent = `${data.cric_name} — Defensive Field Distribution (${scopeStr})`;

    if (defPhaseSelect && data.phase) {
      defPhaseSelect.value = data.phase;
    }
    if (defHandSelect && data.hand) {
      defHandSelect.value = data.hand;
    }

    if (data.fortress_sector) {
      document.getElementById('defFortressBadge').textContent = `Most Restrictive: ${data.fortress_sector.FullName || ''} (${fmt(data.fortress_sector.Conceded_Pct, 1)}%)`;
      document.getElementById('defFortressName').textContent = data.fortress_sector.FullName || '';
      document.getElementById('defFortressDetail').textContent = `Only ${fmt(data.fortress_sector.Conceded_Pct, 1)}% runs conceded • ${data.fortress_sector.Wickets || 0} Wickets Induced`;
    }

    if (data.leak_sector) {
      document.getElementById('defLeakName').textContent = data.leak_sector.FullName || '';
      document.getElementById('defLeakDetail').textContent = `${fmt(data.leak_sector.Conceded_Pct, 1)}% conceded • Opponents scored ${Math.round(data.leak_sector.RunsConceded || 0)} runs`;
    }

    // 3. Quick Stats
    document.getElementById('defStatRuns').textContent = Math.round(data.total_runs_conceded || 0).toLocaleString();
    document.getElementById('defStatWkts').textContent = data.total_wkts || 0;
    document.getElementById('defStatEcon').textContent = fmt(data.overall_econ, 2);
    document.getElementById('defStatSR').textContent = fmt(data.overall_sr, 1);

    // 4. Sector Table
    const tbody = document.getElementById('defSectorBody');
    tbody.innerHTML = (data.summary || []).map((r, i) => {
      const tag = i < 2 ? '<span style="color:#10B981; font-weight:600;">Restrictive</span>' : (i >= (data.summary.length - 2) ? '<span style="color:#F43F5E; font-weight:600;">High Concession</span>' : '<span style="color:#94A3B8;">Neutral</span>');
      return `
        <tr>
          <td><strong>${r.Sector}</strong> <span style="font-size:0.75rem; color:var(--text-muted);">(${r.FullName})</span></td>
          <td>${Math.round(r.RunsConceded || 0)}</td>
          <td><strong>${fmt(r.Conceded_Pct, 1)}%</strong></td>
          <td>${r.Wickets || 0}</td>
          <td>${tag}</td>
        </tr>
      `;
    }).join('');
  }

  // ==========================================================================
  // 8. API FETCH & RENDER: TAB 4 (HEAD-TO-HEAD DUEL & COMPARE)
  // ==========================================================================
  function updateCompareModeLabels() {
    const rawP1 = compP1Input.value.trim() || 'P1';
    const rawP2 = compP2Input.value.trim() || 'P2';
    const p1 = rawP1.split(' ').pop();
    const p2 = rawP2.split(' ').pop();
    if (optBatBowl) optBatBowl.textContent = `${p1} (Bat) vs ${p2} (Bowl)`;
    if (optBowlBat) optBowlBat.textContent = `${p1} (Bowl) vs ${p2} (Bat)`;
  }

  compP1Input.addEventListener('input', updateCompareModeLabels);
  compP2Input.addEventListener('input', updateCompareModeLabels);

  if (compareModeSelect) {
    compareModeSelect.addEventListener('change', () => {
      state.compMode = compareModeSelect.value;
      if (state.compMode === 'bat_vs_bat') {
        if (compareArchetypeWrap) compareArchetypeWrap.style.display = 'block';
        if (compareHandWrap) compareHandWrap.style.display = 'none';
      } else if (state.compMode === 'bowl_vs_bowl') {
        if (compareArchetypeWrap) compareArchetypeWrap.style.display = 'none';
        if (compareHandWrap) compareHandWrap.style.display = 'block';
      } else {
        if (compareArchetypeWrap) compareArchetypeWrap.style.display = 'none';
        if (compareHandWrap) compareHandWrap.style.display = 'none';
      }
      loadComparison(compP1Input.value.trim(), compP2Input.value.trim(), state.compMode, state.compArchetype, state.compHand);
    });
  }

  if (compareArchetypeSelect) {
    compareArchetypeSelect.addEventListener('change', () => {
      state.compArchetype = compareArchetypeSelect.value || 'ALL';
      loadComparison(compP1Input.value.trim(), compP2Input.value.trim(), state.compMode, state.compArchetype, state.compHand);
    });
  }

  if (compareHandSelect) {
    compareHandSelect.addEventListener('change', () => {
      state.compHand = compareHandSelect.value || 'ALL';
      loadComparison(compP1Input.value.trim(), compP2Input.value.trim(), state.compMode, state.compArchetype, state.compHand);
    });
  }

  if (comparePresetSelect) {
    comparePresetSelect.addEventListener('change', () => {
      const selected = comparePresetSelect.options[comparePresetSelect.selectedIndex];
      if (!selected || !selected.value) return;
      const p1 = selected.getAttribute('data-p1');
      const p2 = selected.getAttribute('data-p2');
      if (!p1 || !p2) return;

      state.compP1 = p1;
      state.compP2 = p2;
      const arch = selected.getAttribute('data-archetype') || 'ALL';
      const hand = selected.getAttribute('data-hand') || 'ALL';
      const mode = selected.getAttribute('data-mode') || 'auto';
      state.compArchetype = arch;
      state.compHand = hand;
      state.compMode = mode;
      compP1Input.value = state.compP1;
      compP2Input.value = state.compP2;

      if (compareModeSelect) compareModeSelect.value = mode;
      if (compareArchetypeSelect) compareArchetypeSelect.value = arch;
      if (compareHandSelect) compareHandSelect.value = hand;

      if (mode === 'bat_vs_bat') {
        if (compareArchetypeWrap) compareArchetypeWrap.style.display = 'block';
        if (compareHandWrap) compareHandWrap.style.display = 'none';
      } else if (mode === 'bowl_vs_bowl') {
        if (compareArchetypeWrap) compareArchetypeWrap.style.display = 'none';
        if (compareHandWrap) compareHandWrap.style.display = 'block';
      } else {
        if (compareArchetypeWrap) compareArchetypeWrap.style.display = 'none';
        if (compareHandWrap) compareHandWrap.style.display = 'none';
      }

      updateCompareModeLabels();
      loadComparison(state.compP1, state.compP2, state.compMode, state.compArchetype, state.compHand);
    });
  }

  launchCompareBtn.addEventListener('click', () => {
    state.compP1 = compP1Input.value.trim();
    state.compP2 = compP2Input.value.trim();
    if (!state.compP1 || !state.compP2) {
      showToast('Please enter both player names to compare.', 'warning');
      return;
    }
    loadComparison(state.compP1, state.compP2, state.compMode, state.compArchetype, state.compHand);
  });

  async function loadComparison(p1, p2, mode = state.compMode, archetype = (state.compArchetype || 'ALL'), hand = (state.compHand || 'ALL')) {
    updateCompareModeLabels();
    let scopeTxt = '';
    if (mode === 'bowl_vs_bowl' && hand !== 'ALL') {
      scopeTxt = ` [vs ${hand}]`;
    } else if (mode === 'bat_vs_bat' && archetype !== 'ALL') {
      scopeTxt = ` [vs ${archetype}]`;
    }
    showLoading(`Comparing ${p1} vs ${p2} [${mode.toUpperCase()}]${scopeTxt}...`);
    try {
      const url = `/api/compare?player1=${encodeURIComponent(p1)}&player2=${encodeURIComponent(p2)}&mode=${encodeURIComponent(mode)}&vs_bowler_type=${encodeURIComponent(archetype)}&vs_batter_hand=${encodeURIComponent(hand)}&tournament=${encodeURIComponent(state.currentTournament)}`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Could not compare ${p1} and ${p2}`);
      const data = await res.json();
      renderComparison(data);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      hideLoading();
    }
  }

  function getAdvantageBadge(v1, v2, higherIsBetter = true, p1Label = 'P1', p2Label = 'P2') {
    if (v1 === v2 || isNaN(v1) || isNaN(v2)) {
      return '<span class="advantage-badge tie">Equal</span>';
    }
    const p1Wins = higherIsBetter ? (v1 > v2) : (v1 < v2);
    if (p1Wins) {
      const diff = Math.abs(v1 - v2);
      const diffStr = diff >= 10 ? Math.round(diff) : diff.toFixed(1);
      return `<span class="advantage-badge p1">▲ ${p1Label} (+${diffStr})</span>`;
    } else {
      const diff = Math.abs(v1 - v2);
      const diffStr = diff >= 10 ? Math.round(diff) : diff.toFixed(1);
      return `<span class="advantage-badge p2">▲ ${p2Label} (+${diffStr})</span>`;
    }
  }

  function renderComparison(data) {
    // 1. Image
    const imgEl = document.getElementById('compareImg');
    imgEl.src = `data:image/png;base64,${data.image_b64}`;

    // 2. Titles & duel badge
    const p1Name = data.player1.full_name || data.player1.cric_name;
    const p2Name = data.player2.full_name || data.player2.cric_name;
    const p1Short = p1Name.split(' ').pop();
    const p2Short = p2Name.split(' ').pop();

    const isBat = (data.comparison_type === 'batter_vs_batter');
    const isBowl = (data.comparison_type === 'bowler_vs_bowler');
    const isDuel = (data.comparison_type === 'batter_vs_bowler_duel');

    // Contextual Archetype / Stance dropdown visibility:
    // Only display vs Bowler Archetype dropdown when comparing Batter vs Batter.
    // Only display vs Batter Stance dropdown (LHB/RHB) when comparing Bowler vs Bowler.
    // Hide both during direct Batter vs Bowler duels!
    if (isBat) {
      if (compareArchetypeWrap) compareArchetypeWrap.style.display = 'block';
      if (compareHandWrap) compareHandWrap.style.display = 'none';
    } else if (isBowl) {
      if (compareArchetypeWrap) compareArchetypeWrap.style.display = 'none';
      if (compareHandWrap) compareHandWrap.style.display = 'block';
    } else {
      if (compareArchetypeWrap) compareArchetypeWrap.style.display = 'none';
      if (compareHandWrap) compareHandWrap.style.display = 'none';
    }

    if (compareModeSelect && state.compMode) {
      compareModeSelect.value = state.compMode;
    }
    if (compareArchetypeSelect && data.vs_bowler_type) {
      compareArchetypeSelect.value = data.vs_bowler_type;
    }
    if (compareHandSelect && data.vs_batter_hand) {
      compareHandSelect.value = data.vs_batter_hand;
    }

    let scopeStr = '';
    if (isBat && data.vs_bowler_type && data.vs_bowler_type !== 'ALL') {
      scopeStr = ` (vs ${data.vs_bowler_type})`;
    } else if (isBowl && data.vs_batter_hand && data.vs_batter_hand !== 'ALL') {
      scopeStr = ` (vs ${data.vs_batter_hand})`;
    }
    document.getElementById('compareTitle').textContent = `Player Comparison: ${p1Name} vs ${p2Name}${scopeStr}`;

    const typeBadge = document.getElementById('compareDuelTypeBadge');
    if (isBowl) {
      typeBadge.textContent = 'Bowler vs Bowler';
      typeBadge.className = 'header-tag fortress';
    } else if (isDuel) {
      typeBadge.textContent = 'Batter vs Bowler Duel';
      typeBadge.className = 'header-tag primary';
    } else {
      typeBadge.textContent = 'Batter vs Batter';
      typeBadge.className = 'header-tag';
    }

    // 3. Head-to-Head Dossier Card
    const h2hCard = document.getElementById('h2hDossierCard');
    const h2hRow = document.getElementById('h2hStatsRow');

    if (data.has_h2h && data.h2h_data) {
      h2hCard.style.display = 'block';
      const h = data.h2h_data;
      const titleEl = document.getElementById('h2hCardTitle');
      if (titleEl && h.striker && h.bowler) {
        titleEl.textContent = `Historical Head-to-Head: ${h.striker} (Bat) vs ${h.bowler} (Bowl)`;
      } else if (titleEl) {
        titleEl.textContent = `Historical Head-to-Head Matchup Record`;
      }
      h2hRow.innerHTML = `
        <div class="h2h-stat-tile">
          <div class="num highlight-blue">${h.runs}</div>
          <div class="lbl">Runs Scored</div>
        </div>
        <div class="h2h-stat-tile">
          <div class="num">${h.balls}</div>
          <div class="lbl">Balls Faced</div>
        </div>
        <div class="h2h-stat-tile">
          <div class="num highlight-blue">${fmt(h.sr, 1)}</div>
          <div class="lbl">Strike Rate</div>
        </div>
        <div class="h2h-stat-tile">
          <div class="num">${h.dots} <span style="font-size:0.8rem; color:var(--text-muted)">(${h.dot_pct}%)</span></div>
          <div class="lbl">Dot Balls</div>
        </div>
        <div class="h2h-stat-tile">
          <div class="num highlight-gold">${h.boundaries} <span style="font-size:0.8rem; color:var(--text-muted)">(${h.fours}x4, ${h.sixes}x6)</span></div>
          <div class="lbl">Boundaries</div>
        </div>
        <div class="h2h-stat-tile">
          <div class="num highlight-red">${h.dismissals}</div>
          <div class="lbl">Dismissals (Out)</div>
        </div>
      `;
    } else {
      h2hCard.style.display = 'none';
    }

    // 4. Overall Detailed Statistics Table
    const thP1 = document.getElementById('thCompPlayer1');
    const thP2 = document.getElementById('thCompPlayer2');
    const badgeFilter = document.getElementById('compareStatsFilterBadge');
    const metricsBody = document.getElementById('compareMetricsBody');

    if (thP1) thP1.textContent = p1Name;
    if (thP2) thP2.textContent = p2Name;
    if (badgeFilter) {
      if (isBat) {
        badgeFilter.textContent = (data.vs_bowler_type && data.vs_bowler_type !== 'ALL') ? `vs ${data.vs_bowler_type}` : 'All Bowler Types';
      } else if (isBowl) {
        badgeFilter.textContent = (data.vs_batter_hand && data.vs_batter_hand !== 'ALL') ? `vs ${data.vs_batter_hand}` : 'All Batters';
      } else {
        badgeFilter.textContent = 'Direct Head-to-Head Duel';
      }
    }

    if (metricsBody) {
      if (isBat) {
        const s1 = data.p1_stats || {};
        const s2 = data.p2_stats || {};

        const rows = [
          { name: 'Total Runs Scored', v1: s1.total_runs || 0, v2: s2.total_runs || 0, disp1: (s1.total_runs || 0).toLocaleString(), disp2: (s2.total_runs || 0).toLocaleString(), higher: true },
          { name: 'Balls Faced', v1: s1.total_balls || 0, v2: s2.total_balls || 0, disp1: (s1.total_balls || 0).toLocaleString(), disp2: (s2.total_balls || 0).toLocaleString(), higher: true },
          { name: 'Batting Strike Rate', v1: s1.overall_sr || 0, v2: s2.overall_sr || 0, disp1: (s1.overall_sr || 0).toFixed(1), disp2: (s2.overall_sr || 0).toFixed(1), higher: true },
          { name: 'Batting Average', v1: s1.overall_avg || 0, v2: s2.overall_avg || 0, disp1: (s1.overall_avg || 0).toFixed(1), disp2: (s2.overall_avg || 0).toFixed(1), higher: true },
          { name: 'Dot Ball %', v1: s1.dot_pct || 0, v2: s2.dot_pct || 0, disp1: `${(s1.dot_pct || 0).toFixed(1)}%`, disp2: `${(s2.dot_pct || 0).toFixed(1)}%`, higher: false },
          { name: 'Boundary Conversion %', v1: s1.bnd_pct || 0, v2: s2.bnd_pct || 0, disp1: `${(s1.bnd_pct || 0).toFixed(1)}%`, disp2: `${(s2.bnd_pct || 0).toFixed(1)}%`, higher: true },
          { name: 'Fours / Sixes Breakdown', v1: s1.total_boundaries || 0, v2: s2.total_boundaries || 0, disp1: `${s1.total_fours || 0}x4, ${s1.total_sixes || 0}x6`, disp2: `${s2.total_fours || 0}x4, ${s2.total_sixes || 0}x6`, higher: true },
          { name: 'Times Dismissed', v1: s1.total_outs || 0, v2: s2.total_outs || 0, disp1: `${s1.total_outs || 0} outs`, disp2: `${s2.total_outs || 0} outs`, higher: false }
        ];

        metricsBody.innerHTML = rows.map(r => `
          <tr>
            <td><strong>${r.name}</strong></td>
            <td><strong style="color:#38BDF8;">${r.disp1}</strong></td>
            <td><strong style="color:#F59E0B;">${r.disp2}</strong></td>
            <td>${getAdvantageBadge(r.v1, r.v2, r.higher, p1Short, p2Short)}</td>
          </tr>
        `).join('');

      } else if (isBowl) {
        const s1 = data.b1_stats || {};
        const s2 = data.b2_stats || {};

        const rows = [
          { name: 'Total Overs Bowled', v1: s1.total_overs || 0, v2: s2.total_overs || 0, disp1: `${(s1.total_overs || 0).toFixed(1)} ov`, disp2: `${(s2.total_overs || 0).toFixed(1)} ov`, higher: true },
          { name: 'Wickets Induced', v1: s1.total_wickets || 0, v2: s2.total_wickets || 0, disp1: `${s1.total_wickets || 0} wkts`, disp2: `${s2.total_wickets || 0} wkts`, higher: true },
          { name: 'Economy Rate (Lower = Better)', v1: s1.overall_econ || 0, v2: s2.overall_econ || 0, disp1: (s1.overall_econ || 0).toFixed(2), disp2: (s2.overall_econ || 0).toFixed(2), higher: false },
          { name: 'Bowling Strike Rate', v1: s1.overall_sr || 0, v2: s2.overall_sr || 0, disp1: (s1.overall_sr || 0).toFixed(1), disp2: (s2.overall_sr || 0).toFixed(1), higher: false },
          { name: 'Bowling Average', v1: s1.overall_avg || 0, v2: s2.overall_avg || 0, disp1: (s1.overall_avg || 0).toFixed(1), disp2: (s2.overall_avg || 0).toFixed(1), higher: false },
          { name: 'Dot Ball % (Higher = Better)', v1: s1.dot_pct || 0, v2: s2.dot_pct || 0, disp1: `${(s1.dot_pct || 0).toFixed(1)}%`, disp2: `${(s2.dot_pct || 0).toFixed(1)}%`, higher: true },
          { name: 'Total Runs Conceded', v1: s1.total_runs || 0, v2: s2.total_runs || 0, disp1: (s1.total_runs || 0).toLocaleString(), disp2: (s2.total_runs || 0).toLocaleString(), higher: false },
          { name: 'Boundaries Conceded', v1: s1.total_boundaries || 0, v2: s2.total_boundaries || 0, disp1: `${s1.total_boundaries || 0} bnd`, disp2: `${s2.total_boundaries || 0} bnd`, higher: false }
        ];

        metricsBody.innerHTML = rows.map(r => `
          <tr>
            <td><strong>${r.name}</strong></td>
            <td><strong style="color:#38BDF8;">${r.disp1}</strong></td>
            <td><strong style="color:#10B981;">${r.disp2}</strong></td>
            <td>${getAdvantageBadge(r.v1, r.v2, r.higher, p1Short, p2Short)}</td>
          </tr>
        `).join('');

      } else {
        // Duel: Striker vs Bowler
        const s1 = data.bat_stats || {};
        const s2 = data.bowl_stats || {};

        metricsBody.innerHTML = `
          <tr>
            <td><strong>Primary Career Volume</strong></td>
            <td><strong style="color:#38BDF8;">${(s1.total_runs || 0).toLocaleString()} Runs (${(s1.total_balls || 0)}b)</strong></td>
            <td><strong style="color:#10B981;">${s2.total_wickets || 0} Wickets (${(s2.total_overs || 0).toFixed(1)} ov)</strong></td>
            <td><span class="advantage-badge tie">Discipline Benchmark</span></td>
          </tr>
          <tr>
            <td><strong>Primary Efficiency</strong></td>
            <td><strong style="color:#38BDF8;">${(s1.overall_sr || 0).toFixed(1)} Strike Rate</strong></td>
            <td><strong style="color:#10B981;">${(s2.overall_econ || 0).toFixed(2)} Economy Rate</strong></td>
            <td><span class="advantage-badge tie">Discipline Benchmark</span></td>
          </tr>
          <tr>
            <td><strong>Secondary Metric</strong></td>
            <td><strong style="color:#38BDF8;">${(s1.overall_avg || 0).toFixed(1)} Batting Avg</strong></td>
            <td><strong style="color:#10B981;">${(s2.overall_sr || 0).toFixed(1)} Bowling SR</strong></td>
            <td><span class="advantage-badge tie">Discipline Benchmark</span></td>
          </tr>
          <tr>
            <td><strong>Dot Ball Frequency</strong></td>
            <td><strong style="color:#94A3B8;">${(s1.dot_pct || 0).toFixed(1)}% Dot Balls Faced</strong></td>
            <td><strong style="color:#94A3B8;">${(s2.dot_pct || 0).toFixed(1)}% Dot Balls Bowled</strong></td>
            <td><span class="advantage-badge tie">Control Indicator</span></td>
          </tr>
          <tr>
            <td><strong>Boundary Record</strong></td>
            <td><strong style="color:#F59E0B;">${s1.total_boundaries || 0} Boundaries Hit (${(s1.bnd_pct || 0).toFixed(1)}%)</strong></td>
            <td><strong style="color:#F43F5E;">${s2.total_boundaries || 0} Boundaries Conceded</strong></td>
            <td><span class="advantage-badge tie">Impact Indicator</span></td>
          </tr>
        `;
      }
    }

    // 5. Phase-by-Phase Breakdown Grid
    const phaseGridEl = document.getElementById('comparePhaseGrid');
    const phaseSubEl = document.getElementById('comparePhaseSub');
    if (phaseSubEl) {
      phaseSubEl.textContent = `${p1Name} vs ${p2Name} — Powerplay, Middle, and Death Overs execution`;
    }

    if (phaseGridEl) {
      const phases = [
        { key: 'Powerplay', title: 'Powerplay', range: 'Overs 1–6' },
        { key: 'Middle', title: 'Middle Overs', range: 'Overs 7–15' },
        { key: 'Death', title: 'Death Overs', range: 'Overs 16–20' }
      ];

      if (isBat) {
        const s1 = data.p1_stats || {};
        const s2 = data.p2_stats || {};

        phaseGridEl.innerHTML = phases.map(ph => {
          const p1Ph = (s1.phases && s1.phases[ph.key]) || { balls: 0, runs: 0, outs: 0, sr: 0, dot_pct: 0, fours: 0, sixes: 0 };
          const p2Ph = (s2.phases && s2.phases[ph.key]) || { balls: 0, runs: 0, outs: 0, sr: 0, dot_pct: 0, fours: 0, sixes: 0 };

          return `
            <div class="phase-card">
              <div class="phase-card-header">
                <span class="phase-card-title">${ph.title}</span>
                <span class="phase-card-tag">${ph.range}</span>
              </div>
              <div class="phase-compare-rows">
                <div class="phase-compare-row">
                  <span class="lbl">Strike Rate</span>
                  <div class="vals">
                    <span class="phase-val-pill p1">${fmt(p1Ph.sr, 1)}</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span class="phase-val-pill p2">${fmt(p2Ph.sr, 1)}</span>
                  </div>
                </div>
                <div class="phase-compare-row">
                  <span class="lbl">Runs (Balls)</span>
                  <div class="vals">
                    <span style="color:#F8FAFC; font-weight:600;">${p1Ph.runs || 0} <span style="font-size:0.72rem; color:var(--text-muted);">(${p1Ph.balls || 0}b)</span></span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span style="color:#F8FAFC; font-weight:600;">${p2Ph.runs || 0} <span style="font-size:0.72rem; color:var(--text-muted);">(${p2Ph.balls || 0}b)</span></span>
                  </div>
                </div>
                <div class="phase-compare-row">
                  <span class="lbl">Dismissals</span>
                  <div class="vals">
                    <span style="color:${(p1Ph.outs || 0) > 0 ? '#EF4444' : 'inherit'}; font-weight:600;">${p1Ph.outs || 0} outs</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span style="color:${(p2Ph.outs || 0) > 0 ? '#EF4444' : 'inherit'}; font-weight:600;">${p2Ph.outs || 0} outs</span>
                  </div>
                </div>
                <div class="phase-compare-row">
                  <span class="lbl">Dot Ball %</span>
                  <div class="vals">
                    <span style="color:#94A3B8;">${fmt(p1Ph.dot_pct, 1)}%</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span style="color:#94A3B8;">${fmt(p2Ph.dot_pct, 1)}%</span>
                  </div>
                </div>
                <div class="phase-compare-row">
                  <span class="lbl">Boundaries</span>
                  <div class="vals">
                    <span style="color:#F59E0B; font-size:0.78rem;">${p1Ph.fours || 0}x4, ${p1Ph.sixes || 0}x6</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span style="color:#F59E0B; font-size:0.78rem;">${p2Ph.fours || 0}x4, ${p2Ph.sixes || 0}x6</span>
                  </div>
                </div>
              </div>
            </div>
          `;
        }).join('');

      } else if (isBowl) {
        const s1 = data.b1_stats || {};
        const s2 = data.b2_stats || {};

        phaseGridEl.innerHTML = phases.map(ph => {
          const p1Ph = (s1.phases && s1.phases[ph.key]) || { balls: 0, overs: 0, runs: 0, wickets: 0, econ: 0, dot_pct: 0 };
          const p2Ph = (s2.phases && s2.phases[ph.key]) || { balls: 0, overs: 0, runs: 0, wickets: 0, econ: 0, dot_pct: 0 };

          return `
            <div class="phase-card">
              <div class="phase-card-header">
                <span class="phase-card-title">${ph.title}</span>
                <span class="phase-card-tag">${ph.range}</span>
              </div>
              <div class="phase-compare-rows">
                <div class="phase-compare-row">
                  <span class="lbl">Economy Rate</span>
                  <div class="vals">
                    <span class="phase-val-pill p1">${fmt(p1Ph.econ, 2)}</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span class="phase-val-pill p2">${fmt(p2Ph.econ, 2)}</span>
                  </div>
                </div>
                <div class="phase-compare-row">
                  <span class="lbl">Wickets</span>
                  <div class="vals">
                    <span style="color:#10B981; font-weight:700;">${p1Ph.wickets || 0} wkts</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span style="color:#10B981; font-weight:700;">${p2Ph.wickets || 0} wkts</span>
                  </div>
                </div>
                <div class="phase-compare-row">
                  <span class="lbl">Runs (Overs)</span>
                  <div class="vals">
                    <span style="color:#F8FAFC;">${p1Ph.runs || 0}r <span style="font-size:0.72rem; color:var(--text-muted);">(${p1Ph.overs || 0}ov)</span></span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span style="color:#F8FAFC;">${p2Ph.runs || 0}r <span style="font-size:0.72rem; color:var(--text-muted);">(${p2Ph.overs || 0}ov)</span></span>
                  </div>
                </div>
                <div class="phase-compare-row">
                  <span class="lbl">Dot Ball %</span>
                  <div class="vals">
                    <span style="color:#94A3B8;">${fmt(p1Ph.dot_pct, 1)}%</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span style="color:#94A3B8;">${fmt(p2Ph.dot_pct, 1)}%</span>
                  </div>
                </div>
              </div>
            </div>
          `;
        }).join('');

      } else {
        // Duel
        const s1 = data.bat_stats || {};
        const s2 = data.bowl_stats || {};

        phaseGridEl.innerHTML = phases.map(ph => {
          const p1Ph = (s1.phases && s1.phases[ph.key]) || { balls: 0, runs: 0, outs: 0, sr: 0, dot_pct: 0 };
          const p2Ph = (s2.phases && s2.phases[ph.key]) || { balls: 0, overs: 0, runs: 0, wickets: 0, econ: 0, dot_pct: 0 };

          return `
            <div class="phase-card">
              <div class="phase-card-header">
                <span class="phase-card-title">${ph.title}</span>
                <span class="phase-card-tag">${ph.range}</span>
              </div>
              <div class="phase-compare-rows">
                <div class="phase-compare-row">
                  <span class="lbl">Efficiency Metric</span>
                  <div class="vals">
                    <span class="phase-val-pill p1">SR: ${fmt(p1Ph.sr, 1)}</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span class="phase-val-pill p2">Econ: ${fmt(p2Ph.econ, 2)}</span>
                  </div>
                </div>
                <div class="phase-compare-row">
                  <span class="lbl">Volume</span>
                  <div class="vals">
                    <span style="color:#F8FAFC;">${p1Ph.runs || 0}r (${p1Ph.balls || 0}b)</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span style="color:#10B981; font-weight:700;">${p2Ph.wickets || 0}w (${p2Ph.overs || 0}ov)</span>
                  </div>
                </div>
                <div class="phase-compare-row">
                  <span class="lbl">Dot Ball %</span>
                  <div class="vals">
                    <span style="color:#94A3B8;">${fmt(p1Ph.dot_pct, 1)}%</span>
                    <span style="color:var(--text-muted); font-size:0.75rem;">vs</span>
                    <span style="color:#94A3B8;">${fmt(p2Ph.dot_pct, 1)}%</span>
                  </div>
                </div>
              </div>
            </div>
          `;
        }).join('');
      }
    }
  }

  // ==========================================================================
  // 9. API FETCH & RENDER: TAB 5 (18-LEAGUE CENSUS)
  // ==========================================================================
  async function loadCensus() {
    showLoading('Loading 18 worldwide leagues census database...');
    try {
      const res = await fetch('/api/census');
      const data = await res.json();
      renderCensus(data);
      state.censusLoaded = true;
    } catch (err) {
      console.error('Failed to load database census:', err);
    } finally {
      hideLoading();
    }
  }

  function renderCensus(data) {
    const grid = document.getElementById('censusGrid');
    const census = data.census || [];

    grid.innerHTML = census.map(lg => `
      <div class="league-card" data-code="${lg.code}">
        <div class="league-card-header">
          <span class="league-name">${lg.name}</span>
          <span class="league-country-tag">${lg.country} • ${lg.tier}</span>
        </div>
        <div class="league-stats-grid">
          <div class="l-stat-item">
            Matches
            <strong>${lg.matches.toLocaleString()}</strong>
          </div>
          <div class="l-stat-item">
            Deliveries
            <strong>${lg.deliveries.toLocaleString()}</strong>
          </div>
          <div class="l-stat-item">
            Batters
            <strong>${lg.batters.toLocaleString()}</strong>
          </div>
          <div class="l-stat-item">
            Bowlers
            <strong>${lg.bowlers.toLocaleString()}</strong>
          </div>
        </div>
        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:12px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.06); display:flex; justify-content:space-between;">
          <span>Code: <strong>${lg.code}</strong></span>
          <span>Span: <strong>${lg.span}</strong></span>
        </div>
      </div>
    `).join('');
  }

  // Initial Load
  updateCompareModeLabels();
  selectPlayer(state.currentPlayer);
});
