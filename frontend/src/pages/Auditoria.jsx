import { useState, useEffect, useCallback } from 'react';
import { History, Search, RefreshCw, ChevronRight, User, Calendar, Shield, MapPin, Hash } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../services/api';

const STATUS_COLORS = {
  'RECEBIDO': 'bg-yellow-100 text-yellow-700 border-yellow-200',
  'ARMAZENADO': 'bg-emerald-100 text-emerald-700 border-emerald-200',
  'AUTORIZADO': 'bg-blue-100 text-blue-700 border-blue-200',
  'INCINERADO': 'bg-gray-200 text-gray-700 border-gray-300',
  'RETIRADO_PERICIA': 'bg-orange-100 text-orange-700 border-orange-200',
  'ENTREGUE_AO_JUDICIARIO': 'bg-green-100 text-green-700 border-green-200',
};

export default function Auditoria() {
  const [materiais, setMateriais] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busca, setBusca] = useState('');
  const [selectedMaterial, setSelectedMaterial] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/materiais/`);
      setMateriais(res.data.results || res.data);
    } catch (e) {
      console.error('Erro ao carregar auditoria:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const filtrados = materiais.filter(m => 
    !busca || 
    m.bou?.toLowerCase().includes(busca.toLowerCase()) ||
    m.numero_lacre?.toLowerCase().includes(busca.toLowerCase()) ||
    m.criado_por_nome?.toLowerCase().includes(busca.toLowerCase())
  );

  return (
    <div className="space-y-6 pb-20">
      <header className="flex justify-between items-end flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2.5 rounded-xl bg-pmpr-green shadow-md">
              <History size={24} className="text-white" />
            </div>
            <h1 className="text-3xl font-black text-gray-900 tracking-tight">Rastreabilidade & Log</h1>
          </div>
          <p className="text-gray-400 text-sm">Histórico completo da cadeia de custódia e auditoria por usuário.</p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:min-w-[300px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
            <input 
              type="text" 
              value={busca} 
              onChange={(e) => setBusca(e.target.value)} 
              placeholder="Buscar por BOU, Lacre ou Usuário..." 
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl text-sm focus:ring-2 focus:ring-emerald-500/30 transition-all shadow-sm"
            />
          </div>
          <button onClick={loadData} className="p-2.5 bg-white border border-gray-200 rounded-xl text-gray-500 hover:bg-gray-50 transition shadow-sm">
            <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
        {/* LISTA DE REGISTROS */}
        <div className="xl:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-wider text-gray-400">Status / BOU</th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-wider text-gray-400">Material</th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-wider text-gray-400">Nº Lacre</th>
                <th className="px-6 py-4 text-[11px] font-bold uppercase tracking-wider text-gray-400">Responsável</th>
                <th className="px-6 py-4"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr><td colSpan="5" className="px-6 py-20 text-center text-gray-400">Carregando rastro de auditoria...</td></tr>
              ) : filtrados.length === 0 ? (
                <tr><td colSpan="5" className="px-6 py-20 text-center text-gray-400 font-medium">Nenhum rastro encontrado.</td></tr>
              ) : (
                filtrados.map((mat) => (
                  <tr 
                    key={mat.id} 
                    onClick={() => setSelectedMaterial(mat)}
                    className={`hover:bg-emerald-50/40 cursor-pointer transition-colors group ${selectedMaterial?.id === mat.id ? 'bg-emerald-50/60' : ''}`}
                  >
                    <td className="px-6 py-4">
                      <div className="flex flex-col gap-1.5">
                        <span className={`w-fit px-2 py-0.5 rounded-full text-[10px] font-black border ${STATUS_COLORS[mat.status] || 'bg-gray-100 text-gray-500'}`}>
                          {mat.status?.replace(/_/g, ' ')}
                        </span>
                        <span className="font-bold text-gray-900 tracking-tight">{mat.bou || '-'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex flex-col">
                        <span className="font-semibold text-gray-700">{mat.categoria}</span>
                        <span className="text-[11px] text-gray-400 truncate max-w-[150px]">{mat.descricao_amigavel}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-gray-500">
                      {mat.numero_lacre || 'SEM LACRE'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-pmpr-green/10 text-pmpr-green flex items-center justify-center text-[10px] font-black">
                          {mat.criado_por_nome?.substring(0, 2).toUpperCase() || 'S'}
                        </div>
                        <span className="text-gray-600 font-medium">{mat.criado_por_nome || 'Sistema'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <ChevronRight size={18} className="text-gray-300 group-hover:text-pmpr-green transition-transform group-hover:translate-x-1" />
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* DETALHE DO HISTÓRICO (Linha do Tempo) */}
        <div className="xl:col-span-1">
          <AnimatePresence mode="wait">
            {!selectedMaterial ? (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-gray-50 border-2 border-dashed border-gray-200 rounded-2xl p-12 text-center"
              >
                <div className="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto mb-4 text-gray-300">
                  <Shield size={32} />
                </div>
                <h3 className="text-gray-500 font-bold">Auditoria Detalhada</h3>
                <p className="text-gray-400 text-xs mt-2">Selecione um registro na tabela para visualizar a linha do tempo completa da custódia.</p>
              </motion.div>
            ) : (
              <motion.div 
                key={selectedMaterial.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="bg-white rounded-2xl border border-gray-100 shadow-xl overflow-hidden sticky top-6"
              >
                <div className="p-6 bg-pmpr-green text-white">
                  <div className="flex justify-between items-start mb-4">
                     <span className="text-[10px] font-black uppercase tracking-widest bg-white/20 px-2 py-1 rounded-md">Log de Auditoria</span>
                     <button onClick={() => setSelectedMaterial(null)} className="hover:bg-white/10 rounded-lg p-1 transition"><XIcon size={20} /></button>
                  </div>
                  <h2 className="text-2xl font-black">{selectedMaterial.bou}</h2>
                  <p className="text-emerald-200 text-sm font-medium mt-1">{selectedMaterial.descricao_amigavel}</p>
                </div>

                <div className="p-6 space-y-8">
                   {/* Info do Objeto */}
                   <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Processo</p>
                        <p className="text-sm font-bold text-gray-800">{selectedMaterial.processo || 'NÃO ATRELADO'}</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Lacre Atual</p>
                        <p className="text-sm font-bold text-gray-800 font-mono">{selectedMaterial.numero_lacre || 'N/I'}</p>
                      </div>
                   </div>

                   {/* Linha do Tempo */}
                   <div className="space-y-6">
                     <h4 className="text-[10px] font-black text-gray-900 border-b border-gray-100 pb-2 flex items-center gap-2">
                        <History size={14} className="text-pmpr-green" />
                        LINHA DO TEMPO DA CUSTÓDIA
                     </h4>

                     <div className="relative pl-6 space-y-8 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-100">
                        {selectedMaterial.historico?.map((h, idx) => (
                           <div key={h.id} className="relative">
                              {/* Círculo da timeline */}
                              <div className={`absolute -left-[22px] top-1 w-3 h-3 rounded-full border-2 border-white ring-2 ${idx === 0 ? 'ring-pmpr-green bg-pmpr-green' : 'ring-gray-200 bg-white'}`}></div>
                              
                              <div className="space-y-1">
                                <div className="flex justify-between items-start">
                                  <span className="text-[11px] font-bold text-gray-900 uppercase tracking-tight">
                                    {h.status_na_epoca?.replace(/_/g, ' ')}
                                  </span>
                                  <span className="text-[10px] text-gray-400 font-medium">
                                    {new Date(h.data_criacao).toLocaleString('pt-BR')}
                                  </span>
                                </div>
                                <p className="text-xs text-gray-500 leading-relaxed italic">"{h.observacao}"</p>
                                <div className="flex items-center gap-1.5 mt-2">
                                  <User size={12} className="text-pmpr-green" />
                                  <span className="text-[10px] font-bold text-pmpr-green uppercase tracking-wider">
                                    {h.criado_por_nome || 'Sistema'}
                                  </span>
                                </div>
                              </div>
                           </div>
                        ))}
                     </div>
                   </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

function XIcon({ size }) {
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>;
}
