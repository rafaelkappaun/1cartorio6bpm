import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CadastroEntrada from './pages/CadastroEntrada';
import ConferenciaLista from './pages/ConferenciaLista';
import CustodiaLista from './pages/CustodiaLista';
import LotesIncinercao from './pages/LotesIncinercao';
import RelatorioGeral from './pages/RelatorioGeral';
import Auditoria from './pages/Auditoria';
import MateriaisGerais from './pages/MateriaisGerais';
import Estatisticas from './pages/Estatisticas';
import authService from './services/auth';

function ProtectedRoute({ children }) {
  if (!authService.isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function PublicRoute({ children }) {
  if (authService.isAuthenticated()) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={
          <PublicRoute><Login /></PublicRoute>
        } />
        
        <Route path="/" element={
          <ProtectedRoute><Layout /></ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="cadastro" element={<CadastroEntrada />} />
          <Route path="editar/:id" element={<CadastroEntrada />} />
          <Route path="conferencia" element={<ConferenciaLista />} />
          <Route path="custodia" element={<CustodiaLista />} />
          <Route path="forum" element={<MateriaisGerais />} />
          <Route path="lotes" element={<LotesIncinercao />} />
          <Route path="relatorios" element={<RelatorioGeral />} />
          <Route path="auditoria" element={<Auditoria />} />
          <Route path="estatisticas" element={<Estatisticas />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

