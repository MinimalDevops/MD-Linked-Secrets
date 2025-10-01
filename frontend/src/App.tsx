import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  CircularProgress,
  Alert,
  IconButton,
} from '@mui/material';
import { Lock as LockIcon } from '@mui/icons-material';
import { useAppStore } from './store';
import Dashboard from './components/Dashboard';
import Projects from './components/Projects';
import ProjectDetail from './components/ProjectDetail';
import Exports from './components/Exports';
import GlobalSearch from './components/GlobalSearch';

// Header component with navigation functionality
const AppHeader: React.FC = () => {
  const navigate = useNavigate();

  const handleHomeClick = () => {
    navigate('/');
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <IconButton
          edge="start"
          color="inherit"
          aria-label="home"
          onClick={handleHomeClick}
          sx={{ 
            mr: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            '&:hover': {
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
            }
          }}
        >
          <LockIcon />
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ 
              flexGrow: 1,
              cursor: 'pointer',
              userSelect: 'none'
            }}
          >
            MD-Linked-Secrets
          </Typography>
        </IconButton>
        <Box sx={{ flexGrow: 1 }} />
        <GlobalSearch />
      </Toolbar>
    </AppBar>
  );
};

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    h4: {
      fontWeight: 600,
    },
  },
});

function App() {
  const { loading, error, fetchProjects, fetchExports } = useAppStore();

  useEffect(() => {
    // Load initial data
    fetchProjects();
    fetchExports();
  }, [fetchProjects, fetchExports]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppHeader />

          <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {loading && (
              <Box display="flex" justifyContent="center" my={4}>
                <CircularProgress />
              </Box>
            )}

            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/projects" element={<Projects />} />
              <Route path="/projects/:id" element={<ProjectDetail />} />
              <Route path="/exports" element={<Exports />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
