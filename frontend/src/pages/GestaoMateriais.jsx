import { useState, useEffect } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Filter, Search, Printer, CheckSquare, Square, FileText, CheckCircle } from 'lucide-react';

export default function GestaoMateriais() {
  const [materiais, setMateriais] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selecionados, setSelecionados] = useState([]);
  const [filtroCategoria, setFiltroCategoria] = useState('');
  const [busca, setBusca] = useState('');

  const loadMateriais = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filtroCategoria) params.append('categoria', filtroCategoria);
      
      const res = await axios.get(`http://127.0.0.1:8000/api/materiais/?${params.toString()}`);
      let data = res.data.results || res.data;
      
      const forumMateriais = data.filter(m => 
        ['SOM', 'FACA', 'SIMULACRO', 'OUTROS'].includes(m.categoria) &&
        !['OFICIO_GERADO', 'ENTREGUE_AO_JUDICIARIO'].includes(m.status)
      );
      
      setMateriais(forumMateriais);
    } catch (error) {
      console.error('Erro ao buscar materiais:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMateriais();
  }, [filtroCategoria]);

  const toggleSelect = (id) => {
    if (selecionados.includes(id)) {
      setSelecionados(selecionados.filter(i => i !== id));
    } else {
      setSelecionados([...selecionados, id]);
    }
  };

  const toggleAll = () => {
    if (selecionados.length === materiais.length) {
      setSelecionados([]);
    } else {
      setSelecionados(materiais.map(m => m.id));
    }
  };

  const gerarOficio = async () => {
    if (selecionados.length === 0) {
      return alert('Selecione pelo menos um item!');
    }
    
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/materiais/gerar_oficio/', {
        materiais_ids: selecionados
      });
      
      if (res.data.file_url) {
        window.open(`http://127.0.0.1:8000${res.data.file_url}`, '_blank');
      }
      
      alert(`Ofício gerado com sucesso! ${selecionados.length} itens serão remetidos.`);
      setSelecionados([]);
      loadMateriais();
    } catch (e) {
      console.error(e);
      alert('Erro na geração de Ofício: ' + (e.response?.data?.error || 'Verifique o console'));
    }
  };

  const filteredMateriais = materiais.filter(m => {
    if (!busca) return true;
    const term = busca.toUpperCase();
    return (
      (m.bou || '').toUpperCase().includes(term) ||
      (m.numero_lacre || '').toUpperCase().includes(term) ||
      (m.descricao_geral || '').toUpperCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      <header className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-pmpr-green flex items-center gap-3">
            <FileText size={32} /> Ofícios de Remessa
          </h1>
          <p className="text-gray-500 mt-1">Geração de ofícios para envio de materiais ao Fórum</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="bg-blue-50 border border-blue-200 px-4 py-2 rounded-lg">
            <span className="text-blue-800 font-bold text-lg">{selecionados.length}</span>
            <span className="text-blue-600 text-sm ml-2">selecionados</span>
          </div>
          <button 
            onClick={gerarOficio}
            disabled={selecionados.length === 0}
            className="bg-pmpr-gold hover:bg-yellow-600 disabled:bg-gray-400 text-white font-bold py-3 px-6 rounded-lg shadow-md flex items-center gap-2 transition"
          >
            <Printer size={20} />
            Gerar Ofício ({selecionados.length})
          </button>
        </div>
      </header>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
          <div className="flex gap-4">
            <div className="relative">
              <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input 
                type="text" 
                value={busca}
                onChange={(e) => setBusca(e.target.value)}
                placeholder="Buscar por BOU ou Lacre..." 
                className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg w-64 text-sm"
              />
            </div>
            
            <select 
              value={filtroCategoria}
              onChange={(e) => setFiltroCategoria(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg text-sm"
            >
              <option value="">Todas Categorias</option>
              <option value="SOM">Som/Eletrônicos</option>
              <option value="FACA">Armas Brancas</option>
              <option value="SIMULACRO">Simulacros</option>
              <option value="OUTROS">Outros</option>
            </select>
          </div>
          
          <button onClick={loadMateriais} className="text-pmpr-green hover:text-green-700 text-sm font-medium flex items-center gap-2">
            <Filter size={16} /> Atualizar
          </button>
        </div>

        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200 text-xs uppercase text-gray-500">
              <th className="p-4 w-12">
                <button onClick={toggleAll} className="text-pmpr-green hover:text-green-700">
                  {selecionados.length === materiais.length && materiais.length > 0 ? (
                    <CheckSquare size={20} />
                  ) : (
                    <Square size={20} />
                  )}
                </button>
              </th>
              <th className="p-4">BOU</th>
              <th className="p-4">Categoria</th>
              <th className="p-4">Descrição</th>
              <th className="p-4">Lacre</th>
              <th className="p-4">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredMateriais.map((item) => (
              <motion.tr 
                initial={{ opacity: 0 }} 
                animate={{ opacity: 1 }}
                key={item.id} 
                className={`border-b border-gray-100 hover:bg-gray-50 transition cursor-pointer ${selecionados.includes(item.id) ? 'bg-green-50' : ''}`}
                onClick={() => toggleSelect(item.id)}
              >
                <td className="p-4">
                  {selecionados.includes(item.id) ? (
                    <CheckSquare size={20} className="text-pmpr-green" />
                  ) : (
                    <Square size={20} className="text-gray-300" />
                  )}
                </td>
                <td className="p-4">
                  <span className="font-bold text-pmpr-green">{item.bou || '-'}</span>
                  {item.processo && <div className="text-xs text-gray-400">{item.processo}</div>}
                </td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded text-xs font-bold tracking-wide ${
                    item.categoria === 'SOM' ? 'bg-purple-100 text-purple-700' :
                    item.categoria === 'FACA' ? 'bg-red-100 text-red-700' :
                    item.categoria === 'SIMULACRO' ? 'bg-orange-100 text-orange-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {item.categoria === 'SOM' ? 'Som/Eletrônico' :
                     item.categoria === 'FACA' ? 'Arma Branca' :
                     item.categoria === 'SIMULACRO' ? 'Simulacro' : 'Outros'}
                  </span>
                </td>
                <td className="p-4 text-gray-600 text-sm">{item.descricao_geral || '-'}</td>
                <td className="p-4 font-mono text-sm">{item.numero_lacre || '-'}</td>
                <td className="p-4">
                  <span className="flex items-center gap-2 text-orange-600 text-sm font-medium">
                    <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                    Aguardando Ofício
                  </span>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
        
        {filteredMateriais.length === 0 && (
          <div className="p-12 text-center text-gray-400">
            <FileText size={48} className="mx-auto mb-4 opacity-50" />
            <p>Nenhum material pendente para geração de ofício.</p>
            <p className="text-sm mt-2">Materiais das categorias Som, Arma Branca, Simulacro e Outros aparecerão aqui.</p>
          </div>
        )}
      </div>
    </div>
  );
}
