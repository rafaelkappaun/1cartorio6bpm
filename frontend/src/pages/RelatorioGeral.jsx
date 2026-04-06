import { useState, useEffect } from 'react';
import { FileText, Download, Printer, Loader2, CheckCircle, AlertCircle, Layers, Scale, Trash2 } from 'lucide-react';
import api, { lotesService } from '../services/api';
import { useNavigate } from 'react-router-dom';

const TIPOS_RELATORIO = [
  { id: 'inventario', titulo: 'Inventário Geral', descricao: 'Relatório completo de todos os materiais apreendidos', icon: <FileText size={32} /> },
  { id: 'incineracao', titulo: 'Relatório de Incineração', descricao: 'Materiais autorizados e aguardando destruição', icon: <Trash2 size={32} /> },
  { id: 'custodia', titulo: 'Relatório de Custódia', descricao: 'Materiais armazenados no cofre', icon: <Scale size={32} /> },
  { id: 'lotes', titulo: 'Capa de Lotes', descricao: 'Gerar capas para impressão de caixas', icon: <Layers size={32} /> },
];

export default function RelatorioGeral() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(null);
  const [message, setMessage] = useState(null);
  const [lotes, setLotes] = useState([]);
  const [lotesSelecionados, setLotesSelecionados] = useState([]);
  const [filtros, setFiltros] = useState({
    categoria: '',
    status: '',
    ano: new Date().getFullYear(),
  });

  useEffect(() => {
    loadLotes();
  }, []);

  const loadLotes = async () => {
    try {
      const response = await lotesService.getAll();
      setLotes(response.data.results || response.data);
    } catch (e) {
      console.error('Erro ao carregar lotes:', e);
    }
  };

  const gerarRelatorio = async (tipo) => {
    setLoading(tipo);
    setMessage(null);
    try {
      const resPdf = await api.post('/materiais/gerar_relatorio/', {
        tipo: tipo === 'inventario' ? 'inventario' : tipo,
        filtros: filtros,
      });

      if (resPdf.data.file_url) {
        window.open(resPdf.data.file_url, '_blank');
        setMessage({ type: 'success', text: 'Relatório gerado com sucesso!' });
      }
    } catch (e) {
      console.error('Erro ao gerar relatório:', e);
      setMessage({ type: 'error', text: e.response?.data?.error || 'Erro ao gerar relatório. Verifique os filtros.' });
    } finally {
      setLoading(null);
    }
  };

  const gerarCapasLotes = async () => {
    if (lotesSelecionados.length === 0) {
      setMessage({ type: 'warning', text: 'Selecione pelo menos um lote.' });
      return;
    }
    setLoading('capas');
    try {
      const response = await lotesService.imprimirCapasMassa(lotesSelecionados);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
      setMessage({ type: 'success', text: `${lotesSelecionados.length} capa(s) gerada(s) com sucesso!` });
    } catch (e) {
      console.error('Erro ao gerar capas:', e);
      setMessage({ type: 'error', text: 'Erro ao gerar capas dos lotes.' });
    } finally {
      setLoading(null);
    }
  };

  const gerarCertidaoVara = async () => {
    setLoading('certidao');
    try {
      const response = await lotesService.imprimirCertidaoVara();
      if (response.data.url) {
        window.open(response.data.url, '_blank');
        setMessage({ type: 'success', text: 'Certidão coletiva gerada com sucesso!' });
      }
    } catch (e) {
      console.error('Erro ao gerar certidão:', e);
      setMessage({ type: 'error', text: 'Erro ao gerar certidão. Verifique se há lotes abertos.' });
    } finally {
      setLoading(null);
    }
  };

  const toggleLote = (id) => {
    setLotesSelecionados(prev => 
      prev.includes(id) ? prev.filter(l => l !== id) : [...prev, id]
    );
  };

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">Inventário e Relatórios</h1>
        <p className="text-gray-500">Gere relatórios e documentos oficiais</p>
      </header>

      {message && (
        <div className={`flex items-center gap-3 p-4 rounded-xl ${
          message.type === 'success' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
          message.type === 'error' ? 'bg-red-50 text-red-700 border border-red-200' :
          'bg-yellow-50 text-yellow-700 border border-yellow-200'
        }`}>
          {message.type === 'success' && <CheckCircle size={20} />}
          {message.type === 'error' && <AlertCircle size={20} />}
          {message.type === 'warning' && <AlertCircle size={20} />}
          {message.text}
        </div>
      )}

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-bold text-gray-800 mb-4">Filtros para Relatórios</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Ano</label>
            <select 
              value={filtros.ano}
              onChange={(e) => setFiltros({...filtros, ano: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              {[...Array(5)].map((_, i) => {
                const year = new Date().getFullYear() - i;
                return <option key={year} value={year}>{year}</option>;
              })}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Categoria</label>
            <select 
              value={filtros.categoria}
              onChange={(e) => setFiltros({...filtros, categoria: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">Todas</option>
              <option value="ENTORPECENTE">Entorpecentes</option>
              <option value="SOM">Som/Eletrônicos</option>
              <option value="FACA">Armas Brancas</option>
              <option value="SIMULACRO">Simulacros</option>
              <option value="DINHEIRO">Dinheiro</option>
              <option value="OUTROS">Outros</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select 
              value={filtros.status}
              onChange={(e) => setFiltros({...filtros, status: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="">Todos</option>
              <option value="RECEBIDO">Recebido</option>
              <option value="ARMAZENADO">Armazenado</option>
              <option value="AUTORIZADO">Autorizado</option>
              <option value="AGUARDANDO_INCINERACAO">Aguardando Incineração</option>
              <option value="INCINERADO">Incinerado</option>
            </select>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => gerarRelatorio('inventario')}
              disabled={loading === 'inventario'}
              className="w-full px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {loading === 'inventario' ? <Loader2 size={18} className="animate-spin" /> : <Download size={18} />}
              Gerar Relatório
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {TIPOS_RELATORIO.map((rel) => (
          <button
            key={rel.id}
            onClick={() => {
              if (rel.id === 'lotes') navigate('/lotes');
              else gerarRelatorio(rel.id);
            }}
            disabled={loading === rel.id}
            className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition border border-gray-100 hover:border-emerald-500 text-left group disabled:opacity-50"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-emerald-50 rounded-xl text-emerald-600 group-hover:bg-emerald-100 transition">
                {rel.icon}
              </div>
              {loading === rel.id && <Loader2 size={20} className="animate-spin text-emerald-600" />}
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">{rel.titulo}</h3>
            <p className="text-gray-500 text-sm">{rel.descricao}</p>
          </button>
        ))}
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-800">Ações Rápidas de Lotes</h2>
          <div className="flex gap-2">
            <button
              onClick={gerarCertidaoVara}
              disabled={loading === 'certidao'}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-lg transition flex items-center gap-2 disabled:opacity-50 text-sm"
            >
              {loading === 'certidao' ? <Loader2 size={16} className="animate-spin" /> : <Printer size={16} />}
              Certidão por Vara
            </button>
            <button
              onClick={gerarCapasLotes}
              disabled={loading === 'capas' || lotesSelecionados.length === 0}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition flex items-center gap-2 disabled:opacity-50 text-sm"
            >
              {loading === 'capas' ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
              Imprimir Capas ({lotesSelecionados.length})
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {lotes.map((lote) => (
            <label
              key={lote.id}
              className={`flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition ${
                lotesSelecionados.includes(lote.id)
                  ? 'bg-emerald-50 border-emerald-500'
                  : 'bg-gray-50 border-gray-200 hover:border-emerald-300'
              }`}
            >
              <input
                type="checkbox"
                checked={lotesSelecionados.includes(lote.id)}
                onChange={() => toggleLote(lote.id)}
                className="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500"
              />
              <div className="flex-1">
                <p className="font-semibold text-gray-900">{lote.identificador}</p>
                <p className="text-sm text-gray-500">
                  {lote.status === 'ABERTO' ? 'Aberto' : lote.status === 'INCINERADO' ? 'Incinerado' : lote.status}
                </p>
              </div>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
}
