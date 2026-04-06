import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ShieldAlert, CheckCircle, Search, Flame, 
  Package, Info, Printer, Filter, ArrowRight, Box, Loader2
} from 'lucide-react';
import api, { materiaisService } from '../services/api';

const STATUS_COLORS = {
  'ARMAZENADO': 'bg-emerald-100 text-emerald-700 border-emerald-200',
  'AUTORIZADO': 'bg-amber-100 text-amber-700 border-amber-200',
  'AGUARDANDO_INCINERACAO': 'bg-blue-100 text-blue-700 border-blue-200',
  'INCINERADO': 'bg-gray-100 text-gray-500 border-gray-200',
};

const STATUS_LABELS = {
  'ARMAZENADO': 'No Cofre',
  'AUTORIZADO': 'Autorizado (Avulso)',
  'AGUARDANDO_INCINERACAO': 'Em Lote de Queima',
  'INCINERADO': 'Destruído',
};

export default function CustodiaLista() {
  const [materiais, setMateriais] = useState({ cofre: [], prontos: [] });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [tab, setTab] = useState('cofre');
  const [busca, setBusca] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await materiaisService.getAll({ categoria: 'ENTORPECENTE' });
      const data = res.data.results || res.data;
      setMateriais({
        cofre: data.filter(m => ['ARMAZENADO', 'AUTORIZADO', 'AGUARDANDO_INCINERACAO'].includes(m.status)),
        prontos: data.filter(m => ['AUTORIZADO', 'AGUARDANDO_INCINERACAO'].includes(m.status))
      });
    } catch (e) {
      console.error('Erro ao carregar custódia:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const autorizarDestruicao = async (id) => {
    if (!window.confirm("Confirmar que existe decisão judicial autorizando a destruição deste material?")) return;
    setActionLoading(id);
    try {
      await materiaisService.autorizar(id);
      alert('Material autorizado e encaminhado para loteamento automático!');
      loadData();
    } catch (e) {
      alert('Erro: ' + (e.response?.data?.error || e.message));
    } finally {
      setActionLoading(null);
    }
  };

  const dados = tab === 'cofre' ? materiais.cofre : materiais.prontos;
  const filtrados = dados.filter(m => 
    !busca || 
    m.bou?.toLowerCase().includes(busca.toLowerCase()) || 
    m.numero_lacre?.toLowerCase().includes(busca.toLowerCase())
  );

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-black text-pmpr-green flex items-center gap-3 lowercase">
            <Package className="text-pmpr-gold" /> ESTOQUE CUSTÓDIA
          </h1>
          <p className="text-gray-500 font-medium tracking-tight">Controle físico e autorizações judiciais de entorpecentes</p>
        </div>
        <div className="relative w-72">
          <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input 
            type="text" placeholder="Buscar por BOU ou Lacre..." 
            value={busca} onChange={(e) => setBusca(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-pmpr-green outline-none text-sm transition-all shadow-sm"
          />
        </div>
      </header>

      <div className="flex gap-4">
        <button 
          onClick={() => setTab('cofre')} 
          className={`flex items-center gap-3 px-6 py-4 rounded-2xl font-bold transition-all shadow-sm ${tab === 'cofre' ? 'bg-pmpr-green text-white ring-4 ring-emerald-100' : 'bg-white text-gray-400 hover:bg-gray-50 border'}`}
        >
          <ShieldAlert size={20} /> NO COFRE 
          <span className={`px-2 py-0.5 rounded-full text-xs ${tab === 'cofre' ? 'bg-white/20' : 'bg-gray-100'}`}>{materiais.cofre.length}</span>
        </button>
        <button 
          onClick={() => setTab('prontos')} 
          className={`flex items-center gap-3 px-6 py-4 rounded-2xl font-bold transition-all shadow-sm ${tab === 'prontos' ? 'bg-orange-600 text-white ring-4 ring-orange-100' : 'bg-white text-gray-400 hover:bg-gray-50 border'}`}
        >
          <Flame size={20} /> PRONTO PARA INCINERAR
          <span className={`px-2 py-0.5 rounded-full text-xs ${tab === 'prontos' ? 'bg-white/20' : 'bg-gray-100'}`}>{materiais.prontos.length}</span>
        </button>
      </div>

      <div className="bg-white rounded-3xl shadow-xl border border-gray-100 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50/50 border-b border-gray-100">
              <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-gray-400">Origem / BOU</th>
              <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-gray-400">Identificação</th>
              <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-gray-400">Peso Real</th>
              <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-gray-400">Status</th>
              {tab === 'prontos' && <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-gray-400">Lote</th>}
              <th className="px-6 py-5 text-[10px] font-black uppercase tracking-widest text-gray-400 text-center">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {loading ? (
              <tr><td colSpan="6" className="px-6 py-20 text-center text-gray-300 font-bold uppercase tracking-widest animate-pulse">Carregando Inventário...</td></tr>
            ) : filtrados.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-20 text-center">
                  <div className="flex flex-col items-center gap-2 opacity-20">
                    <Package size={48} />
                    <p className="font-bold uppercase text-sm">Nenhum item encontrado</p>
                  </div>
                </td>
              </tr>
            ) : (
              filtrados.map((m) => (
                <tr key={m.id} className="hover:bg-gray-50/50 transition-colors group">
                  <td className="px-6 py-5">
                    <p className="font-black text-gray-800 text-sm">{m.bou || '-'}</p>
                    <p className="text-[10px] text-gray-400 font-bold uppercase">{m.vara?.replace('VARA_', 'Vara ')}</p>
                  </td>
                  <td className="px-6 py-5">
                    <p className="text-sm font-bold text-pmpr-green">{m.substancia?.replace('_', ' ') || m.categoria}</p>
                    <p className="text-[10px] text-gray-400 font-medium">Lacre: {m.numero_lacre || 'N/I'}</p>
                  </td>
                  <td className="px-6 py-5">
                    <div className="bg-emerald-50 text-emerald-700 px-3 py-1 rounded-lg inline-block font-black text-sm border border-emerald-100">
                      {m.peso_formatado || m.peso_real || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-tighter border ${STATUS_COLORS[m.status] || 'bg-gray-100'}`}>
                      {STATUS_LABELS[m.status] || m.status}
                    </span>
                  </td>
                  {tab === 'prontos' && (
                    <td className="px-6 py-5">
                      {m.lote ? (
                        <div className="flex items-center gap-1.5 text-blue-600 font-bold text-xs">
                          <Box size={14} /> {m.lote_identificador || 'EM LOTE'}
                        </div>
                      ) : (
                        <span className="text-gray-300 text-xs font-medium italic">Aguardando...</span>
                      )}
                    </td>
                  )}
                  <td className="px-6 py-5 text-center">
                    {m.status === 'ARMAZENADO' ? (
                      <button 
                         onClick={() => autorizarDestruicao(m.id)}
                         className="bg-white border-2 border-pmpr-green text-pmpr-green px-4 py-2 rounded-xl text-xs font-black hover:bg-pmpr-green hover:text-white transition-all shadow-sm"
                      >
                        AUTORIZAR QUEIMA
                      </button>
                    ) : (
                      <div className="flex justify-center text-emerald-500 opacity-20"><CheckCircle size={24} /></div>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <div className="bg-gray-50 rounded-2xl p-6 border border-gray-100 flex items-start gap-4">
        <div className="bg-white p-3 rounded-full shadow-sm text-pmpr-green"><Info size={24} /></div>
        <div className="text-sm text-gray-600">
          <p className="font-bold text-gray-800 mb-1 uppercase tracking-tight">Protocolo de Autorização</p>
          <p>Ao autorizar a queima, o material é automaticamente vinculado a um lote (caixa) de até 20 processos. No dia da incineração, imprima a <b>Certidão Coletiva</b> para coleta das assinaturas de todas as autoridades presentes.</p>
        </div>
      </div>
    </div>
  );
}
