const API_BASE = window.location.origin;
const API_PREFIX = '/v1';

class DataCleanAPI {
  constructor() {
    this.baseURL = API_BASE + API_PREFIX;
    this.token = localStorage.getItem('dc_token');
    this.user = JSON.parse(localStorage.getItem('dc_user') || 'null');
  }

  isLoggedIn() {
    return !!this.token;
  }

  async register(email, password, name) {
    const resp = await fetch(this.baseURL + '/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name })
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || 'Registration failed');
    }
    const data = await resp.json();
    this._setAuth(data);
    return data;
  }

  async login(email, password) {
    const resp = await fetch(this.baseURL + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await resp.json();
    this._setAuth(data);
    return data;
  }

  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem('dc_token');
    localStorage.removeItem('dc_user');
  }

  async getMe() {
    if (!this.token) return null;
    const resp = await fetch(this.baseURL + `/auth/me?token=${this.token}`);
    if (!resp.ok) {
      this.logout();
      return null;
    }
    const data = await resp.json();
    this.user = data;
    localStorage.setItem('dc_user', JSON.stringify(data));
    return data;
  }

  async getKeys() {
    const resp = await fetch(this.baseURL + `/keys?token=${this.token}`);
    if (!resp.ok) throw new Error('Failed to fetch keys');
    return resp.json();
  }

  async createKey(name) {
    const resp = await fetch(this.baseURL + `/keys?token=${this.token}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || 'Failed to create key');
    }
    return resp.json();
  }

  async revokeKey(keyId) {
    const resp = await fetch(this.baseURL + `/keys/${keyId}?token=${this.token}`, {
      method: 'DELETE'
    });
    if (!resp.ok) throw new Error('Failed to revoke key');
    return resp.json();
  }

  async dedup(records, matchFields, mode) {
    const resp = await fetch(this.baseURL + '/dedup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this._getApiKey()
      },
      body: JSON.stringify({
        records,
        match_fields: matchFields,
        match_mode: mode
      })
    });
    return this._handleApiResponse(resp);
  }

  async standardize(records, fields) {
    const resp = await fetch(this.baseURL + '/standardize', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this._getApiKey()
      },
      body: JSON.stringify({ records, fields })
    });
    return this._handleApiResponse(resp);
  }

  async clean(records, options) {
    const resp = await fetch(this.baseURL + '/clean', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this._getApiKey()
      },
      body: JSON.stringify({ records, ...options })
    });
    return this._handleApiResponse(resp);
  }

  async _handleApiResponse(resp) {
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ detail: resp.statusText }));
      throw new Error(err.detail || `API error (${resp.status})`);
    }
    return resp.json();
  }

  _setAuth(data) {
    this.token = data.token;
    this.user = { email: data.email, plan: data.plan, credits: data.credits };
    localStorage.setItem('dc_token', this.token);
    localStorage.setItem('dc_user', JSON.stringify(this.user));
  }

  _getApiKey() {
    return localStorage.getItem('dc_active_key') || '';
  }

  setActiveKey(key) {
    localStorage.setItem('dc_active_key', key);
  }
}

const api = new DataCleanAPI();

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function maskKey(prefix) {
  if (!prefix) return '****';
  return prefix + '••••••••••••';
}
