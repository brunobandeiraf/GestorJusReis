import { Routes, Route, NavLink } from 'react-router-dom';
import { ProcessoProvider } from './context/ProcessoContext';
import Dashboard from './pages/Dashboard';
import ProcessoPage from './pages/ProcessoPage';
import ConsultaPage from './pages/ConsultaPage';
import BuscaCPFPage from './pages/BuscaCPFPage';

function App() {
  return (
    <ProcessoProvider>
      <div style={styles.app}>
        <header style={styles.header}>
          <h1 style={styles.brand}>Monitoramento Judicial</h1>
          <nav style={styles.nav}>
            <NavLink
              to="/"
              end
              style={({ isActive }) => ({
                ...styles.navLink,
                ...(isActive ? styles.navLinkActive : {}),
              })}
            >
              Dashboard
            </NavLink>
            <NavLink
              to="/consulta"
              style={({ isActive }) => ({
                ...styles.navLink,
                ...(isActive ? styles.navLinkActive : {}),
              })}
            >
              Consulta Avulsa
            </NavLink>
            <NavLink
              to="/busca-cpf"
              style={({ isActive }) => ({
                ...styles.navLink,
                ...(isActive ? styles.navLinkActive : {}),
              })}
            >
              Busca por CPF
            </NavLink>
          </nav>
        </header>

        <main style={styles.main}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/processo/:id" element={<ProcessoPage />} />
            <Route path="/consulta" element={<ConsultaPage />} />
            <Route path="/busca-cpf" element={<BuscaCPFPage />} />
          </Routes>
        </main>
      </div>
    </ProcessoProvider>
  );
}

const styles = {
  app: {
    minHeight: '100vh',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    color: '#212121',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '0.75rem 1.5rem',
    backgroundColor: '#1976d2',
    color: '#fff',
    flexWrap: 'wrap',
    gap: '0.5rem',
  },
  brand: {
    margin: 0,
    fontSize: '1.25rem',
    fontWeight: '600',
  },
  nav: {
    display: 'flex',
    gap: '1rem',
  },
  navLink: {
    color: 'rgba(255,255,255,0.8)',
    textDecoration: 'none',
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.9rem',
  },
  navLinkActive: {
    color: '#fff',
    backgroundColor: 'rgba(255,255,255,0.15)',
    fontWeight: '600',
  },
  main: {
    padding: '1rem',
  },
};

export default App;
