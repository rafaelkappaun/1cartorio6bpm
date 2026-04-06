import { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { Shield, ShieldAlert, Scale, Edit3, Layers, BarChart, History, Truck, SlidersHorizontal, LogOut, User, Menu, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import authService from '../services/auth';

const Sidebar = ({ user, onLogout }) => {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const navItems = [
    { name: 'Dashboard', path: '/', icon: <Shield size={20} /> },
    { name: 'Novo Cadastro', path: '/cadastro', icon: <Edit3 size={20} /> },
    { name: 'Conferir Cofre', path: '/conferencia', icon: <Scale size={20} /> },
    { name: 'Estoque Custódia', path: '/custodia', icon: <ShieldAlert size={20} /> },
    { name: 'Remessa ao Fórum', path: '/forum', icon: <Truck size={20} /> },
    { name: 'Lotes de Incineração', path: '/lotes', icon: <Layers size={20} /> },
    { name: 'Inventário', path: '/relatorios', icon: <BarChart size={20} /> },
    { name: 'Estatísticas & Filtros', path: '/estatisticas', icon: <SlidersHorizontal size={20} /> },
    { name: 'Auditoria', path: '/auditoria', icon: <History size={20} /> },
  ];

  return (
    <>
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-md"
      >
        {mobileOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="lg:hidden fixed inset-0 bg-black/50 z-40"
            onClick={() => setMobileOpen(false)}
          />
        )}
      </AnimatePresence>

      <aside className={`
        w-64 bg-white text-gray-800 flex flex-col h-screen fixed shadow-lg z-50
        transition-transform duration-300 lg:translate-x-0
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center gap-3">
            <img src="/img/brasao_pmpr.svg" alt="PMPR" className="w-10 h-10 object-contain drop-shadow-sm" />
            <div>
              <h1 className="text-sm font-black text-pmpr-green leading-tight">6º BATALHÃO</h1>
              <p className="text-[10px] text-gray-400 font-bold uppercase tracking-tighter">Polícia Militar do PR</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                  isActive 
                    ? 'bg-emerald-50 text-emerald-700 font-semibold border-l-4 border-emerald-500' 
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                {item.icon}
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-emerald-100 flex justify-center items-center font-bold text-emerald-600">
              <User size={16} />
            </div>
            <div className="text-sm flex-1 min-w-0">
              <p className="font-medium truncate">{user?.username || 'Usuário'}</p>
              <p className="text-xs text-gray-400">Escrivão</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition"
          >
            <LogOut size={16} />
            Sair
          </button>
        </div>
      </aside>
    </>
  );
};

export default function Layout() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);

  useEffect(() => {
    const storedUser = authService.getUser();
    if (storedUser) {
      setUser(storedUser);
    } else {
      const token = authService.getToken();
      if (token) {
        const payload = JSON.parse(atob(token.split('.')[1]));
        setUser({ username: payload.username || 'Usuário' });
        authService.setUser({ username: payload.username || 'Usuário' });
      }
    }
  }, []);

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar user={user} onLogout={handleLogout} />
      <motion.main 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex-1 lg:ml-64 p-4 lg:p-8 pt-16 lg:pt-8"
      >
        <Outlet />
      </motion.main>
    </div>
  );
}
