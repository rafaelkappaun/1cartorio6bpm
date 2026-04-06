import { useState, useEffect } from 'react';
import { FileText, Truck, CheckCircle, Upload, Search, Package, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

export default function MateriaisGerais() {
  const [materiais, setMateriais] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState('');
  const [selected, setSelected] = useState([]);
  const [tab, setTab] = useState('pendentes'); // pendentes, encaminhados, entregues
  const [uploading, setUploading] = useState(null);

  const loadMateriais = async () => {
    setLoading(true);
    try {
      const res = await api.get('/materiais/');
      const data = res.data.results || res.data;
      // Filtrar apenas materiais gerais (não entorpecentes e não dinheiro)
      const gerais = data.filter(m => m.categoria !== 'ENTORPECENTE' && m.categoria !== 'DINHEIRO');
      setMateriais(gerais);
    } catch (e) {
      console.error("Erro ao carregar materiais:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMateriais();
  }, []);

  const handleSelect = (id) => {
    setSelected(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  const gerarOficio = async () => {
    if (selected.length === 0) return alert("Selecione ao menos um item.");
    try {
      const res = await api.post('/materiais/gerar_oficio/', { materiais_ids: selected });
      window.open(res.data.file_url, '_blank');
      alert("Ofício gerado com sucesso! O status dos itens foi atualizado.");
      setSelected([]);
      loadMateriais();
    } catch (e) {
      alert("Erro ao gerar ofício: " + (e.response?.data?.error || e.message));
    }
  };

  const handleFileUpload = async (id, file) => {
    const formData = new FormData();
    formData.append('recibo', file);
    setUploading(id);
    try {
      await api.post(`/materiais/${id}/confirmar_entrega_forum/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      alert("Comprovante enviado e entrega confirmada!");
      loadMateriais();
    } catch (e) {
      alert("Erro no upload: " + (e.response?.data?.error || e.message));
    } finally {
      setUploading(null);
    }
  };

  const statusFilter = {
    pendentes: ['AGUARDANDO_OFICIO'],
    encaminhados: ['OFICIO_GERADO', 'EM_TRANSPORTE_FORUM'],
    entregues: ['ENTREGUE_AO_JUDICIARIO']
  };

  const filtrados = materiais.filter(m => 
    statusFilter[tab].includes(m.status) &&
    (!busca || m.bou?.includes(busca) || m.descricao_geral?.toLowerCase().includes(busca.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Encaminhamento ao Fórum</h1>
          <p className="text-gray-500">Gestão de Materiais Gerais (Armas, Som, Objetos)</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input 
              type="text" 
              placeholder="Buscar por BOU ou descrição..." 
              className="pl-10 pr-4 py-2 border rounded-lg w-64 focus:ring-2 focus:ring-pmpr-green outline-none"
              value={busca}
              onChange={(e) => setBusca(e.target.value)}
            />
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="flex border-b border-gray-200">
        <button 
          onClick={() => setTab('pendentes')}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${tab === 'pendentes' ? 'border-pmpr-green text-pmpr-green' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <Package size={18} className="inline mr-2" />
          Aguardando Ofício ({materiais.filter(m => statusFilter.pendentes.includes(m.status)).length})
        </button>
        <button 
          onClick={() => setTab('encaminhados')}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${tab === 'encaminhados' ? 'border-pmpr-green text-pmpr-green' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <Truck size={18} className="inline mr-2" />
          Em Remessa ({materiais.filter(m => statusFilter.encaminhados.includes(m.status)).length})
        </button>
        <button 
          onClick={() => setTab('entregues')}
          className={`px-6 py-3 font-medium transition-colors border-b-2 ${tab === 'entregues' ? 'border-pmpr-green text-pmpr-green' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
        >
          <CheckCircle size={18} className="inline mr-2" />
          Entregues / Baixados ({materiais.filter(m => statusFilter.entregues.includes(m.status)).length})
        </button>
      </div>

      {/* Ações em Massa */}
      <AnimatePresence>
        {selected.length > 0 && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed bottom-8 left-1/2 -translate-x-1/2 bg-pmpr-green text-white px-6 py-4 rounded-2xl shadow-2xl flex items-center gap-6 z-50 border border-pmpr-gold/30"
          >
            <span className="font-semibold">{selected.length} itens selecionados</span>
            <div className="h-6 w-px bg-white/20" />
            <button 
              onClick={gerarOficio}
              className="flex items-center gap-2 bg-pmpr-gold text-pmpr-dark px-4 py-2 rounded-lg font-bold hover:bg-yellow-500 transition-colors"
            >
              <FileText size={18} />
              Gerar Ofício de Remessa
            </button>
            <button onClick={() => setSelected([])} className="text-white/70 hover:text-white text-sm underline">Cancelar</button>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              {tab === 'pendentes' && <th className="px-6 py-4 w-12"></th>}
              <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">BOU / Natureza</th>
              <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Descrição do Material</th>
              <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider">Status Atual</th>
              <th className="px-6 py-4 text-xs font-bold text-gray-500 uppercase tracking-wider text-right">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              <tr><td colSpan="5" className="px-6 py-12 text-center text-gray-400">Carregando materiais...</td></tr>
            ) : filtrados.length === 0 ? (
              <tr>
                <td colSpan="5" className="px-6 py-16 text-center">
                  <div className="flex flex-col items-center">
                    <Package size={48} className="text-gray-200 mb-4" />
                    <p className="text-gray-400 font-medium">Nenhum material encontrado nesta etapa.</p>
                  </div>
                </td>
              </tr>
            ) : (
              filtrados.map((m) => (
                <tr key={m.id} className={`hover:bg-gray-50/50 transition-colors ${selected.includes(m.id) ? 'bg-emerald-50/50' : ''}`}>
                  {tab === 'pendentes' && (
                    <td className="px-6 py-4">
                      <input 
                        type="checkbox" 
                        checked={selected.includes(m.id)}
                        onChange={() => handleSelect(m.id)}
                        className="w-4 h-4 rounded border-gray-300 text-pmpr-green focus:ring-pmpr-green"
                      />
                    </td>
                  )}
                  <td className="px-6 py-4">
                    <div className="font-bold text-gray-900">{m.bou || 'N/I'}</div>
                    <div className="text-xs text-gray-500 uppercase">{m.categoria}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-700">{m.descricao_geral || 'Sem descrição'}</div>
                    <div className="text-xs text-gray-400 mt-0.5">Lacre: {m.numero_lacre || 'Não informado'}</div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                      m.status === 'ENTREGUE_AO_JUDICIARIO' ? 'bg-emerald-100 text-emerald-800' :
                      m.status === 'OFICIO_GERADO' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {m.status.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    {m.status === 'OFICIO_GERADO' && (
                      <div className="flex items-center justify-end gap-2">
                        <label className="cursor-pointer bg-white border border-gray-200 text-gray-600 hover:border-pmpr-green hover:text-pmpr-green px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5">
                          <Upload size={14} />
                          {uploading === m.id ? 'Enviando...' : 'Anexar Recibo'}
                          <input 
                            type="file" 
                            className="hidden" 
                            accept=".pdf,image/*" 
                            onChange={(e) => handleFileUpload(m.id, e.target.files[0])}
                            disabled={uploading === m.id}
                          />
                        </label>
                      </div>
                    )}
                    {m.status === 'ENTREGUE_AO_JUDICIARIO' && (
                      <div className="flex items-center justify-end text-emerald-600 gap-1 font-bold text-xs">
                        <CheckCircle size={14} />
                        Baixado
                      </div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {tab === 'pendentes' && filtrados.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-4 items-start">
          <AlertTriangle className="text-amber-500 shrink-0" size={20} />
          <div className="text-sm text-amber-800">
            <p className="font-bold">Dica do Sistema</p>
            <p>Selecione vários itens de um mesmo processo ou BOU para agrupá-los em um único ofício de remessa ao judiciário. Isso economiza papel e facilita o protocolo no fórum.</p>
          </div>
        </div>
      )}
    </div>
  );
}
