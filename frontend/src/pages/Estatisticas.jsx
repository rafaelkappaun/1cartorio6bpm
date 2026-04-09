import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Filter, Calendar, ChevronDown, ChevronUp, X, Download,
  ShieldAlert, Scale, Flame, Package, Truck, DollarSign,
  BarChart3, PieChart as PieChartIcon, TrendingUp, Users, MapPin,
  FileText, Gavel, Hash, User, Building, RefreshCw, SlidersHorizontal,
  Printer, FileBarChart, Shield, PackageX, UsersRound, FlameKindling
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
  LineChart, Line, Area, AreaChart
} from 'recharts';
import api from '../services/api';

const COLORS = [
  '#1a3a2a', '#c5a059', '#10b981', '#06b6d4', '#f59e0b',
  '#8b5cf6', '#ec4899', '#ef4444', '#6b7280', '#14b8a6',
  '#f97316', '#3b82f6', '#a855f7', '#78716c', '#84cc16'
];

const MESES = [
  '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white/95 backdrop-blur-md border border-gray-200 rounded-xl px-4 py-3 shadow-xl">
      <p className="font-bold text-gray-800 text-sm mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} className="text-sm" style={{ color: p.color }}>
          {p.name || 'Total'}: <span className="font-bold">{p.value}</span>
        </p>
      ))}
    </div>
  );
};

/* ========== COMPONENTES AUXILIARES ========== */

function FilterSelect({ label, icon: Icon, value, onChange, options, placeholder = 'Todos' }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[10px] font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
        {Icon && <Icon size={12} />}
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all appearance-none cursor-pointer hover:border-gray-300"
        style={{ backgroundImage: `url("data:image/svg+xml,%3csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' fill='%236b7280' viewBox='0 0 16 16'%3e%3cpath d='M4.646 5.646a.5.5 0 0 1 .708 0L8 8.293l2.646-2.647a.5.5 0 0 1 .708.708l-3 3a.5.5 0 0 1-.708 0l-3-3a.5.5 0 0 1 0-.708z'/%3e%3c/svg%3e")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right 0.5rem center', backgroundSize: '16px' }}
      >
        <option value="">{placeholder}</option>
        {options.map(opt => (
          <option key={opt.value} value={opt.value}>{opt.label}</option>
        ))}
      </select>
    </div>
  );
}

function FilterInput({ label, icon: Icon, value, onChange, placeholder, type = 'text' }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-[10px] font-bold uppercase tracking-wider text-gray-400 flex items-center gap-1.5">
        {Icon && <Icon size={12} />}
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full px-3 py-2.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-700 focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500 transition-all placeholder:text-gray-300 hover:border-gray-300"
      />
    </div>
  );
}

function StatMini({ title, value, icon: Icon, color = 'emerald', subtitle }) {
  const colorMap = {
    emerald: { bg: 'bg-emerald-50', text: 'text-emerald-600', border: 'border-emerald-500' },
    blue: { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-500' },
    amber: { bg: 'bg-amber-50', text: 'text-amber-600', border: 'border-amber-500' },
    red: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-500' },
    purple: { bg: 'bg-purple-50', text: 'text-purple-600', border: 'border-purple-500' },
    gray: { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-400' },
    cyan: { bg: 'bg-cyan-50', text: 'text-cyan-600', border: 'border-cyan-500' },
    orange: { bg: 'bg-orange-50', text: 'text-orange-600', border: 'border-orange-500' },
  };
  const c = colorMap[color] || colorMap.emerald;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`bg-white rounded-xl p-4 border-l-4 ${c.border} shadow-sm hover:shadow-md transition-shadow`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">{title}</p>
          <h3 className="text-2xl font-black text-gray-900 mt-1">{value}</h3>
          {subtitle && <p className="text-[10px] text-gray-400 mt-0.5">{subtitle}</p>}
        </div>
        <div className={`p-2.5 rounded-xl ${c.bg}`}>
          <Icon size={20} className={c.text} />
        </div>
      </div>
    </motion.div>
  );
}

function ActiveFilter({ label, onClear }) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      className="inline-flex items-center gap-1 bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full text-xs font-semibold border border-emerald-200"
    >
      {label}
      <button onClick={onClear} className="hover:bg-emerald-200 rounded-full p-0.5 transition">
        <X size={12} />
      </button>
    </motion.span>
  );
}

/* ========== COMPONENTE PRINCIPAL ========== */

export default function Estatisticas() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [showFilters, setShowFilters] = useState(true);
  const [materiais, setMateriais] = useState([]);
  const [showTable, setShowTable] = useState(false);

  // --- State dos Filtros ---
  const [filtros, setFiltros] = useState({
    categoria: '',
    substancia: '',
    status: '',
    vara: '',
    bou: '',
    processo: '',
    autor: '',
    natureza_penal: '',
    localizacao: '',
    palavra_chave: '',
    unidade_origem: '',
    ano: '',
    semestre: '',
    mes: '',
    data_inicio: '',
    data_fim: '',
  });

  const setFiltro = useCallback((key, value) => {
    setFiltros(prev => ({ ...prev, [key]: value }));
  }, []);

  const limparFiltros = useCallback(() => {
    setFiltros({
      categoria: '', substancia: '', status: '', vara: '',
      bou: '', processo: '', autor: '', natureza_penal: '',
      localizacao: '', palavra_chave: '', unidade_origem: '',
      ano: '', semestre: '', mes: '', data_inicio: '', data_fim: '',
    });
  }, []);

  // Conta filtros ativos
  const filtrosAtivos = useMemo(() => {
    return Object.entries(filtros).filter(([, v]) => v !== '');
  }, [filtros]);

  // Constrói query string
  const buildQueryString = useCallback(() => {
    const params = new URLSearchParams();
    Object.entries(filtros).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });
    return params.toString();
  }, [filtros]);

  // Carrega estatísticas
  const loadEstatisticas = useCallback(async () => {
    setLoading(true);
    try {
      const qs = buildQueryString();
      const [statsRes, matRes] = await Promise.all([
        api.get(`/materiais/estatisticas/?${qs}`),
        api.get(`/materiais/?${qs}`)
      ]);
      setData(statsRes.data);
      setMateriais(matRes.data.results || matRes.data);
    } catch (e) {
      console.error('Erro ao carregar estatísticas:', e);
    } finally {
      setLoading(false);
    }
  }, [buildQueryString]);

  // Função para imprimir relatório - abre URL do Django com filtros
  const handleImprimirRelatorio = (tipo) => {
    const params = new URLSearchParams();
    
    // Adiciona filtros do usuário (exceto categoria/status)
    Object.entries(filtros).forEach(([key, value]) => {
      if (value && key !== 'categoria' && key !== 'status') {
        params.append(key, value);
      }
    });
    
    let url = '/relatorio/gerencial/';
    
    // Filtros específicos por tipo de relatório
    switch (tipo) {
      case 'inventario':
        // Mostra tudo, usa filtros do usuário
        break;
      case 'entorpecentes':
        params.set('categoria', 'ENTORPECENTE');
        break;
      case 'objetos':
        params.set('categoria', 'SOM');
        break;
      case 'noticiados':
        // Relatório de noticiados - mostra todos
        break;
      case 'incineracao':
        // Usa rota específica de incineração
        url = '/relatorio/incineracao/';
        break;
      default:
        break;
    }
    
    const queryString = params.toString();
    window.open(url + (queryString ? '?' + queryString : ''), '_blank');
  };

  const formatPeso = (gramas) => {
    if (!gramas) return '0g';
    if (gramas >= 1000) return `${(gramas / 1000).toFixed(2).replace('.', ',')} kg`;
    return `${gramas.toFixed(1).replace('.', ',')} g`;
  };

  useEffect(() => {
    loadEstatisticas();
  }, [loadEstatisticas]);

  // Opções de filtro derivadas
  const opcoes = data?.opcoes_filtro || {
    categorias: [], substancias: [], status: [], varas: [], anos: []
  };

  const semestresOpcoes = [
    { value: '1', label: '1º Semestre (Jan-Jun)' },
    { value: '2', label: '2º Semestre (Jul-Dez)' },
  ];

  const mesesOpcoes = MESES.slice(1).map((m, i) => ({ value: String(i + 1), label: m }));

  const unidadesOpcoes = [
    { value: 'RPA', label: 'RPA' },
    { value: 'DEAEV', label: 'DEAEV' },
    { value: 'ROCAM', label: 'ROCAM' },
    { value: 'GOTRAN', label: 'GOTRAN' },
    { value: 'CAVALARIA', label: 'CAVALARIA' },
    { value: 'CHOQUE', label: 'CHOQUE' },
    { value: 'CHOQUE CANIL', label: 'CHOQUE CANIL' },
    { value: 'TRANSITO', label: 'TRANSITO' },
    { value: 'ROTAM', label: 'ROTAM' },
    { value: 'CPU', label: 'CPU' },
    { value: 'P2', label: 'P2' },
  ];

  // Formata labels para filtros ativos
  const getFilterLabel = (key, value) => {
    const labelMap = {
      categoria: () => opcoes.categorias?.find(c => c.value === value)?.label || value,
      substancia: () => opcoes.substancias?.find(s => s.value === value)?.label || value,
      status: () => opcoes.status?.find(s => s.value === value)?.label || value,
      vara: () => opcoes.varas?.find(v => v.value === value)?.label || value,
      ano: () => `Ano: ${value}`,
      semestre: () => `${value}º Semestre`,
      mes: () => `Mês: ${MESES[parseInt(value)] || value}`,
      data_inicio: () => `De: ${value}`,
      data_fim: () => `Até: ${value}`,
      bou: () => `BOU: ${value}`,
      processo: () => `Proc: ${value}`,
      autor: () => `Autor: ${value}`,
      natureza_penal: () => `Crime: ${value}`,
      localizacao: () => `Local: ${value}`,
      palavra_chave: () => `Busca: "${value}"`,
      unidade_origem: () => `Unidade: ${value}`,
    };
    return (labelMap[key] || (() => `${key}: ${value}`))();
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Header */}
      <header className="flex justify-between items-start flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-gradient-to-br from-pmpr-green to-emerald-800 shadow-lg">
            <BarChart3 size={28} className="text-white" />
          </div>
          <div>
            <h1 className="text-3xl font-black text-gray-900 tracking-tight">Estatísticas & Filtros</h1>
            <p className="text-gray-400 text-sm mt-0.5">Painel analítico avançado — 6º BPM Cascavel/PR</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
              showFilters
                ? 'bg-pmpr-green text-white shadow-md'
                : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
            }`}
          >
            <SlidersHorizontal size={16} />
            Filtros
            {filtrosAtivos.length > 0 && (
              <span className="bg-white/20 text-white px-1.5 py-0.5 rounded-md text-[10px] font-black">
                {filtrosAtivos.length}
              </span>
            )}
          </button>
          <button
            onClick={loadEstatisticas}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-gray-200 text-gray-600 text-sm font-semibold hover:bg-gray-50 transition-all"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Atualizar
          </button>
        </div>
      </header>

      {/* BOTÕES DE RELATÓRIOS - NOVO BLOCO */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
        <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
          <Printer size={16} className="text-pmpr-green" />
          IMPRIMIR RELATÓRIOS (baseado nos filtros aplicados)
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          <button
            onClick={() => handleImprimirRelatorio('inventario')}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-gray-50 hover:bg-gray-100 border border-gray-200 transition-all"
          >
            <FileBarChart size={24} className="text-gray-600" />
            <span className="text-xs font-semibold text-gray-700 text-center">Inventário Geral</span>
          </button>
          <button
            onClick={() => handleImprimirRelatorio('entorpecentes')}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-red-50 hover:bg-red-100 border border-red-200 transition-all"
          >
            <Shield size={24} className="text-red-600" />
            <span className="text-xs font-semibold text-red-700 text-center">Entorpecentes</span>
          </button>
          <button
            onClick={() => handleImprimirRelatorio('objetos')}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-blue-50 hover:bg-blue-100 border border-blue-200 transition-all"
          >
            <PackageX size={24} className="text-blue-600" />
            <span className="text-xs font-semibold text-blue-700 text-center">Objetos Diversos</span>
          </button>
          <button
            onClick={() => handleImprimirRelatorio('noticiados')}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-purple-50 hover:bg-purple-100 border border-purple-200 transition-all"
          >
            <UsersRound size={24} className="text-purple-600" />
            <span className="text-xs font-semibold text-purple-700 text-center">Noticiados</span>
          </button>
          <button
            onClick={() => handleImprimirRelatorio('incineracao')}
            className="flex flex-col items-center gap-2 p-4 rounded-xl bg-orange-50 hover:bg-orange-100 border border-orange-200 transition-all"
          >
            <FlameKindling size={24} className="text-orange-600" />
            <span className="text-xs font-semibold text-orange-700 text-center">Incineração</span>
          </button>
        </div>
        {filtrosAtivos.length > 0 && (
          <p className="text-xs text-gray-500 mt-3">
            <span className="font-semibold">{filtrosAtivos.length} filtro(s)</span> aplicados — os relatórios acima refletirão esses filtros.
          </p>
        )}
      </div>

      {/* Painel de Filtros */}
      <AnimatePresence>
        {showFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
              <div className="flex items-center justify-between mb-5">
                <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                  <Filter size={16} className="text-pmpr-green" />
                  Painel de Filtros Avançados
                </h3>
                {filtrosAtivos.length > 0 && (
                  <button onClick={limparFiltros} className="text-xs text-red-500 hover:text-red-700 font-semibold flex items-center gap-1 transition">
                    <X size={14} /> Limpar todos
                  </button>
                )}
              </div>

              {/* LINHA 1 - Período Temporal */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4 mb-4">
                <FilterSelect
                  label="Ano" icon={Calendar}
                  value={filtros.ano}
                  onChange={(v) => setFiltro('ano', v)}
                  options={(opcoes.anos || []).map(a => ({ value: String(a), label: String(a) }))}
                />
                <FilterSelect
                  label="Semestre" icon={Calendar}
                  value={filtros.semestre}
                  onChange={(v) => setFiltro('semestre', v)}
                  options={semestresOpcoes}
                />
                <FilterSelect
                  label="Mês" icon={Calendar}
                  value={filtros.mes}
                  onChange={(v) => setFiltro('mes', v)}
                  options={mesesOpcoes}
                />
                <FilterInput
                  label="Data Inicial" icon={Calendar}
                  value={filtros.data_inicio}
                  onChange={(v) => setFiltro('data_inicio', v)}
                  type="date"
                />
                <FilterInput
                  label="Data Final" icon={Calendar}
                  value={filtros.data_fim}
                  onChange={(v) => setFiltro('data_fim', v)}
                  type="date"
                />
              </div>

              {/* LINHA 2 - Natureza e Tipo */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-4">
                <FilterSelect
                  label="Categoria" icon={Package}
                  value={filtros.categoria}
                  onChange={(v) => setFiltro('categoria', v)}
                  options={opcoes.categorias || []}
                />
                <FilterSelect
                  label="Substância" icon={ShieldAlert}
                  value={filtros.substancia}
                  onChange={(v) => setFiltro('substancia', v)}
                  options={opcoes.substancias || []}
                />
                <FilterSelect
                  label="Status Atual" icon={MapPin}
                  value={filtros.status}
                  onChange={(v) => setFiltro('status', v)}
                  options={opcoes.status || []}
                />
                <FilterInput
                  label="Localização (Cofre)" icon={MapPin}
                  value={filtros.localizacao}
                  onChange={(v) => setFiltro('localizacao', v)}
                  placeholder="Ex: Armário 1"
                />
              </div>

              {/* LINHA 3 - Judicial */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mb-4">
                <FilterSelect
                  label="Vara Judicial" icon={Gavel}
                  value={filtros.vara}
                  onChange={(v) => setFiltro('vara', v)}
                  options={opcoes.varas || []}
                />
                <FilterInput
                  label="Nº Processo (PROJUDI)" icon={Hash}
                  value={filtros.processo}
                  onChange={(v) => setFiltro('processo', v)}
                  placeholder="Ex: 0001234-56..."
                />
                <FilterInput
                  label="Nº BOU" icon={FileText}
                  value={filtros.bou}
                  onChange={(v) => setFiltro('bou', v)}
                  placeholder="Ex: 2026/000123"
                />
                <FilterInput
                  label="Nome do Autor / Réu" icon={User}
                  value={filtros.autor}
                  onChange={(v) => setFiltro('autor', v)}
                  placeholder="Ex: JOÃO SILVA"
                />
              </div>

              {/* LINHA 4 - Extras */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
                <FilterInput
                  label="Crime / Natureza Penal" icon={ShieldAlert}
                  value={filtros.natureza_penal}
                  onChange={(v) => setFiltro('natureza_penal', v)}
                  placeholder="Ex: Tráfico, Furto, Perturbação..."
                />
                <FilterSelect
                  label="Unidade PM Origem" icon={Building}
                  value={filtros.unidade_origem}
                  onChange={(v) => setFiltro('unidade_origem', v)}
                  options={unidadesOpcoes}
                />
                <div className="sm:col-span-2">
                  <FilterInput
                    label="Busca por Palavra-Chave" icon={Search}
                    value={filtros.palavra_chave}
                    onChange={(v) => setFiltro('palavra_chave', v)}
                    placeholder="Busca livre em BOU, processo, nome, lacre, descrição..."
                  />
                </div>
              </div>

              {/* Filtros Ativos (Tags) */}
              {filtrosAtivos.length > 0 && (
                <div className="mt-5 pt-4 border-t border-gray-100">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-gray-400 mb-2">
                    Filtros Ativos ({filtrosAtivos.length})
                  </p>
                  <div className="flex flex-wrap gap-2">
                    <AnimatePresence>
                      {filtrosAtivos.map(([key, value]) => (
                        <ActiveFilter
                          key={key}
                          label={getFilterLabel(key, value)}
                          onClear={() => setFiltro(key, '')}
                        />
                      ))}
                    </AnimatePresence>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Loading */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <RefreshCw size={32} className="text-pmpr-green animate-spin" />
          <p className="text-gray-400 font-medium">Processando filtros...</p>
        </div>
      ) : data ? (
        <>
          {/* Cards Resumo */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatMini
              title="Total de Itens" value={data.total}
              icon={Package} color="emerald"
              subtitle={`${data.resumo.bous_unicos} BOUs distintos`}
            />
            <StatMini
              title="Entorpecentes" value={data.resumo.entorpecentes}
              icon={ShieldAlert} color="red"
              subtitle={formatPeso(data.resumo.peso_total_gramas)}
            />
            <StatMini
              title="Materiais Gerais" value={data.resumo.materiais_gerais}
              icon={Truck} color="blue"
            />
            <StatMini
              title="Dinheiro/Valores" value={data.resumo.dinheiro}
              icon={DollarSign} color="amber"
            />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatMini
              title="No Cofre" value={data.resumo.no_cofre}
              icon={Scale} color="cyan"
            />
            <StatMini
              title="Incinerados" value={data.resumo.incinerados}
              icon={Flame} color="orange"
            />
            <StatMini
              title="Entregues ao Judiciário" value={data.resumo.entregues_judiciario}
              icon={Gavel} color="purple"
            />
            <StatMini
              title="BOUs Distintos" value={data.resumo.bous_unicos}
              icon={FileText} color="gray"
            />
          </div>

          {/* Gráficos */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Por Categoria */}
            {data.por_categoria?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-sm font-bold text-gray-800 mb-5 flex items-center gap-2">
                  <Package size={16} className="text-pmpr-green" />
                  Distribuição por Categoria
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={data.por_categoria.map(c => ({ name: c.label, value: c.total }))}
                      cx="50%" cy="50%"
                      innerRadius={55} outerRadius={95}
                      paddingAngle={4} dataKey="value"
                      stroke="none"
                    >
                      {data.por_categoria.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend verticalAlign="bottom" height={40} iconType="circle"
                      formatter={(v) => <span className="text-xs text-gray-600 font-medium">{v}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Por Status */}
            {data.por_status?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-sm font-bold text-gray-800 mb-5 flex items-center gap-2">
                  <MapPin size={16} className="text-pmpr-green" />
                  Distribuição por Status
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={data.por_status.map(s => ({ name: s.label?.substring(0, 20) + (s.label?.length > 20 ? '...' : ''), total: s.total, fullLabel: s.label }))} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
                    <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="name" width={160} axisLine={false} tickLine={false} tick={{ fontSize: 10, fontWeight: 500 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="total" fill="#1a3a2a" radius={[0, 6, 6, 0]} barSize={22} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Por Substância */}
            {data.por_substancia?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-sm font-bold text-gray-800 mb-5 flex items-center gap-2">
                  <ShieldAlert size={16} className="text-red-500" />
                  Apreensões por Substância
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={data.por_substancia.map(s => ({ name: s.label, total: s.total }))}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 9, fontWeight: 600 }} axisLine={false} tickLine={false} angle={-25} textAnchor="end" height={60} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="total" radius={[6, 6, 0, 0]} barSize={36}>
                      {data.por_substancia.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Por Vara */}
            {data.por_vara?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-sm font-bold text-gray-800 mb-5 flex items-center gap-2">
                  <Gavel size={16} className="text-amber-600" />
                  Distribuição por Vara Judicial
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie
                      data={data.por_vara.map(v => ({ name: v.label, value: v.total }))}
                      cx="50%" cy="50%"
                      innerRadius={55} outerRadius={95}
                      paddingAngle={4} dataKey="value"
                      stroke="none"
                    >
                      {data.por_vara.map((_, i) => (
                        <Cell key={i} fill={COLORS[(i + 3) % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend verticalAlign="bottom" height={40} iconType="circle"
                      formatter={(v) => <span className="text-xs text-gray-600 font-medium">{v}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Evolução Mensal */}
            {data.por_mes?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100 lg:col-span-2">
                <h3 className="text-sm font-bold text-gray-800 mb-5 flex items-center gap-2">
                  <TrendingUp size={16} className="text-blue-500" />
                  Evolução Mensal de Registros
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={data.por_mes.map(m => ({ name: m.mes_label, total: m.total }))}>
                    <defs>
                      <linearGradient id="gradientArea" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#1a3a2a" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#1a3a2a" stopOpacity={0.02} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 11, fontWeight: 500 }} axisLine={false} tickLine={false} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Area type="monotone" dataKey="total" stroke="#1a3a2a" strokeWidth={2.5} fill="url(#gradientArea)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Top Autores */}
            {data.top_autores?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-sm font-bold text-gray-800 mb-5 flex items-center gap-2">
                  <Users size={16} className="text-purple-500" />
                  Top Autores / Réus ({data.top_autores.length})
                </h3>
                <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                  {data.top_autores.map((a, i) => (
                    <div key={i} className="flex items-center justify-between px-3 py-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                      <div className="flex items-center gap-2.5">
                        <span className="w-6 h-6 rounded-full bg-pmpr-green text-white text-[10px] font-bold flex items-center justify-center">
                          {i + 1}
                        </span>
                        <span className="text-sm text-gray-700 font-medium truncate max-w-[200px]">
                          {a.nome || 'N/I'}
                        </span>
                      </div>
                      <span className="text-sm font-bold text-pmpr-green">{a.total}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Por Unidade PM */}
            {data.por_unidade?.length > 0 && (
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 className="text-sm font-bold text-gray-800 mb-5 flex items-center gap-2">
                  <Building size={16} className="text-cyan-600" />
                  Apreensões por Unidade PM
                </h3>
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={data.por_unidade.map(u => ({ name: u.unidade || 'N/I', total: u.total }))}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 10, fontWeight: 600 }} axisLine={false} tickLine={false} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11 }} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="total" fill="#c5a059" radius={[6, 6, 0, 0]} barSize={36} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Tabela de Resultados */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            <button
              onClick={() => setShowTable(!showTable)}
              className="w-full flex items-center justify-between px-6 py-4 hover:bg-gray-50 transition"
            >
              <h3 className="text-sm font-bold text-gray-800 flex items-center gap-2">
                <FileText size={16} className="text-pmpr-green" />
                Registros Detalhados ({materiais.length} itens)
              </h3>
              {showTable ? <ChevronUp size={18} className="text-gray-400" /> : <ChevronDown size={18} className="text-gray-400" />}
            </button>

            <AnimatePresence>
              {showTable && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 sticky top-0 z-10">
                        <tr>
                          <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-gray-500">BOU</th>
                          <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-gray-500">Processo</th>
                          <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-gray-500">Categoria</th>
                          <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-gray-500">Substância/Descrição</th>
                          <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-gray-500">Lacre</th>
                          <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-gray-500">Status</th>
                          <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-gray-500">Responsável</th>
                          <th className="px-4 py-3 text-left text-[10px] font-bold uppercase tracking-wider text-gray-500">Data</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-50">
                        {materiais.map(m => (
                          <tr key={m.id} className="hover:bg-emerald-50/40 transition-colors">
                            <td className="px-4 py-3 font-semibold text-emerald-700">{m.bou || '-'}</td>
                            <td className="px-4 py-3 text-gray-500 font-mono text-xs">{m.processo || '-'}</td>
                            <td className="px-4 py-3">
                              <span className="px-2 py-0.5 rounded-md text-[10px] font-bold bg-gray-100 text-gray-700">
                                {m.categoria}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-gray-700 max-w-[200px] truncate">
                              {m.descricao_amigavel || m.substancia?.replace('_', ' ') || m.descricao_geral || '-'}
                            </td>
                            <td className="px-4 py-3 font-mono text-xs text-gray-500">{m.numero_lacre || '-'}</td>
                            <td className="px-4 py-3">
                              <StatusBadge status={m.status} />
                            </td>
                            <td className="px-4 py-3 text-gray-600 font-medium whitespace-nowrap">
                              <span className="flex items-center gap-1.5">
                                <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 text-[9px] flex items-center justify-center font-black">
                                  {m.criado_por_nome?.substring(0, 2).toUpperCase() || 'S'}
                                </span>
                                {m.criado_por_nome || 'Sistema'}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-gray-400 text-xs">
                              {m.data_criacao ? new Date(m.data_criacao).toLocaleDateString('pt-BR') : '-'}
                            </td>
                          </tr>
                        ))}
                        {materiais.length === 0 && (
                          <tr>
                            <td colSpan="8" className="px-6 py-12 text-center text-gray-400">
                              Nenhum registro encontrado para os filtros aplicados.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </>
      ) : (
        <div className="text-center py-20 text-gray-400">Nenhum dado disponível.</div>
      )}
    </div>
  );
}

/* ===== STATUS BADGE ===== */
function StatusBadge({ status }) {
  const colorMap = {
    'RECEBIDO': 'bg-yellow-100 text-yellow-700',
    'CONSTATAÇÃO': 'bg-blue-100 text-blue-700',
    'ARMAZENADO': 'bg-emerald-100 text-emerald-700',
    'RETIRADO_PERICIA': 'bg-orange-100 text-orange-700',
    'RETORNO_PERICIA': 'bg-teal-100 text-teal-700',
    'AUTORIZADO': 'bg-indigo-100 text-indigo-700',
    'TRANSPORTE': 'bg-cyan-100 text-cyan-700',
    'INCINERADO': 'bg-gray-200 text-gray-600',
    'AGUARDANDO_OFICIO': 'bg-amber-100 text-amber-700',
    'OFICIO_GERADO': 'bg-sky-100 text-sky-700',
    'EM_TRANSPORTE_FORUM': 'bg-violet-100 text-violet-700',
    'ENTREGUE_AO_JUDICIARIO': 'bg-green-100 text-green-700',
    'AGUARDANDO_GUIA': 'bg-pink-100 text-pink-700',
    'GUIA_GERADA': 'bg-rose-100 text-rose-700',
    'DEPOSITADO_JUDICIALMENTE': 'bg-lime-100 text-lime-700',
  };

  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold whitespace-nowrap ${colorMap[status] || 'bg-gray-100 text-gray-500'}`}>
      {status?.replace(/_/g, ' ')}
    </span>
  );
}
