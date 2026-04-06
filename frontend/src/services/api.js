import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: false,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refresh = localStorage.getItem('refresh');
      if (refresh) {
        try {
          const response = await axios.post(`${API_URL}/token/refresh/`, { refresh });
          localStorage.setItem('token', response.data.access);
          originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('token');
          localStorage.removeItem('refresh');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export const materiaisService = {
  getAll: (params) => api.get('/materiais/', { params }),
  getById: (id) => api.get(`/materiais/${id}/`),
  create: (data) => api.post('/materiais/', data),
  update: (id, data) => api.patch(`/materiais/${id}/`, data),
  delete: (id) => api.delete(`/materiais/${id}/`),
  estatisticas: (params) => api.get('/materiais/estatisticas/', { params }),
  conferir: (id, data) => api.post(`/materiais/${id}/conferir_fisicamente/`, data),
  autorizar: (id) => api.post(`/materiais/${id}/autorizar_incineracao/`),
  gerarOficio: (ids) => api.post('/materiais/gerar_oficio/', { materiais_ids: ids }),
  confirmarEntrega: (id, formData) => api.post(`/materiais/${id}/confirmar_entrega_forum/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
};

export const lotesService = {
  getAll: (params) => api.get('/lotes/', { params }),
  getById: (id) => api.get(`/lotes/${id}/`),
  create: (data) => api.post('/lotes/', data),
  gerarAutomaticos: () => api.post('/lotes/gerar_lotes_automaticos/'),
  adicionarMaterial: (loteId, materialId) => api.post(`/lotes/${loteId}/adicionar_material_avulso/`, { material_id: materialId }),
  imprimirCapa: (loteId) => api.get(`/lotes/${loteId}/imprimir_capa/`),
  imprimirCapasMassa: (loteIds) => api.get('/lotes/imprimir_capas_em_massa/', { params: { lote_ids: loteIds } }, { responseType: 'blob' }),
  imprimirCertidaoVara: () => api.get('/lotes/imprimir_certidao_por_vara/'),
  finalizar: (loteId, formData) => api.post(`/lotes/${loteId}/finalizar_lote/`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  finalizarMassa: (loteIds, protocolo, termoAssinado) => {
    const formData = new FormData();
    loteIds.forEach(id => formData.append('lote_ids', id));
    formData.append('protocolo', protocolo);
    formData.append('termo_assinado', termoAssinado);
    return api.post('/lotes/finalizar_massa/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  removerMaterial: (loteId, materialId) => api.post(`/lotes/${loteId}/remover_material/`, { material_id: materialId }),
};

export const ocorrenciasService = {
  getAll: (params) => api.get('/ocorrencias/', { params }),
  getById: (id) => api.get(`/ocorrencias/${id}/`),
  create: (data) => api.post('/ocorrencias/', data),
  update: (id, data) => api.patch(`/ocorrencias/${id}/`, data),
  buscarPorBou: (bou) => api.get('/ocorrencias/buscar_por_bou/', { params: { bou } }),
  imprimirRecibo: (id) => api.get(`/ocorrencias/${id}/imprimir_recibo/`),
};

export default api;
