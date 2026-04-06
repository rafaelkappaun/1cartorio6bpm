import { useState, useEffect } from 'react';
import { Scale, Search, Eye, CheckCircle, Loader2 } from 'lucide-react';
import { materiaisService } from '../services/api';

const STATUS_COLORS = {
  'RECEBIDO': 'bg-yellow-100 text-yellow-700',
  'ARMAZENADO': 'bg-emerald-100 text-emerald-700',
  'AUTORIZADO': 'bg-blue-100 text-blue-700',
  'INCINERADO': 'bg-gray-100 text-gray-700',
};

export default function ConferenciaLista() {
  const [materiais, setMateriais] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [busca, setBusca] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await materiaisService.getAll({ status: 'RECEBIDO' });
      const data = res.data.results || res.data;
      setMateriais(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const filtrados = materiais.filter(m => 
    !busca || 
    (m.bou && m.bou.toUpperCase().includes(busca.toUpperCase())) ||
    (m.numero_lacre && m.numero_lacre.toUpperCase().includes(busca.toUpperCase()))
  );

  const confirmarConferencia = async (id) => {
    const peso = prompt('Digite o peso real em gramas:');
    if (!peso) return;
    
    setActionLoading(id);
    try {
      await materiaisService.conferir(id, {
        peso_real: parseFloat(peso.replace(',', '.')),
        localizacao_no_cofre: 'Cofre Principal'
      });
      alert('Conferência realizada!');
      loadData();
    } catch (e) {
      alert('Erro: ' + (e.response?.data?.error || e.message));
    } finally {
      setActionLoading(null);
    }
  };

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pesagem / Conferência</h1>
          <p className="text-gray-500">Materiais aguardando conferência física</p>
        </div>
        <div className="flex items-center gap-2">
          <Search size={18} className="text-gray-400" />
          <input
            type="text"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar por BOU..."
            className="p-2 border rounded-lg"
          />
        </div>
      </header>

      <div className="bg-white rounded-xl shadow-sm overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 text-gray-600">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase">BOU</th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase">Lacre</th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase">Substância</th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase">Peso Est.</th>
              <th className="px-6 py-3 text-left text-xs font-semibold uppercase">Status</th>
              <th className="px-6 py-3 text-center text-xs font-semibold uppercase">Ações</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {loading ? (
              <tr>
                <td colSpan="6" className="px-6 py-12 text-center text-gray-400">Carregando...</td>
              </tr>
            ) : filtrados.length === 0 ? (
              <tr>
                <td colSpan="6" className="px-6 py-12 text-center text-gray-400">Nenhum material pendente</td>
              </tr>
            ) : (
              filtrados.map((mat) => (
                <tr key={mat.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 font-semibold text-emerald-600">{mat.bou || '-'}</td>
                  <td className="px-6 py-4 font-mono text-sm">{mat.numero_lacre || '-'}</td>
                  <td className="px-6 py-4">{mat.substancia?.replace('_', ' ') || mat.categoria}</td>
                  <td className="px-6 py-4">{mat.peso_formatado || mat.peso_estimado || '-'}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[mat.status] || 'bg-gray-100'}`}>
                      {mat.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={() => confirmarConferencia(mat.id)}
                      className="bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-emerald-600 flex items-center gap-2 mx-auto"
                    >
                      <CheckCircle size={16} /> Conferir
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
