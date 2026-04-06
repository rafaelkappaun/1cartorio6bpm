import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Layers, Flame, Plus, Printer, FileText, Search, ChevronDown, 
  ChevronUp, Trash2, Box, Scale, AlertTriangle, CheckCircle, 
  Clock, Package, Upload, Loader2
} from 'lucide-react';
import { lotesService, materiaisService } from '../services/api';

const COLORS = {
  ABERTO: 'bg-amber-50 border-amber-200 text-amber-700',
  PRONTO: 'bg-emerald-50 border-emerald-200 text-emerald-700',
  INCINERADO: 'bg-gray-100 border-gray-200 text-gray-400'
};

export default function LotesIncineracao() {
  const [lotes, setLotes] = useState([]);
  const [autorizados, setAutorizados] = useState([]); 
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('abertos');
  const [expandedLote, setExpandedLote] = useState(null);
  const [showFinalizeModal, setShowFinalizeModal] = useState(false);
  const [selectedLoteIds, setSelectedLoteIds] = useState([]);
  const [file, setFile] = useState(null);
  const [protocolo, setProtocolo] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      const [resLotes, resMateriais] = await Promise.all([
        lotesService.getAll(),
        materiaisService.getAll({ status: 'AUTORIZADO' })
      ]);
      setLotes(resLotes.data.results || resLotes.data);
      setAutorizados(resMateriais.data.results || resMateriais.data);
      setSelectedLoteIds([]);
    } catch (e) {
      console.error('Erro ao carregar lotes:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const toggleSelect = (id) => {
    setSelectedLoteIds(prev => prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]);
  };

  const selecionarTodos = () => {
    const abertos = lotes.filter(l => l.status === 'ABERTO').map(l => l.id);
    setSelectedLoteIds(selectedLoteIds.length === abertos.length ? [] : abertos);
  };

  const imprimirCapa = async (id) => {
    try {
      const res = await lotesService.imprimirCapa(id);
      window.open(res.data.url, '_blank');
    } catch (e) { alert('Erro ao gerar capa.'); }
  };

  const imprimirTodasCapas = async () => {
    if (selectedLoteIds.length === 0) return alert('Selecione os lotes primeiro!');
    try {
      const response = await lotesService.imprimirCapasMassa(selectedLoteIds);
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');
    } catch (e) { alert('Erro ao gerar capas.'); }
  };

  const imprimirCertidaoColetiva = async () => {
    try {
      const res = await lotesService.imprimirCertidaoVara();
      window.open(res.data.url, '_blank');
    } catch (e) { alert('Erro: ' + (e.response?.data?.error || 'Nenhum lote pronto para certidão.')); }
  };

  const removerDoLote = async (loteId, materialId) => {
    if (!window.confirm("Deseja remover este item do lote? Ele voltará para a lista de autorizados avulsos.")) return;
    try {
      await lotesService.removerMaterial(loteId, materialId);
      loadData();
    } catch (e) { alert('Erro ao remover material.'); }
  };

  const finalizarMassa = async (e) => {
    e.preventDefault();
    if (!file) return alert('Selecione o arquivo assinado!');
    if (!protocolo) return alert('Informe o número do protocolo do processo de inciteração!');
    if (selectedLoteIds.length === 0) return;
    
    if (!window.confirm(`ATENÇÃO: Você está prestes a incinerar ${selectedLoteIds.length} lotes definitivamente. Confirma?`)) return;

    setLoading(true);
    try {
      await lotesService.finalizarMassa(selectedLoteIds, protocolo, file);
      alert('Incinerado! Todos os lotes selecionados receberam baixa e o protocolo foi registrado.');
      setShowFinalizeModal(false);
      setSelectedLoteIds([]);
      setFile(null);
      setProtocolo('');
      loadData();
    } catch (e) {
      alert('Erro ao finalizar: ' + (e.response?.data?.error || 'Falha no upload.'));
    } finally {
      setLoading(false);
    }
  };

  const lotesExibidos = lotes.filter(l => tab === 'abertos' ? l.status === 'ABERTO' : l.status === 'INCINERADO');

  return (
    <div className="max-w-7xl mx-auto pb-12">
      <header className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-pmpr-green flex items-center gap-3 tracking-tighter">
            <Flame className="text-orange-500" /> Remessa Semestral
          </h1>
          <p className="text-gray-500 font-medium tracking-tight">Gestão de transporte e baixa coletiva de entorpecentes</p>
        </div>
        <div className="flex gap-3">
          <button 
             onClick={imprimirTodasCapas}
             disabled={selectedLoteIds.length === 0}
             className="bg-white text-pmpr-green border-2 border-pmpr-green px-5 py-2.5 rounded-xl font-bold flex items-center gap-2 hover:bg-gray-50 transition-all shadow-sm disabled:opacity-30"
          >
            <Printer size={18} /> IMPRIMIR {selectedLoteIds.length} CAPAS
          </button>
          <button 
            onClick={imprimirCertidaoColetiva}
            className="bg-white text-emerald-600 border-2 border-emerald-500 px-5 py-2.5 rounded-xl font-bold flex items-center gap-2 hover:bg-emerald-50 transition-all shadow-sm"
          >
            <FileText size={18} /> CERTIDÃO POR VARA
          </button>
          <button 
            onClick={() => { if(selectedLoteIds.length > 0) setShowFinalizeModal(true); else alert('Selecione pelo menos um lote!') }}
            disabled={selectedLoteIds.length === 0}
            className="bg-pmpr-green text-pmpr-gold px-6 py-2.5 rounded-xl font-bold flex items-center gap-2 shadow-lg hover:opacity-90 transition-all disabled:opacity-50"
          >
            <CheckCircle size={20} /> FINALIZAR BAIXA ({selectedLoteIds.length})
          </button>
        </div>
      </header>

      {/* Action Banner */}
      <div className="bg-gradient-to-r from-gray-50 to-white border border-gray-200 p-5 rounded-3xl mb-8 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-6">
           <div className="bg-pmpr-green p-3 rounded-2xl shadow-lg border-b-4 border-black"><Layers size={24} className="text-pmpr-gold" /></div>
           <div>
             <p className="text-gray-900 font-black uppercase text-sm tracking-tight">Fluxo de Incineração em Massa</p>
             <p className="text-xs text-gray-400 font-medium">Selecione os lotes prontos, imprima as capas e o termo geral, e finalize ao retornar.</p>
           </div>
        </div>
        {tab === 'abertos' && (
          <button onClick={selecionarTodos} className="text-[10px] font-black text-pmpr-green bg-white px-5 py-2.5 rounded-xl shadow-md border hover:scale-105 active:scale-95 transition-all">
            {selectedLoteIds.length === lotesExibidos.length ? 'DESMARCAR TUDO' : 'SELECIONAR TODAS AS CAIXAS'}
          </button>
        )}
      </div>

      <div className="flex gap-4 mb-8">
        {[
          { id: 'abertos', label: 'Prontos para Queima', icon: <Package size={18} />, count: lotes.filter(l => l.status === 'ABERTO').length },
          { id: 'concluidos', label: 'Histórico de Incineração', icon: <CheckCircle size={18} />, count: lotes.filter(l => l.status === 'INCINERADO').length }
        ].map(t => (
          <button 
            key={t.id} onClick={() => { setTab(t.id); setSelectedLoteIds([]); }}
            className={`flex items-center gap-3 px-6 py-3 rounded-2xl font-bold transition-all shadow-sm ${tab === t.id ? 'bg-white border-2 border-pmpr-green text-pmpr-green' : 'bg-gray-100 text-gray-400 border-2 border-transparent'}`}
          >
            {t.icon} {t.label} 
            <span className="bg-pmpr-green/10 text-pmpr-green px-2 py-0.5 rounded-full text-xs">{t.count}</span>
          </button>
        ))}
      </div>

      {loading && lotes.length === 0 ? (
        <div className="p-20 text-center animate-pulse text-gray-400 font-bold uppercase tracking-widest italic">Processando remessa...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {lotesExibidos.map(lote => (
            <LoteCard 
              key={lote.id} 
              lote={lote} 
              selected={selectedLoteIds.includes(lote.id)}
              onSelect={() => toggleSelect(lote.id)}
              expanded={expandedLote === lote.id} 
              onToggle={() => setExpandedLote(expandedLote === lote.id ? null : lote.id)}
              onPrintCapa={() => imprimirCapa(lote.id)}
              onRemove={(matId) => removerDoLote(lote.id, matId)}
            />
          ))}
          
          {lotesExibidos.length === 0 && (
            <div className="col-span-full bg-white border-2 border-dashed border-gray-200 rounded-3xl p-16 text-center text-gray-300">
              <Package size={48} className="mx-auto mb-4 opacity-20" />
              <p className="font-bold text-lg italic">Nenhuma caixa aberta no momento</p>
            </div>
          )}
        </div>
      )}

      {/* Modal de Finalização EM MASSA */}
      <AnimatePresence>
        {showFinalizeModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }} className="bg-white rounded-3xl shadow-2xl w-full max-w-lg overflow-hidden border-t-8 border-orange-500">
              <div className="bg-white p-8 text-center">
                <div className="bg-orange-100 w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4">
                   <Flame size={40} className="text-orange-600" />
                </div>
                <h3 className="text-2xl font-black text-gray-800 uppercase tracking-tight">Finalizar {selectedLoteIds.length} Lotes</h3>
                <p className="text-gray-500 text-sm font-medium mt-1">Isso dará baixa em todos os processos selecionados.</p>
              </div>
              <form onSubmit={finalizarMassa} className="px-8 pb-8 space-y-6">
                <div className="bg-orange-50 border border-orange-100 p-4 rounded-2xl text-orange-800 text-xs flex gap-3">
                  <AlertTriangle className="flex-shrink-0" size={18} />
                  <p>Certifique-se de que o <b>Termo de Destruição</b> assinado cita todos os números de BOU/Lacre contidos nestas caixas.</p>
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 mb-2 uppercase tracking-widest">Protocolo de Incineração (e-Protocolo)</label>
                  <input 
                    type="text" 
                    placeholder="Ex: 21.000.000-0"
                    value={protocolo}
                    onChange={(e) => setProtocolo(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-2xl text-sm focus:ring-2 focus:ring-orange-500 outline-none transition-all font-bold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-gray-500 mb-2 uppercase tracking-widest">Documento de Incineração (PDF)</label>
                  <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed rounded-2xl cursor-pointer hover:bg-orange-50/30 border-gray-200 group transition-all">
                    <Upload className="text-gray-300 group-hover:text-orange-500" size={32} />
                    <span className="mt-2 text-xs text-gray-500 font-bold">{file ? file.name : "Arraste ou clique para o upload"}</span>
                    <input type="file" className="hidden" accept=".pdf" onChange={(e) => setFile(e.target.files[0])} />
                  </label>
                </div>
                <div className="flex gap-4 pt-2">
                  <button type="button" onClick={() => setShowFinalizeModal(false)} className="flex-1 py-4 bg-gray-100 text-gray-500 rounded-2xl font-black text-xs hover:bg-gray-200 transition-colors">VOLTAR</button>
                  <button type="submit" disabled={!file || !protocolo || loading} className="flex-1 py-4 bg-orange-600 text-white rounded-2xl font-black text-xs shadow-lg shadow-orange-200 disabled:opacity-30 transition-all">BAIXAR REMESSA</button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}

function LoteCard({ lote, selected, onSelect, expanded, onToggle, onPrintCapa, onRemove }) {
  const percent = Math.min((lote.processos_count / 20) * 100, 100);
  
  return (
    <motion.div className={`relative bg-white border-2 rounded-3xl transition-all overflow-hidden flex flex-col ${selected ? 'border-orange-500 shadow-orange-100 shadow-xl scale-[1.02]' : 'border-gray-50 shadow-sm hover:border-gray-200'}`}>
      
      {lote.status === 'ABERTO' && (
        <div className="absolute top-5 right-5 z-10">
          <input 
             type="checkbox" checked={selected} onChange={onSelect} 
             className="w-6 h-6 rounded-lg text-orange-600 focus:ring-orange-500 cursor-pointer border-gray-200" 
          />
        </div>
      )}

      <div className={`p-5 flex justify-between items-start ${lote.status === 'ABERTO' ? 'bg-gradient-to-br from-white to-gray-50/50' : 'bg-gray-100'}`}>
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-2xl ${lote.status === 'ABERTO' ? (selected ? 'bg-orange-500 text-white' : 'bg-amber-100 text-amber-600') : 'bg-gray-200 text-gray-500'}`}>
            <Box size={22} />
          </div>
          <div>
            <h3 className="font-black text-gray-800 text-lg uppercase tracking-tighter leading-none mb-1">{lote.identificador}</h3>
            <div className="flex items-center gap-1.5">
               <span className={`px-2 py-0.5 rounded-full text-[8px] font-black uppercase tracking-widest border ${COLORS[lote.status]}`}>{lote.status}</span>
               <span className="text-[9px] text-gray-400 font-bold uppercase">{new Date(lote.data_criacao).toLocaleDateString('pt-BR')}</span>
            </div>
          </div>
        </div>
        <button onClick={onToggle} className="p-2 hover:bg-gray-200 rounded-xl transition-colors mr-10">
          {expanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>
      </div>

      <div className="px-6 py-4 flex-1">
        <div className="flex justify-between items-end mb-2">
          <div>
            <p className="text-[10px] font-bold text-gray-400 uppercase">Processos ({lote.processos_count} / 20)</p>
            {lote.status === 'ABERTO' && (
              <p className="text-[9px] text-amber-600 font-bold italic">
                Aguardando +{20 - lote.processos_count} processos p/ fechar autom.
              </p>
            )}
          </div>
          <p className="text-xs font-black text-pmpr-green">{(lote.peso_total / 1000).toFixed(2)} kg</p>
        </div>
        <div className="h-2 w-full bg-gray-100 rounded-full overflow-hidden">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${percent}%` }}
            className={`h-full ${percent >= 100 ? 'bg-orange-500' : 'bg-emerald-500'}`} 
          />
        </div>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }} className="px-6 pb-6 overflow-hidden">
             <div className="border-t pt-4 space-y-2">
               <p className="text-[10px] font-bold text-gray-400 uppercase mb-2">Itens no Lote:</p>
               {lote.materiais?.map(mat => (
                 <div key={mat.id} className="flex justify-between items-center text-xs p-2 bg-gray-50 rounded-lg group">
                   <div>
                     <p className="font-bold text-gray-700">{mat.bou}</p>
                     <p className="text-gray-400 text-[9px]">{mat.descricao_amigavel}</p>
                   </div>
                   {lote.status === 'ABERTO' && (
                     <button onClick={() => onRemove(mat.id)} className="text-red-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity">
                       <Trash2 size={14} />
                     </button>
                   )}
                 </div>
               ))}
             </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-2 border-t text-[11px] font-bold">
        <button 
          onClick={onPrintCapa}
          className="py-4 flex items-center justify-center gap-2 hover:bg-gray-50 border-r border-gray-100 transition-colors uppercase"
        >
          <Printer size={16} className="text-emerald-500" /> Imprimir Capa
        </button>
        {lote.status === 'ABERTO' ? (
          <button 
            onClick={onSelect}
            className={`py-4 flex items-center justify-center gap-2 transition-colors uppercase ${selected ? 'bg-orange-50 text-orange-600' : 'bg-white text-gray-400 hover:bg-gray-50'}`}
          >
            {selected ? <CheckCircle size={16} /> : <Layers size={16} />} 
            {selected ? 'Selecionado' : 'Selecionar'}
          </button>
        ) : (
          <div className="py-4 flex items-center justify-center gap-2 text-gray-300 uppercase cursor-not-allowed bg-gray-50/50">
            <CheckCircle size={16} /> Finalizado
          </div>
        )}
      </div>
    </motion.div>
  );
}
