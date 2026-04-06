import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const authService = {
  async login(username, password) {
    const response = await axios.post(`${API_URL}/token/`, { username, password });
    if (response.data.access) {
      localStorage.setItem('token', response.data.access);
      localStorage.setItem('refresh', response.data.refresh);
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
    }
    return response.data;
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh');
    localStorage.removeItem('user');
    delete axios.defaults.headers.common['Authorization'];
  },

  getToken() {
    return localStorage.getItem('token');
  },

  getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  },

  setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  async refreshToken() {
    const refresh = localStorage.getItem('refresh');
    if (!refresh) return null;
    try {
      const response = await axios.post(`${API_URL}/token/refresh/`, { refresh });
      if (response.data.access) {
        localStorage.setItem('token', response.data.access);
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`;
      }
      return response.data.access;
    } catch (error) {
      this.logout();
      return null;
    }
  },

  init() {
    const token = this.getToken();
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }
  }
};

authService.init();

export default authService;
