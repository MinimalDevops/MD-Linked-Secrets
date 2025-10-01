import React, { useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  TextField,
  FormControl,
  Select,
  MenuItem,
  InputAdornment,
  Paper,
  List,
  ListItemButton,
  ListItemText,
  ListItemIcon,
  Chip,
  Typography,
  CircularProgress,
  Popper,
  Fade,
  ClickAwayListener,
} from '@mui/material';
import {
  Search as SearchIcon,
  Folder as ProjectIcon,
  Code as VariableIcon,
  Visibility as ValueIcon,
  TrendingUp as EverythingIcon,
} from '@mui/icons-material';
import { 
  apiClient, 
  SearchScope, 
  SearchResponse, 
  SearchResultType,
  ProjectSearchResult,
  VariableSearchResult,
  ValueSearchResult
} from '../api/client';
import { useAppStore } from '../store';

interface GlobalSearchProps {
  sx?: any;
}

const GlobalSearch: React.FC<GlobalSearchProps> = ({ sx }) => {
  const navigate = useNavigate();
  const { projects } = useAppStore();
  
  // State
  const [query, setQuery] = useState('');
  const [scope, setScope] = useState<SearchScope>('everything');
  const [projectId, setProjectId] = useState<number | null>(null);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  // Refs
  const searchRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<NodeJS.Timeout | undefined>(undefined);

  // Scope options
  const scopeOptions = [
    { value: 'everything', label: 'Everything', icon: <EverythingIcon /> },
    { value: 'projects', label: 'Projects', icon: <ProjectIcon /> },
    { value: 'env_vars', label: 'Env Vars', icon: <VariableIcon /> },
    { value: 'values', label: 'Values', icon: <ValueIcon /> },
  ];

  // Available projects for filtering
  const projectOptions = projects.map(p => ({ id: p.id, name: p.name }));

  // Debounced search
  const performSearch = useCallback(async (searchQuery: string) => {
    if (searchQuery.trim().length < 2) {
      setResults(null);
      setShowResults(false);
      return;
    }

    setLoading(true);
    try {
      const searchRequest = {
        query: searchQuery.trim(),
        scope,
        project_id: projectId || undefined,
        limit: 10
      };

      const response = await apiClient.globalSearch(searchRequest);
      setResults(response);
      setShowResults(true);
      setAnchorEl(searchRef.current);
    } catch (error) {
      console.error('Search error:', error);
      setResults(null);
      setShowResults(false);
    } finally {
      setLoading(false);
    }
  }, [scope, projectId]);

  // Handle query change with debouncing
  const handleQueryChange = (newQuery: string) => {
    setQuery(newQuery);
    
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      performSearch(newQuery);
    }, 300);
  };

  // Handle scope change
  const handleScopeChange = (newScope: SearchScope) => {
    setScope(newScope);
    if (query.trim().length >= 2) {
      performSearch(query);
    }
  };

  // Handle project filter change
  const handleProjectChange = (newProjectId: number | null) => {
    setProjectId(newProjectId);
    if (query.trim().length >= 2) {
      performSearch(query);
    }
  };

  // Handle result click
  const handleResultClick = (result: SearchResultType) => {
    setShowResults(false);
    setQuery('');

    if (result.type === 'project') {
      navigate(`/projects/${result.id}`);
    } else if (result.type === 'variable' || result.type === 'value') {
      // Navigate to project and highlight the variable
      navigate(`/projects/${result.project_id}?highlight=${result.id}`);
    }
  };

  // Handle click away
  const handleClickAway = () => {
    setShowResults(false);
  };

  // Render result icon
  const getResultIcon = (type: string) => {
    switch (type) {
      case 'project': return <ProjectIcon color="primary" />;
      case 'variable': return <VariableIcon color="secondary" />;
      case 'value': return <ValueIcon color="info" />;
      default: return <SearchIcon />;
    }
  };

  // Render result primary text
  const getResultPrimaryText = (result: SearchResultType) => {
    switch (result.type) {
      case 'project':
        return (result as ProjectSearchResult).name;
      case 'variable':
        return (result as VariableSearchResult).name;
      case 'value':
        return (result as ValueSearchResult).variable_name;
      default:
        return 'Unknown';
    }
  };

  // Render result secondary text
  const getResultSecondaryText = (result: SearchResultType) => {
    switch (result.type) {
      case 'project':
        const project = result as ProjectSearchResult;
        return `${project.variables_count} variables`;
      case 'variable':
        const variable = result as VariableSearchResult;
        return `${variable.project_name} • ${variable.value_type}`;
      case 'value':
        const value = result as ValueSearchResult;
        return `${value.project_name} • ${value.value_preview}`;
      default:
        return '';
    }
  };

  // Render highlight with bold matching text
  const renderHighlight = (highlight: string) => {
    const parts = highlight.split(/(\*\*.*?\*\*)/g);
    return (
      <span>
        {parts.map((part, index) => {
          if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={index}>{part.slice(2, -2)}</strong>;
          }
          return <span key={index}>{part}</span>;
        })}
      </span>
    );
  };

  return (
    <ClickAwayListener onClickAway={handleClickAway}>
      <Box sx={{ position: 'relative', ...sx }}>
        <Box display="flex" alignItems="center" gap={1}>
          {/* Search Input */}
          <TextField
            ref={searchRef}
            size="small"
            placeholder="Search projects, variables, values..."
            value={query}
            onChange={(e) => handleQueryChange(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  {loading ? (
                    <CircularProgress size={16} />
                  ) : (
                    <SearchIcon color="action" />
                  )}
                </InputAdornment>
              ),
            }}
            sx={{
              minWidth: 300,
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              '& .MuiOutlinedInput-root': {
                color: 'white',
                '& fieldset': {
                  borderColor: 'rgba(255, 255, 255, 0.3)',
                },
                '&:hover fieldset': {
                  borderColor: 'rgba(255, 255, 255, 0.5)',
                },
                '&.Mui-focused fieldset': {
                  borderColor: 'white',
                },
              },
              '& .MuiInputBase-input::placeholder': {
                color: 'rgba(255, 255, 255, 0.7)',
                opacity: 1,
              },
            }}
          />

          {/* Scope Selector */}
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <Select
              value={scope}
              onChange={(e) => handleScopeChange(e.target.value as SearchScope)}
              sx={{
                color: 'white',
                '& .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.3)',
                },
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'rgba(255, 255, 255, 0.5)',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'white',
                },
                '& .MuiSvgIcon-root': {
                  color: 'white',
                },
              }}
            >
              {scopeOptions.map((option) => (
                <MenuItem key={option.value} value={option.value}>
                  <Box display="flex" alignItems="center" gap={1}>
                    {option.icon}
                    {option.label}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Project Filter (for env_vars and values) */}
          {(scope === 'env_vars' || scope === 'values') && (
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <Select
                value={projectId || ''}
                onChange={(e) => handleProjectChange(e.target.value ? Number(e.target.value) : null)}
                displayEmpty
                sx={{
                  color: 'white',
                  '& .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.3)',
                  },
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'rgba(255, 255, 255, 0.5)',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'white',
                  },
                  '& .MuiSvgIcon-root': {
                    color: 'white',
                  },
                }}
              >
                <MenuItem value="">
                  <em>All Projects</em>
                </MenuItem>
                {projectOptions.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Box>

        {/* Search Results Dropdown */}
        <Popper
          open={showResults && Boolean(results)}
          anchorEl={anchorEl}
          placement="bottom-start"
          transition
          style={{ zIndex: 9999, width: anchorEl?.offsetWidth || 300 }}
        >
          {({ TransitionProps }) => (
            <Fade {...TransitionProps} timeout={200}>
              <Paper elevation={8} sx={{ maxHeight: 400, overflow: 'auto', mt: 1 }}>
                {results && (
                  <>
                    {/* Header */}
                    <Box p={2} borderBottom="1px solid #e0e0e0">
                      <Typography variant="subtitle2" color="text.secondary">
                        Found {results.total_results} results in {results.execution_time_ms}ms
                      </Typography>
                    </Box>

                    {/* Results List */}
                    <List dense>
                      {results.results.map((result) => (
                        <ListItemButton
                          key={`${result.type}-${result.id}`}
                          onClick={() => handleResultClick(result)}
                          sx={{
                            '&:hover': {
                              backgroundColor: 'action.hover',
                            },
                          }}
                        >
                          <ListItemIcon sx={{ minWidth: 40 }}>
                            {getResultIcon(result.type)}
                          </ListItemIcon>
                          
                          <ListItemText
                            primary={
                              <Box display="flex" alignItems="center" gap={1}>
                                <Typography variant="body2" fontWeight="medium">
                                  {getResultPrimaryText(result)}
                                </Typography>
                                <Chip
                                  size="small"
                                  label={result.type}
                                  color={
                                    result.type === 'project' ? 'primary' :
                                    result.type === 'variable' ? 'secondary' : 'info'
                                  }
                                  sx={{ fontSize: '0.7rem', height: 20 }}
                                />
                              </Box>
                            }
                            secondary={
                              <Box>
                                <Typography variant="caption" color="text.secondary">
                                  {getResultSecondaryText(result)}
                                </Typography>
                                <br />
                                <Typography variant="caption" color="text.disabled">
                                  {renderHighlight(result.highlight)}
                                </Typography>
                              </Box>
                            }
                          />
                        </ListItemButton>
                      ))}
                    </List>

                    {results.results.length === 0 && (
                      <Box p={3} textAlign="center">
                        <Typography variant="body2" color="text.secondary">
                          No results found for "{results.query}"
                        </Typography>
                      </Box>
                    )}
                  </>
                )}
              </Paper>
            </Fade>
          )}
        </Popper>
      </Box>
    </ClickAwayListener>
  );
};

export default GlobalSearch; 