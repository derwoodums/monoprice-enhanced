/**
 * Monoprice Zone Card
 * A compact, light-themed card for controlling Monoprice multi-zone amplifier zones
 */

class MonopriceZoneCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._dragging = null; // Track which slider is being dragged
  }

  set hass(hass) {
    this._hass = hass;
    // Only do full render if not dragging and select isn't focused
    const activeEl = this.shadowRoot?.activeElement;
    const selectFocused = activeEl?.tagName === 'SELECT';
    if (!this._dragging && !selectFocused) {
      this.render();
    }
  }

  setConfig(config) {
    if (!config.media_player) {
      throw new Error('You need to define a media_player entity');
    }
    this._config = {
      name: config.name || null,
      media_player: config.media_player,
      treble: config.treble || null,
      bass: config.bass || null,
      balance: config.balance || null,
      show_tone_controls: config.show_tone_controls !== false,
    };
  }

  getCardSize() {
    return 2;
  }

  render() {
    if (!this._hass || !this._config) return;

    const mp = this._hass.states[this._config.media_player];
    if (!mp) {
      this.shadowRoot.innerHTML = `<ha-card>Entity not found: ${this._config.media_player}</ha-card>`;
      return;
    }

    const treble = this._config.treble ? this._hass.states[this._config.treble] : null;
    const bass = this._config.bass ? this._hass.states[this._config.bass] : null;
    const balance = this._config.balance ? this._hass.states[this._config.balance] : null;

    const isOn = mp.state === 'on';
    const volume = mp.attributes.volume_level || 0;
    const isMuted = mp.attributes.is_volume_muted || false;
    const source = mp.attributes.source || '';
    const sources = mp.attributes.source_list || [];
    const name = this._config.name || mp.attributes.friendly_name || 'Zone';

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          --accent: #4a9ced;
          --accent-light: #e8f4fc;
          --text-primary: #1a1a1a;
          --text-secondary: #666;
          --border: #e0e0e0;
          --bg-control: #f5f5f5;
          --slider-bg: #e0e0e0;
          --slider-height: 6px;
          --thumb-size: 18px;
          --off-opacity: 0.45;
        }

        ha-card {
          background: #fff;
          border-radius: 12px;
          padding: 12px 14px;
          font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif;
          user-select: none;
        }

        .header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 10px;
        }

        .zone-name {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary);
          opacity: ${isOn ? 1 : 'var(--off-opacity)'};
        }

        .power-btn {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          border: none;
          background: ${isOn ? 'var(--accent)' : 'var(--bg-control)'};
          color: ${isOn ? '#fff' : 'var(--text-secondary)'};
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.15s;
        }

        .power-btn:hover {
          transform: scale(1.08);
        }

        .power-btn svg {
          width: 14px;
          height: 14px;
        }

        .controls {
          opacity: ${isOn ? 1 : 'var(--off-opacity)'};
          pointer-events: ${isOn ? 'auto' : 'none'};
          transition: opacity 0.15s;
        }

        .row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
        }

        .row:last-child {
          margin-bottom: 0;
        }

        .label {
          font-size: 11px;
          font-weight: 500;
          color: var(--text-secondary);
          text-transform: uppercase;
          letter-spacing: 0.3px;
          width: 52px;
          flex-shrink: 0;
        }

        .mute-btn {
          width: 26px;
          height: 26px;
          border-radius: 6px;
          border: none;
          background: ${isMuted ? '#fee2e2' : 'var(--bg-control)'};
          color: ${isMuted ? '#dc2626' : 'var(--text-secondary)'};
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          transition: all 0.1s;
        }

        .mute-btn:hover {
          background: ${isMuted ? '#fecaca' : '#e8e8e8'};
          color: ${isMuted ? '#b91c1c' : 'var(--text-primary)'};
        }

        .mute-btn svg {
          width: 14px;
          height: 14px;
        }

        .slider-container {
          flex: 1;
          height: 26px;
          display: flex;
          align-items: center;
          position: relative;
          touch-action: none;
        }

        .slider-track {
          position: absolute;
          left: 0;
          right: 0;
          height: var(--slider-height);
          background: var(--slider-bg);
          border-radius: calc(var(--slider-height) / 2);
        }

        .slider-fill {
          position: absolute;
          left: 0;
          height: var(--slider-height);
          background: var(--accent);
          border-radius: calc(var(--slider-height) / 2);
          pointer-events: none;
        }

        .slider-thumb {
          position: absolute;
          width: var(--thumb-size);
          height: var(--thumb-size);
          background: var(--accent);
          border-radius: 50%;
          box-shadow: 0 1px 3px rgba(0,0,0,0.3);
          transform: translateX(-50%);
          cursor: grab;
          transition: transform 0.1s;
        }

        .slider-thumb:hover {
          transform: translateX(-50%) scale(1.1);
        }

        .slider-thumb.dragging {
          cursor: grabbing;
          transform: translateX(-50%) scale(1.15);
        }

        .balance-tick {
          position: absolute;
          left: 50%;
          top: 50%;
          width: 2px;
          height: 14px;
          background: rgba(0, 0, 0, 0.3);
          transform: translate(-50%, -50%);
          border-radius: 1px;
          pointer-events: none;
        }

        .value {
          font-size: 11px;
          font-weight: 600;
          color: var(--text-secondary);
          min-width: 28px;
          text-align: right;
        }

        .source-select {
          flex: 1;
          height: 26px;
          background: var(--bg-control);
          border: 1px solid var(--border);
          border-radius: 6px;
          color: var(--text-primary);
          font-size: 12px;
          padding: 0 24px 0 8px;
          cursor: pointer;
          -webkit-appearance: none;
          -moz-appearance: none;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right 8px center;
        }

        .source-select:focus {
          outline: none;
          border-color: var(--accent);
        }

        .source-select option {
          background: #fff;
          color: var(--text-primary);
          padding: 8px;
        }

        .tone-section {
          border-top: 1px solid var(--border);
          padding-top: 10px;
          margin-top: 10px;
        }
      </style>

      <ha-card>
        <div class="header">
          <div class="zone-name">${name}</div>
          <button class="power-btn" id="power">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
              <path d="M12 2v10M18.4 6.6a9 9 0 1 1-12.8 0"/>
            </svg>
          </button>
        </div>

        <div class="controls">
          <div class="row">
            <span class="label">Volume</span>
            <button class="mute-btn" id="mute">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                ${isMuted 
                  ? '<path d="M11 5L6 9H2v6h4l5 4V5z"/><line x1="23" y1="9" x2="17" y2="15"/><line x1="17" y1="9" x2="23" y2="15"/>'
                  : '<path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>'
                }
              </svg>
            </button>
            <div class="slider-container" data-slider="volume" data-min="0" data-max="100" data-value="${Math.round(volume * 100)}">
              <div class="slider-track"></div>
              <div class="slider-fill" style="width: ${volume * 100}%"></div>
              <div class="slider-thumb" style="left: ${volume * 100}%"></div>
            </div>
            <span class="value" data-value-for="volume">${Math.round(volume * 100)}%</span>
          </div>

          <div class="row">
            <span class="label">Source</span>
            <select class="source-select" id="source">
              ${sources.map(s => `<option value="${s}" ${s === source ? 'selected' : ''}>${s}</option>`).join('')}
            </select>
          </div>

          ${this._config.show_tone_controls && (treble || bass || balance) ? `
            <div class="tone-section">
              ${treble ? this._renderSlider('Treble', 'treble', treble) : ''}
              ${bass ? this._renderSlider('Bass', 'bass', bass) : ''}
              ${balance ? this._renderBalanceSlider(balance) : ''}
            </div>
          ` : ''}
        </div>
      </ha-card>
    `;

    this._attachEventListeners();
  }

  _renderSlider(label, id, entity) {
    const value = parseFloat(entity.state) || 0;
    const min = entity.attributes.min || 0;
    const max = entity.attributes.max || 14;
    const percent = ((value - min) / (max - min)) * 100;
    
    return `
      <div class="row">
        <span class="label">${label}</span>
        <div class="slider-container" data-slider="${id}" data-min="${min}" data-max="${max}" data-value="${value}">
          <div class="slider-track"></div>
          <div class="slider-fill" style="width: ${percent}%"></div>
          <div class="slider-thumb" style="left: ${percent}%"></div>
        </div>
        <span class="value" data-value-for="${id}">${Math.round(value)}</span>
      </div>
    `;
  }

  _renderBalanceSlider(entity) {
    const value = parseFloat(entity.state) || 10;
    const min = entity.attributes.min || 0;
    const max = entity.attributes.max || 20;
    const center = (max - min) / 2 + min;
    const percent = ((value - min) / (max - min)) * 100;
    
    const displayValue = Math.round(value - center);
    const displayText = displayValue === 0 ? 'C' : (displayValue > 0 ? `R${displayValue}` : `L${Math.abs(displayValue)}`);
    
    return `
      <div class="row">
        <span class="label">Balance</span>
        <div class="slider-container" data-slider="balance" data-min="${min}" data-max="${max}" data-value="${value}" data-center="${center}">
          <div class="slider-track"></div>
          <div class="balance-tick"></div>
          <div class="slider-fill" style="width: ${percent}%"></div>
          <div class="slider-thumb" style="left: ${percent}%"></div>
        </div>
        <span class="value" data-value-for="balance">${displayText}</span>
      </div>
    `;
  }

  _attachEventListeners() {
    // Power button
    this.shadowRoot.getElementById('power')?.addEventListener('click', () => {
      const mp = this._hass.states[this._config.media_player];
      this._hass.callService('media_player', mp.state === 'on' ? 'turn_off' : 'turn_on', {
        entity_id: this._config.media_player
      });
    });

    // Mute button
    this.shadowRoot.getElementById('mute')?.addEventListener('click', () => {
      const mp = this._hass.states[this._config.media_player];
      this._hass.callService('media_player', 'volume_mute', {
        entity_id: this._config.media_player,
        is_volume_muted: !mp.attributes.is_volume_muted
      });
    });

    // Source select
    this.shadowRoot.getElementById('source')?.addEventListener('change', (e) => {
      this._hass.callService('media_player', 'select_source', {
        entity_id: this._config.media_player,
        source: e.target.value
      });
    });

    // Attach slider events
    this.shadowRoot.querySelectorAll('.slider-container').forEach(container => {
      const thumb = container.querySelector('.slider-thumb');
      const sliderId = container.dataset.slider;
      
      const startDrag = (e) => {
        e.preventDefault();
        this._dragging = sliderId;
        thumb.classList.add('dragging');
        
        const onMove = (moveEvent) => {
          const clientX = moveEvent.touches ? moveEvent.touches[0].clientX : moveEvent.clientX;
          this._updateSliderPosition(container, clientX);
        };
        
        const onEnd = () => {
          thumb.classList.remove('dragging');
          this._dragging = null;
          this._commitSliderValue(container);
          document.removeEventListener('mousemove', onMove);
          document.removeEventListener('mouseup', onEnd);
          document.removeEventListener('touchmove', onMove);
          document.removeEventListener('touchend', onEnd);
        };
        
        document.addEventListener('mousemove', onMove);
        document.addEventListener('mouseup', onEnd);
        document.addEventListener('touchmove', onMove, { passive: false });
        document.addEventListener('touchend', onEnd);
      };
      
      // Click on track to jump
      container.addEventListener('click', (e) => {
        if (e.target === thumb) return;
        this._updateSliderPosition(container, e.clientX);
        this._commitSliderValue(container);
      });
      
      thumb.addEventListener('mousedown', startDrag);
      thumb.addEventListener('touchstart', startDrag, { passive: false });
    });
  }

  _updateSliderPosition(container, clientX) {
    const rect = container.getBoundingClientRect();
    const percent = Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100));
    
    const thumb = container.querySelector('.slider-thumb');
    const fill = container.querySelector('.slider-fill');
    const sliderId = container.dataset.slider;
    const min = parseFloat(container.dataset.min);
    const max = parseFloat(container.dataset.max);
    const value = min + (percent / 100) * (max - min);
    
    thumb.style.left = `${percent}%`;
    fill.style.width = `${percent}%`;
    container.dataset.value = value;
    
    // Update display value
    const valueDisplay = this.shadowRoot.querySelector(`[data-value-for="${sliderId}"]`);
    if (valueDisplay) {
      if (sliderId === 'volume') {
        valueDisplay.textContent = `${Math.round(value)}%`;
      } else if (sliderId === 'balance') {
        const center = parseFloat(container.dataset.center);
        const displayValue = Math.round(value - center);
        valueDisplay.textContent = displayValue === 0 ? 'C' : (displayValue > 0 ? `R${displayValue}` : `L${Math.abs(displayValue)}`);
      } else {
        valueDisplay.textContent = Math.round(value);
      }
    }
  }

  _commitSliderValue(container) {
    const sliderId = container.dataset.slider;
    const value = parseFloat(container.dataset.value);
    
    if (sliderId === 'volume') {
      this._hass.callService('media_player', 'volume_set', {
        entity_id: this._config.media_player,
        volume_level: value / 100
      });
    } else {
      const entityId = this._config[sliderId];
      if (entityId) {
        this._hass.callService('number', 'set_value', {
          entity_id: entityId,
          value: Math.round(value)
        });
      }
    }
  }

  static getStubConfig() {
    return {
      media_player: 'media_player.monoprice_zone_1',
      treble: 'number.monoprice_zone_1_treble',
      bass: 'number.monoprice_zone_1_bass',
      balance: 'number.monoprice_zone_1_balance'
    };
  }

  static getConfigElement() {
    return document.createElement('monoprice-zone-card-editor');
  }
}

// Visual Editor using HA's native ha-form
class MonopriceZoneCardEditor extends HTMLElement {
  constructor() {
    super();
    this._config = {};
    this._hass = null;
  }

  set hass(hass) {
    this._hass = hass;
    if (this._form) {
      this._form.hass = hass;
    }
  }

  setConfig(config) {
    this._config = { ...config };
    // Only render if we haven't yet, or update form data if we have
    if (this._form) {
      this._updateFormData();
    }
  }

  connectedCallback() {
    if (!this._form) {
      this._buildForm();
    }
  }

  _buildForm() {
    this._form = document.createElement('ha-form');
    this._form.schema = [
      {
        name: 'name',
        selector: { text: {} }
      },
      {
        name: 'media_player',
        required: true,
        selector: { entity: { domain: 'media_player' } }
      },
      {
        name: 'treble',
        selector: { entity: { filter: { domain: 'number' } } }
      },
      {
        name: 'bass',
        selector: { entity: { filter: { domain: 'number' } } }
      },
      {
        name: 'balance',
        selector: { entity: { filter: { domain: 'number' } } }
      },
      {
        name: 'show_tone_controls',
        selector: { boolean: {} }
      }
    ];

    this._form.computeLabel = (schema) => {
      const labels = {
        name: 'Name (optional)',
        media_player: 'Media Player',
        treble: 'Treble Entity',
        bass: 'Bass Entity',
        balance: 'Balance Entity',
        show_tone_controls: 'Show tone controls'
      };
      return labels[schema.name] || schema.name;
    };

    this._form.addEventListener('value-changed', (ev) => {
      if (!this._config || !this._hass) return;
      
      const newConfig = ev.detail.value;
      
      // Fire config changed event
      this.dispatchEvent(new CustomEvent('config-changed', {
        detail: { config: newConfig },
        bubbles: true,
        composed: true
      }));
    });

    this.appendChild(this._form);
    this._updateFormData();
  }

  _updateFormData() {
    if (!this._form) return;
    
    const data = { 
      show_tone_controls: true,
      ...this._config 
    };
    this._form.data = data;
    
    if (this._hass) {
      this._form.hass = this._hass;
    }
  }
}

customElements.define('monoprice-zone-card', MonopriceZoneCard);
customElements.define('monoprice-zone-card-editor', MonopriceZoneCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'monoprice-zone-card',
  name: 'Monoprice Zone Card',
  description: 'A compact card for controlling Monoprice multi-zone amplifier zones with tone controls',
  documentationURL: 'https://github.com/derwoodums/monoprice-zone-card'
});

console.info('%c MONOPRICE-ZONE-CARD %c 2.4.0 ', 'color: white; background: #4a9ced; font-weight: bold;', 'color: #4a9ced; background: white; font-weight: bold;');
