import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Scale, Flame, Trash2, ShieldAlert, Package, Truck, Clock, TrendingUp, Filter, ChevronRight, Download, Calendar, PieChart as PieChartIcon, BarChart3 } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend, LineChart, Line } from 'recharts';
import api from '../services/api';

const COLORS = ['#10b981', '#06b6d4', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6366f1', '#14b8a6'];

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [periodo, setPeriodo] = useState(new Date().getFullYear());

  useEffect(() => {
    loadStats();
  }, [periodo]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const response = await api.get('/materiais/estatisticas/', { params: { ano: periodo } });
      setStats(response.data);
    } catch (e) {
      console.error('Erro ao carregar estatísticas:', e);
    } finally {
      setLoading(false);
    }
  };

  const formatarPeso = (gramas) => {
    if (!gramas) return '0 g';
    if (gramas >= 1000) return `${(gramas / 1000).toFixed(3).replace('.', ',')} kg`;
    return `${gramas.toFixed(3).replace('.', ',')} g`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-emerald-200 border-t-emerald-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-500 font-medium">Carregando painel estratégico...</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-8 text-center text-gray-500">
        Erro ao carregar dados. Verifique a conexão com o servidor.
      </div>
    );
  }

  const { resumo, por_categoria, por_substancia, por_status, por_mes, por_vara } = stats;

  return (
    <div className="space-y-6 pb-12">
      <header className="flex flex-col lg:flex-row lg:justify-between lg:items-start gap-4">
        <div className="flex items-center gap-4">
          <img src="/img/brasao_pmpr.svg" alt="PMPR" className="w-16 h-16 object-contain" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Painel Estratégico</h1>
            <p className="text-gray-500 font-medium">6º Batalhão de Polícia Militar - Cascavel/PR</p>
          </div>
        </div>
        <div className="flex items-center gap-3 bg-white p-2 rounded-xl shadow-sm border">
          <Calendar size={18} className="text-gray-400 ml-2" />
          <select
            value={periodo}
            onChange={(e) => setPeriodo(Number(e.target.value))}
            className="px-3 py-2 bg-transparent outline-none font-medium"
          >
            {[...Array(5)].map((_, i) => {
              const year = new Date().getFullYear() - i;
              return <option key={year} value={year}>{year}</option>;
            })}
          </select>
        </div>
      </header>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Itens" 
          value={resumo.entorpecentes + resumo.materiais_gerais} 
          subtitle={`${resumo.bous_unicos} BOU(s) único(s)`}
          icon={<Package size={22} className="text-emerald-600" />} 
          color="bg-white border-l-4 border-emerald-500" 
          onClick={() => navigate('/relatorios')}
        />
        <StatCard 
          title="No Cofre" 
          value={resumo.no_cofre} 
          subtitle={formatarPeso(resumo.peso_total_gramas)}
          icon={<Scale size={22} className="text-blue-600" />} 
          color="bg-white border-l-4 border-blue-500" 
          onClick={() => navigate('/custodia')}
        />
        <StatCard 
          title="Autorizados" 
          value={por_status.find(s => s.status === 'AUTORIZADO')?.total || 0} 
          icon={<Flame size={22} className="text-orange-600" />} 
          color="bg-white border-l-4 border-orange-500" 
          onClick={() => navigate('/lotes')}
        />
        <StatCard 
          title="Incinerados" 
          value={resumo.incinerados} 
          icon={<Trash2 size={22} className="text-gray-600" />} 
          color="bg-white border-l-4 border-gray-400" 
          onClick={() => navigate('/lotes')}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <PieChartIcon size={16} className="text-pmpr-green" />
            Por Categoria
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={por_categoria} dataKey="total" nameKey="label" cx="50%" cy="50%" outerRadius={80} label={({name, percent}) => `${name} (${(percent*100).toFixed(0)}%)`}>
                {por_categoria?.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-pmpr-green" />
            Por Substância
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={por_substancia?.slice(0, 6)} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
              <XAxis type="number" axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="label" width={80} axisLine={false} tickLine={false} tick={{fontSize: 11}} />
              <Tooltip cursor={{fill: '#f0fdf4'}} />
              <Bar dataKey="total" fill="#059669" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Filter size={16} className="text-pmpr-green" />
            Por Status
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={por_status}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="label" tick={{fontSize: 10}} axisLine={false} tickLine={false} />
              <YAxis axisLine={false} tickLine={false} />
              <Tooltip cursor={{fill: '#f0fdf4'}} />
              <Bar dataKey="total" radius={[4, 4, 0, 0]}>
                {por_status?.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <BarChart3 size={16} className="text-pmpr-green" />
            Evolução Mensal ({periodo})
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={por_mes}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="mes_label" tick={{fontSize: 10}} axisLine={false} tickLine={false} />
              <YAxis axisLine={false} tickLine={false} />
              <Tooltip />
              <Line type="monotone" dataKey="total" stroke="#059669" strokeWidth={3} dot={{fill: '#059669', strokeWidth: 2}} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <ShieldAlert size={16} className="text-pmpr-green" />
            Por Vara Criminal
          </h3>
          <div className="space-y-3 max-h-[250px] overflow-y-auto">
            {por_vara?.map((item, index) => (
              <div key={item.vara || index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">{item.label}</span>
                <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-bold">
                  {item.total}
                </span>
              </div>
            ))}
            {(!por_vara || por_vara.length === 0) && (
              <p className="text-center text-gray-400 py-4">Nenhum dado disponível</p>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <QuickAction 
          title="Novo Cadastro" 
          icon={<Package size={24} className="text-emerald-600" />}
          onClick={() => navigate('/cadastro')}
        />
        <QuickAction 
          title="Conferir Cofre" 
          icon={<Scale size={24} className="text-blue-600" />}
          onClick={() => navigate('/conferencia')}
        />
        <QuickAction 
          title="Remessa Fórum" 
          icon={<Truck size={24} className="text-orange-600" />}
          onClick={() => navigate('/forum')}
        />
        <QuickAction 
          title="Gerar Relatório" 
          icon={<Download size={24} className="text-purple-600" />}
          onClick={() => navigate('/relatorios')}
        />
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color, subtitle, onClick }) {
  return (
    <motion.div 
      whileHover={{ y: -4, shadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)' }} 
      onClick={onClick}
      className={`${color} rounded-xl p-5 flex items-center justify-between shadow-sm cursor-pointer transition-all hover:bg-gray-50 group`}
    >
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-xl bg-gray-50 group-hover:bg-white transition-colors">{icon}</div>
        <div>
          <p className="text-gray-400 text-[9px] font-black uppercase tracking-widest mb-1">{title}</p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-2xl font-black text-gray-900 leading-none">{value}</h3>
          </div>
          {subtitle && <p className="text-[10px] text-gray-500 font-medium mt-1">{subtitle}</p>}
        </div>
      </div>
      <ChevronRight size={16} className="text-gray-300 group-hover:text-emerald-600 group-hover:translate-x-1 transition-all" />
    </motion.div>
  );
}

function QuickAction({ title, icon, onClick }) {
  return (
    <motion.button
      whileHover={{ y: -2 }}
      onClick={onClick}
      className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex items-center gap-4 hover:shadow-md transition-all"
    >
      {icon}
      <span className="font-semibold text-gray-700">{title}</span>
    </motion.button>
  );
}
