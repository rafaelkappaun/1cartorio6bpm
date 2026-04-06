import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { useParams, useNavigate } from 'react-router-dom';
import { Plus, Trash2, Save, FileText, UserPlus, Package, Search, Calendar, AlertCircle } from 'lucide-react';

const DROGAS_LISTA = [
  { value: 'MACONHA', label: 'Maconha (Flor/Cume)' },
  { value: 'SKUNK', label: 'Skunk (Maconha Importada)' },
  { value: 'HASHISH', label: 'Haxixe (Hashish)' },
  { value: 'COCAINA_PO', label: 'Cocaína (Pó/Branca)' },
  { value: 'COCAINA_CRA', label: 'Crack (Cocaína Base)' },
  { value: 'OPIACEOS', label: 'Ópio / Heroína' },
  { value: 'MDF', label: 'Maconha de Fumo (MDF)' },
  { value: 'LSD', label: 'LSD (Ácido)' },
  { value: 'ECSTASY', label: 'Ecstasy / MDMA' },
  { value: 'METANFETAMINA', label: 'Metanfetamina (Crystal)' },
  { value: 'COCAINAMINA', label: 'Cocainaína (Merla)' },
  { value: 'RECEPTACULO', label: 'Receptáculo/Eppendorf' },
  { value: 'SEMENTE', label: 'Semente de Maconha' },
  { value: 'COLHEITA', label: 'Planta/Colheita de Maconha' },
  { value: 'OUTRA', label: 'Outra Substância' },
];

const UNIDADES_PM = [
  'RPA', 'RPA-1', 'RPA-2', 'ROTAM', 'ROCAM', 'CHOQUE', 'CAVALARIA', 
  'TRANSITO', 'CPU', 'P2', 'P2-GERAIS', 'DEAEV', 'GOTRAN', 
  'BPFRON', 'BOPE', 'BPCHQ', 'BPMON', 'FORÇA TÁTICA', 'OUTRA'
];

export default function CadastroEntrada() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [loadingNaturezas, setLoadingNaturezas] = useState(true);
  const [temApreensao, setTemApreensao] = useState(true);
  const [duplicateOcorrencia, setDuplicateOcorrencia] = useState(null);
  
  const currentYear = new Date().getFullYear();
  const today = new Date().toISOString().split('T')[0];
  
  const [formData, setFormData] = useState({
    bou_ano: currentYear.toString(),
    bou_numero: '',
    data_fato: today,
    vara: 'VARA_01',
    processo: '',
    natureza_penal: '',
    natureza_penal_id: null,
    policial_nome: '',
    policial_graduacao: 'SD',
    rg_policial: '',
    unidade_origem: 'RPA',
    observacao: '',
    termo_depositario_fiel: false,
    noticiados: []
  });

  const [naturezasList, setNaturezasList] = useState([]);
  const [naturezasSuggestions, setNaturezasSuggestions] = useState([]);
  const [showNaturezaDropdown, setShowNaturezaDropdown] = useState(false);
  const naturezaRef = useRef(null);

  const loadData = async () => {
    if (!id) return;
    setLoading(true);
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/ocorrencias/${id}/`);
      const data = res.data;
      const [ano, numero] = data.bou.split('/');
      
      setFormData({
        ...data,
        bou_ano: ano,
        bou_numero: numero,
        noticiados: data.noticiados.map(n => ({
          ...n,
          materiais: n.materiais.map(m => ({ ...m }))
        }))
      });
      setTemApreensao(data.noticiados.length > 0);
    } catch (e) {
      alert("Erro ao carregar dados da ocorrência.");
    } finally {
      setLoading(false);
    }
  };

  const loadNaturezas = async () => {
    setLoadingNaturezas(true);
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/naturezas-penais/');
      const data = res.data.results || res.data;
      setNaturezasList(data);
      setNaturezasSuggestions(data.slice(0, 15));
    } catch (err) { 
      console.error('Erro ao carregar naturezas:', err); 
    } finally {
      setLoadingNaturezas(false);
    }
  };

  useEffect(() => {
    loadNaturezas();
    if (id) loadData();
    const handleClickOutside = (e) => {
      if (naturezaRef.current && !naturezaRef.current.contains(e.target)) {
        setShowNaturezaDropdown(false);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [id]);

  const searchNaturezas = (term) => {
    if (!term) {
      setNaturezasSuggestions(naturezasList.slice(0, 10));
    } else {
      const filtered = naturezasList.filter(n => 
        n.nome.toUpperCase().includes(term.toUpperCase())
      );
      setNaturezasSuggestions(filtered.slice(0, 15));
    }
    setShowNaturezaDropdown(true);
  };

  const selectNatureza = (natureza) => {
    setFormData({
      ...formData,
      natureza_penal: natureza.nome,
      natureza_penal_id: natureza.id
    });
    setShowNaturezaDropdown(false);
  };

  const createNatureza = async (nome) => {
    try {
      const res = await axios.post('http://127.0.0.1:8000/api/naturezas-penais/', {
        nome: nome.toUpperCase(),
        tipo: 'TC'
      });
      await loadNaturezas();
      selectNatureza(res.data);
    } catch (err) {
      alert('Erro ao criar natureza penal');
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData({ 
      ...formData, 
      [name]: type === 'checkbox' ? checked : value 
    });
  };

  const handleNaturezaInput = (e) => {
    const value = e.target.value;
    setFormData({ ...formData, natureza_penal: value, natureza_penal_id: null });
    searchNaturezas(value);
  };

  const formatarProcesso = (value) => {
    let v = value.replace(/\D/g, '');
    if (v.length > 20) v = v.slice(0, 20);
    let formatted = v.slice(0, 7);
    if (v.length > 7) formatted += '-' + v.slice(7, 9);
    if (v.length > 9) formatted += '.' + v.slice(9, 13);
    if (v.length > 13) formatted += '.' + v.slice(13, 14);
    if (v.length > 14) formatted += '.' + v.slice(14, 16);
    if (v.length > 16) formatted += '.' + v.slice(16, 20);
    return formatted;
  };

  const handleProcessoChange = (e) => {
    const formatted = formatarProcesso(e.target.value);
    setFormData({ ...formData, processo: formatted });
  };

  const addNoticiado = () => {
    setFormData({
      ...formData,
      noticiados: [...formData.noticiados, { 
        nome: '', 
        materiais: [],
        observacao: ''
      }]
    });
  };

  const updateNoticiado = (nIndex, field, value) => {
    const updated = [...formData.noticiados];
    updated[nIndex][field] = value;
    setFormData({ ...formData, noticiados: updated });
  };

  const removeNoticiado = (nIndex) => {
    const updated = formData.noticiados.filter((_, i) => i !== nIndex);
    setFormData({ ...formData, noticiados: updated });
  };

  const addMaterial = (nIndex) => {
    const updated = [...formData.noticiados];
    updated[nIndex].materiais.push({
      categoria: 'ENTORPECENTE',
      substancia: '',
      nome_popular: '',
      peso_estimado: '',
      unidade: 'G',
      numero_lacre: '',
      descricao_geral: '',
      observacao_material: ''
    });
    setFormData({ ...formData, noticiados: updated });
  };

  const updateMaterial = (nIndex, mIndex, field, value) => {
    const updated = [...formData.noticiados];
    updated[nIndex].materiais[mIndex][field] = value;
    setFormData({ ...formData, noticiados: updated });
  };

  const removeMaterial = (nIndex, mIndex) => {
    const updated = [...formData.noticiados];
    updated[nIndex].materiais = updated[nIndex].materiais.filter((_, i) => i !== mIndex);
    setFormData({ ...formData, noticiados: updated });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.bou_numero) return alert('Número do BOU é obrigatório');
    if (!formData.policial_nome) return alert('Nome do policial é obrigatório');
    if (!formData.natureza_penal) return alert('Natureza penal é obrigatória');

    for (const n of formData.noticiados) {
      for (const m of n.materiais) {
        if (m.categoria === 'ENTORPECENTE' && !m.substancia) {
          return alert(`Por favor, informe a substância do material para o noticiado ${n.nome}.`);
        }
      }
    }

    setLoading(true);
    setDuplicateOcorrencia(null);

      try {
      const noticiadosPayload = [];
      if (formData.noticiados.length > 0) {
        for (const noti of formData.noticiados) {
          if (!noti.nome) continue;
          
          const materiaisPayload = [];
          for (const mat of noti.materiais) {
            materiaisPayload.push({
              id: mat.id || undefined,
              categoria: mat.categoria,
              substancia: mat.substancia || null,
              nome_popular: mat.nome_popular || null,
              peso_estimado: mat.peso_estimado ? parseFloat(mat.peso_estimado) : null,
              unidade: mat.unidade || 'G',
              numero_lacre: mat.numero_lacre || null,
              descricao_geral: mat.descricao_geral || null,
              observacao_material: mat.observacao_material || null
            });
          }
          
          noticiadosPayload.push({
            id: noti.id || undefined,
            nome: noti.nome.toUpperCase(),
            materiais: materiaisPayload,
            observacao: noti.observacao || null
          });
        }
      }

      const payload = {
        bou: `${formData.bou_ano}/${formData.bou_numero}`,
        data_registro_bou: formData.data_fato,
        vara: formData.vara,
        processo: formData.processo || null,
        natureza_penal: formData.natureza_penal,
        policial_nome: formData.policial_nome.toUpperCase(),
        policial_graduacao: formData.policial_graduacao,
        rg_policial: formData.rg_policial || null,
        unidade_origem: formData.unidade_origem,
        observacao: formData.observacao || null,
        noticiados: noticiadosPayload
      };

      const url = id ? `http://127.0.0.1:8000/api/ocorrencias/${id}/` : 'http://127.0.0.1:8000/api/ocorrencias/';
      const method = id ? 'put' : 'post';
      
      const res = await axios[method](url, payload);
      
      const pdfRes = await axios.get(`http://127.0.0.1:8000/api/ocorrencias/${res.data.id}/imprimir_recibo/`);
      window.open(pdfRes.data.url, '_blank');
      
      alert(id ? 'Alterações salvas com sucesso!' : 'Cadastro Finalizado. O Recibo foi aberto em nova aba!');
      
      if (!id) navigate('/cadastro', { replace: true });
      window.location.reload();
    } catch (err) {
      const errorData = err.response?.data;
      if (errorData?.bou && errorData.bou.some(m => m.includes("já existe"))) {
        try {
          const bouStr = `${formData.bou_ano}/${formData.bou_numero}`;
          const findRes = await axios.get(`http://127.0.0.1:8000/api/ocorrencias/buscar_por_bou/?bou=${bouStr}`);
          setDuplicateOcorrencia(findRes.data);
        } catch (findErr) {
          alert('Este BOU já está cadastrado, mas não foi possível localizar os detalhes.');
        }
      } else {
        alert('Erro: ' + (JSON.stringify(errorData) || 'Verifique os campos'));
      }
    } finally {
      setLoading(false);
    }
  };

  const labelClass = "block text-xs font-bold text-gray-500 mb-1 uppercase tracking-wide";
  const inputClass = "w-full p-2 border border-gray-300 rounded focus:ring-2 focus:ring-pmpr-gold focus:border-pmpr-gold outline-none text-sm";

  return (
    <div className="max-w-7xl mx-auto pb-12">
      <header className="mb-6 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-pmpr-green">{id ? 'Editar Ocorrência' : 'Registro de Ocorrência'}</h1>
          <p className="text-gray-500">{id ? `Editando BOU ${formData.bou}` : 'Cadastro de BOU e Apreensões'}</p>
        </div>
      </header>

      <AnimatePresence>
        {duplicateOcorrencia && (
          <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }} className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center justify-between gap-4 overflow-hidden">
            <div className="flex items-center gap-4">
              <div className="bg-red-500 p-2 rounded-full text-white"><AlertCircle size={24} /></div>
              <div>
                <p className="text-red-900 font-bold">BOU já cadastrado em sistema!</p>
                <p className="text-red-700 text-sm">A ocorrência {duplicateOcorrencia.bou} foi registrada em {new Date(duplicateOcorrencia.data_criacao).toLocaleDateString()}.</p>
              </div>
            </div>
            <button onClick={() => { navigate(`/editar/${duplicateOcorrencia.id}`); setDuplicateOcorrencia(null); }} className="bg-red-600 text-white px-6 py-2 rounded-lg font-bold hover:bg-red-700 transition">IR PARA EDIÇÃO</button>
          </motion.div>
        )}
      </AnimatePresence>

      <form onSubmit={handleSubmit} className="space-y-6">
        <section className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm">
          <h2 className="text-xl font-bold text-pmpr-green flex items-center gap-2 border-b pb-2 mb-4"><FileText size={20} /> 1. Dados do Boletim (BOU)</h2>
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-4">
            <div className="md:col-span-1">
              <label className={labelClass}>Ano *</label>
              <select name="bou_ano" value={formData.bou_ano} onChange={handleChange} className={inputClass}>
                {[currentYear, currentYear - 1, currentYear - 2].map(y => <option key={y} value={y}>{y}</option>)}
              </select>
            </div>
            <div className="md:col-span-1"><label className={labelClass}>Nº *</label><input name="bou_numero" value={formData.bou_numero} onChange={handleChange} className={inputClass + " font-bold"} required /></div>
            <div className="md:col-span-1"><label className={labelClass}>Data *</label><input type="date" name="data_fato" value={formData.data_fato} onChange={handleChange} max={today} className={inputClass} required /></div>
            <div className="md:col-span-1">
              <label className={labelClass}>Vara *</label>
              <select name="vara" value={formData.vara} onChange={handleChange} className={inputClass}>
                <option value="VARA_01">1ª Vara</option><option value="VARA_02">2ª Vara</option><option value="VARA_03">3ª Vara</option><option value="JECRIM">JECRIM</option>
              </select>
            </div>
            <div className="md:col-span-2" ref={naturezaRef}>
              <label className={labelClass}>Natureza *</label>
              <div className="relative">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input name="natureza_penal" value={formData.natureza_penal} onChange={handleNaturezaInput} onFocus={() => searchNaturezas(formData.natureza_penal)} className={inputClass + " uppercase pl-10"} placeholder="Selecione..." required />
                {showNaturezaDropdown && (
                  <div className="absolute z-50 w-full mt-1 bg-white border rounded-lg shadow-xl max-h-60 overflow-auto">
                    {naturezasSuggestions.length === 0 && formData.natureza_penal.length > 2 && (
                      <button type="button" onClick={() => createNatureza(formData.natureza_penal)} className="w-full px-4 py-3 text-left hover:bg-green-50 text-green-700 font-medium">+ Criar: "{formData.natureza_penal}"</button>
                    )}
                    {naturezasSuggestions.map(n => <button key={n.id} type="button" onClick={() => selectNatureza(n)} className="w-full px-4 py-3 text-left hover:bg-blue-50 border-b">{n.nome}</button>)}
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2"><label className={labelClass}>PROJUDI</label><input value={formData.processo} onChange={handleProcessoChange} className={inputClass} placeholder="0000000-00..." /></div>
            <div className="md:col-span-2"><label className={labelClass}>Observação de Conferência (Erros no BO)</label><input name="observacao" value={formData.observacao} onChange={handleChange} className={inputClass} /></div>
          </div>
        </section>

        <section className="bg-gray-50 p-6 rounded-xl border border-gray-200">
          <h2 className="text-xl font-bold text-gray-700 flex items-center justify-between mb-4">
            <div className="flex items-center gap-2"><Package size={20} /> 2. Apreensões</div>
            <label className="flex items-center gap-2 text-pmpr-green text-sm cursor-pointer border bg-white px-3 py-1.5 rounded-lg shadow-sm">
                <input type="checkbox" checked={temApreensao} onChange={(e) => setTemApreensao(e.target.checked)} className="w-4 h-4" />
                Houve apreensão?
            </label>
          </h2>

          {temApreensao && (
            <div className="space-y-4">
              <div className="flex justify-end"><button type="button" onClick={addNoticiado} className="bg-pmpr-green text-white px-4 py-2 rounded-lg text-sm font-bold flex items-center gap-2"><UserPlus size={16}/> ADD NOTICIADO</button></div>
              {formData.noticiados.map((noticiado, nIndex) => (
                <div key={nIndex} className="bg-white border rounded-xl overflow-hidden shadow-sm">
                   <div className="bg-gray-800 text-white p-3 flex justify-between items-center">
                      <input required placeholder="NOME DO NOTICIADO" value={noticiado.nome} onChange={(e) => updateNoticiado(nIndex, 'nome', e.target.value)} className="bg-transparent border-0 text-lg font-bold uppercase w-full focus:ring-0 outline-none" />
                      <button type="button" onClick={() => removeNoticiado(nIndex)} className="text-red-400 hover:text-red-500"><Trash2 size={20}/></button>
                   </div>
                   <div className="p-4 space-y-4">
                      <div className="space-y-3">
                        <div className="flex justify-between items-center text-xs font-bold text-gray-400 uppercase"><span>Itens</span><button type="button" onClick={() => addMaterial(nIndex)} className="text-pmpr-green border border-pmpr-green px-2 py-1 rounded">+ NOVO ITEM</button></div>
                        {noticiado.materiais.map((mat, mIndex) => (
                          <div key={mIndex} className="bg-gray-50 border border-gray-100 p-4 rounded-xl shadow-sm space-y-3">
                            <div className="grid grid-cols-1 md:grid-cols-12 gap-3 relative">
                               <div className="md:col-span-2">
                                  <label className={labelClass}>Categoria</label>
                                  <select value={mat.categoria} onChange={(e) => updateMaterial(nIndex, mIndex, 'categoria', e.target.value)} className={inputClass}>
                                    <option value="ENTORPECENTE">Entorpecente</option><option value="DINHEIRO">Dinheiro</option><option value="SOM">Som</option><option value="FACA">Arma Branca</option><option value="SIMULACRO">Simulacro</option><option value="OUTROS">Outros</option>
                                  </select>
                               </div>
                               {mat.categoria === 'ENTORPECENTE' ? (
                                 <><div className="md:col-span-3">
                                     <label className={labelClass}>Substância *</label>
                                     <select required value={mat.substancia} onChange={(e) => updateMaterial(nIndex, mIndex, 'substancia', e.target.value)} className={inputClass}>
                                       <option value="">Selecione...</option>{DROGAS_LISTA.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
                                     </select>
                                   </div>
                                   <div className="md:col-span-2"><label className={labelClass}>Qtd.</label><input type="number" step="0.001" value={mat.peso_estimado} onChange={(e) => updateMaterial(nIndex, mIndex, 'peso_estimado', e.target.value)} className={inputClass} /></div>
                                   <div className="md:col-span-2"><label className={labelClass}>Unidade</label><select value={mat.unidade} onChange={(e) => updateMaterial(nIndex, mIndex, 'unidade', e.target.value)} className={inputClass}><option value="G">g</option><option value="KG">kg</option><option value="UN">un</option></select></div>
                                 </>
                               ) : (<div className="md:col-span-7"><label className={labelClass}>Descrição *</label><input required value={mat.descricao_geral} onChange={(e) => updateMaterial(nIndex, mIndex, 'descricao_geral', e.target.value)} className={inputClass} /></div>)}
                               <div className="md:col-span-2"><label className={labelClass}>Lacre</label><input value={mat.numero_lacre} onChange={(e) => updateMaterial(nIndex, mIndex, 'numero_lacre', e.target.value)} className={inputClass} /></div>
                               <div className="md:col-span-1 flex items-end justify-center"><button type="button" onClick={() => removeMaterial(nIndex, mIndex)} className="text-red-300 hover:text-red-500 mb-2"><Trash2 size={16}/></button></div>
                            </div>
                             <div className="pt-2 border-t border-gray-100">
                                <label className={labelClass}>Observação do Item (ex: detalhes de conservação, acessórios, etc.)</label>
                                <input value={mat.observacao_material || ''} onChange={(e) => updateMaterial(nIndex, mIndex, 'observacao_material', e.target.value)} className={inputClass + " border-dashed"} placeholder="..." />
                             </div>
                           </div>
                         ))}
                       </div>
                      <div className="pt-3 border-t border-gray-200">
                         <label className={labelClass}>Observação do Noticiado (opcional)</label>
                         <textarea 
                           value={noticiado.observacao || ''} 
                           onChange={(e) => updateNoticiado(nIndex, 'observacao', e.target.value)} 
                           className={inputClass + " border-dashed resize-none"} 
                           rows="2"
                           placeholder="Observações adicionais sobre o noticiado..."
                         />
                      </div>
                    </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="bg-gray-50 p-6 rounded-xl border border-gray-200">
          <h2 className="text-xl font-bold text-gray-700 flex items-center gap-2 mb-4"><Search size={20} /> 3. Equipe Policial</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
             <div className="md:col-span-1"><label className={labelClass}>Graduação</label><select name="policial_graduacao" value={formData.policial_graduacao} onChange={handleChange} className={inputClass}>{['SD','CB','3SGT','2SGT','1SGT','SUB','2TEN','1TEN','CAP','MAJ'].map(g => <option key={g} value={g}>{g}</option>)}</select></div>
             <div className="md:col-span-2"><label className={labelClass}>Nome *</label><input name="policial_nome" value={formData.policial_nome} onChange={handleChange} className={inputClass + " uppercase"} required /></div>
             <div className="md:col-span-1"><label className={labelClass}>RG</label><input name="rg_policial" value={formData.rg_policial} onChange={handleChange} className={inputClass} /></div>
          </div>
        </section>

        <button disabled={loading} type="submit" className="w-full bg-pmpr-green text-white font-bold py-5 rounded-2xl shadow-xl hover:opacity-90 transition flex justify-center items-center gap-4 text-xl border-b-4 border-yellow-600 uppercase">
          <Save size={28} className={loading && "animate-spin"} /> {loading ? 'PROCESSANDO...' : (id ? 'SALVAR' : 'FINALIZAR')}
        </button>
      </form>
    </div>
  );
}
