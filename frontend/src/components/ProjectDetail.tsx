import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  IconButton,
  Tooltip,
  Chip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormHelperText,
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  VisibilityOff as HideIcon,
  Analytics as AnalyticsIcon,
  CloudUpload as ImportIcon,
  History as HistoryIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material';
import { useAppStore } from '../store';
import { apiClient } from '../api/client';
import ImpactAnalysisDialog from './ImpactAnalysisDialog';
import ImportEnvDialog from './ImportEnvDialog';
import VariableHistoryDialog from './VariableHistoryDialog';
import ProjectHistorySettingsDialog from './ProjectHistorySettings';
import type { VariableImpactAnalysis } from '../api/client';

interface EnvironmentVariable {
  id: number;
  name: string;
  raw_value?: string;
  linked_to?: string;
  concat_parts?: string;
  description?: string;
  is_encrypted: boolean;
  created_at: string;
  updated_at: string;
}

const ProjectDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const highlightVar = searchParams.get('highlight');
  const { projects, loading, error, fetchProjects } = useAppStore();
  const [variables, setVariables] = useState<EnvironmentVariable[]>([]);
  const [showValues, setShowValues] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingVariableId, setEditingVariableId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    type: 'raw' as 'raw' | 'linked' | 'concatenated',
    raw_value: '',
    linked_to: '',
    concat_parts: '',
    description: '',
    is_encrypted: false,
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [deletionError, setDeletionError] = useState<string | null>(null);
  const [typeChangeWarning, setTypeChangeWarning] = useState<string | null>(null);
  
  // Impact Analysis Dialog
  const [impactDialogOpen, setImpactDialogOpen] = useState(false);
  const [impactAnalysisData, setImpactAnalysisData] = useState<VariableImpactAnalysis | null>(null);
  const [impactAnalysisLoading, setImpactAnalysisLoading] = useState(false);
  const [pendingEditVariableId, setPendingEditVariableId] = useState<number | null>(null);
  
  // Import Dialog
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  
  // History Dialogs
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [historySettingsOpen, setHistorySettingsOpen] = useState(false);
  const [selectedVariableId, setSelectedVariableId] = useState<number | null>(null);
  const [selectedVariableName, setSelectedVariableName] = useState<string>('');
  
  // Dropdown data
  const [availableProjects, setAvailableProjects] = useState<Array<{ id: number; name: string; description: string }>>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(null);
  const [availableVariables, setAvailableVariables] = useState<Array<{ id: number; name: string; description: string; value_type: string }>>([]);
  const [currentProjectVariables, setCurrentProjectVariables] = useState<Array<{ id: number; name: string; description: string; value_type: string }>>([]);

  const project = projects.find(p => p.id === Number(id));

  const loadDropdownData = useCallback(async () => {
    try {
      // Load available projects for linking (excluding current project)
      const projectsData = await fetch(`http://localhost:8088/api/v1/projects/dropdown/options?current_project_id=${id}`);
      if (projectsData.ok) {
        const projectsResult = await projectsData.json();
        setAvailableProjects(projectsResult.projects || []);
      }

      // Load current project variables for concatenation (all variables including linked and concatenated)
      const currentVarsData = await fetch(`http://localhost:8088/api/v1/env-vars/concatenation/options?project_id=${id}`);
      if (currentVarsData.ok) {
        const currentVarsResult = await currentVarsData.json();
        setCurrentProjectVariables(currentVarsResult.variables || []);
      }
    } catch (error) {
      console.error('Error loading dropdown data:', error);
    }
  }, [id]);

  useEffect(() => {
    if (!projects.length) {
      fetchProjects();
    }
    if (id) {
      fetchProjectVariables(Number(id));
      loadDropdownData();
    }
  }, [id, projects.length, fetchProjects, loadDropdownData]);



  const loadVariablesForProject = async (projectId: number) => {
    try {
      const response = await fetch(`http://localhost:8088/api/v1/env-vars/dropdown/options?project_id=${projectId}`);
      if (response.ok) {
        const result = await response.json();
        setAvailableVariables(result.variables || []);
      }
    } catch (error) {
      console.error('Error loading variables for project:', error);
    }
  };

  const fetchProjectVariables = async (projectId: number) => {
    try {
      const response = await fetch(`http://localhost:8088/api/v1/env-vars/?project_id=${projectId}`);
      if (response.ok) {
        const data = await response.json();
        setVariables(data.variables || []);
      }
    } catch (error) {
      console.error('Error fetching variables:', error);
    }
  };

  const handleBack = () => {
    navigate('/projects');
  };

  const handleAddVariable = () => {
    setDialogOpen(true);
    setEditingVariableId(null);
    setFormData({
      name: '',
      type: 'raw',
      raw_value: '',
      linked_to: '',
      concat_parts: '',
      description: '',
      is_encrypted: false,
    });
    setFormError(null);
    setTypeChangeWarning(null);
    setDeletionError(null); // Clear any deletion errors when opening dialog
  };

  const handleEditVariable = (variableId: number) => {
    const variable = variables.find(v => v.id === variableId);
    if (variable) {
      setEditingVariableId(variableId);
      setFormData({
        name: variable.name,
        type: variable.raw_value ? 'raw' : variable.linked_to ? 'linked' : 'concatenated',
        raw_value: variable.raw_value || '',
        linked_to: variable.linked_to || '',
        concat_parts: variable.concat_parts || '',
        description: variable.description || '',
        is_encrypted: variable.is_encrypted,
      });
      setDialogOpen(true);
      setFormError(null);
      setDeletionError(null); // Clear any deletion errors when opening dialog
    }
  };

  const handleDeleteVariable = async (variableId: number) => {
    if (window.confirm('Are you sure you want to delete this environment variable? This action cannot be undone.')) {
      try {
        setDeletionError(null); // Clear any previous deletion errors
        await apiClient.deleteEnvVar(variableId);
        setVariables(variables.filter(v => v.id !== variableId));
      } catch (error) {
        console.error('Error deleting variable:', error);
        // Show error in the same page instead of using alert
        setDeletionError(error instanceof Error ? error.message : 'Failed to delete variable');
      }
    }
  };

  const handleShowImpactAnalysis = async (variableId: number) => {
    try {
      setImpactAnalysisLoading(true);
      setImpactDialogOpen(true);
      setPendingEditVariableId(variableId);
      
      const impactData = await apiClient.getVariableImpactAnalysis(variableId);
      setImpactAnalysisData(impactData);
    } catch (error) {
      console.error('Error fetching impact analysis:', error);
      setDeletionError('Failed to load impact analysis');
      setImpactDialogOpen(false);
    } finally {
      setImpactAnalysisLoading(false);
    }
  };

  const handleProceedWithEdit = () => {
    if (pendingEditVariableId) {
      handleEditVariable(pendingEditVariableId);
      setPendingEditVariableId(null);
    }
    setImpactDialogOpen(false);
    setDialogOpen(true);
  };

  const handleUntrackExport = async (exportId: number) => {
    try {
      await apiClient.deleteExport(exportId);
      // Refresh impact analysis data to reflect the change
      if (pendingEditVariableId) {
        await handleShowImpactAnalysis(pendingEditVariableId);
      }
    } catch (error) {
      console.error('Failed to untrack export:', error);
      // You could add a toast notification here
    }
  };

  const handleImportComplete = () => {
    // Refresh the variables list after successful import
    if (id) {
      loadVariablesForProject(Number(id));
    }
  };

  const handleShowHistory = (variableId: number, variableName: string) => {
    setSelectedVariableId(variableId);
    setSelectedVariableName(variableName);
    setHistoryDialogOpen(true);
  };

  const handleCloseHistory = () => {
    setHistoryDialogOpen(false);
    setSelectedVariableId(null);
    setSelectedVariableName('');
  };

  const handleVariableUpdated = () => {
    // Refresh the variables list after restoration
    if (id) {
      loadVariablesForProject(Number(id));
    }
  };

  const handleOpenHistorySettings = () => {
    setHistorySettingsOpen(true);
  };

  const handleCloseHistorySettings = () => {
    setHistorySettingsOpen(false);
  };

  const handleCloseImpactDialog = () => {
    setImpactDialogOpen(false);
    setImpactAnalysisData(null);
    setPendingEditVariableId(null);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setEditingVariableId(null);
    setFormData({
      name: '',
      type: 'raw',
      raw_value: '',
      linked_to: '',
      concat_parts: '',
      description: '',
      is_encrypted: false,
    });
    setFormError(null);
    setTypeChangeWarning(null);
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      setFormError('Variable name is required');
      return;
    }

    // Validate variable name format
    const name = formData.name.trim();
    if (name.includes(' ')) {
      setFormError('Variable name cannot contain spaces');
      return;
    }
    if (!/^[A-Za-z0-9_]+$/.test(name)) {
      setFormError('Variable name can only contain letters, numbers, and underscores');
      return;
    }
    if (name.startsWith('_') || name.endsWith('_')) {
      setFormError('Variable name cannot start or end with underscore');
      return;
    }
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(name)) {
      setFormError('Variable name must start with a letter or underscore');
      return;
    }

    // Validate based on type
    if (formData.type === 'raw' && !formData.raw_value.trim()) {
      setFormError('Raw value is required for raw type variables');
      return;
    }
    if (formData.type === 'linked' && !formData.linked_to.trim()) {
      setFormError('Linked reference is required for linked type variables');
      return;
    }
    if (formData.type === 'concatenated' && !formData.concat_parts.trim()) {
      setFormError('Concatenation parts are required for concatenated type variables');
      return;
    }

    try {
      const variableData = {
        project_id: Number(id),
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        is_encrypted: formData.is_encrypted,
        ...(formData.type === 'raw' && { raw_value: formData.raw_value.trim() }),
        ...(formData.type === 'linked' && { linked_to: formData.linked_to.trim() }),
        ...(formData.type === 'concatenated' && { concat_parts: formData.concat_parts.trim() }),
      };

      let newVariable: EnvironmentVariable;
      
      if (editingVariableId) {
        // Check if we're changing the variable type
        const originalVariable = variables.find(v => v.id === editingVariableId);
        const originalType = originalVariable?.raw_value ? 'raw' : originalVariable?.linked_to ? 'linked' : 'concatenated';
        const newType = formData.type;
        
        if (originalType !== newType) {
          // Type is changing, use the change-type endpoint
          const result = await apiClient.changeVariableType(editingVariableId, variableData);
          newVariable = {
            id: result.id,
            name: result.name,
            raw_value: result.raw_value,
            linked_to: result.linked_to,
            concat_parts: result.concat_parts,
            description: result.description,
            is_encrypted: false, // Default value since API doesn't return this
            created_at: result.created_at,
            updated_at: result.updated_at,
          };
        } else {
          // Type is not changing, use regular update
          const result = await apiClient.updateEnvVar(editingVariableId, variableData);
          newVariable = {
            id: result.id,
            name: result.name,
            raw_value: result.raw_value,
            linked_to: result.linked_to,
            concat_parts: result.concat_parts,
            description: result.description,
            is_encrypted: false, // Default value since API doesn't return this
            created_at: result.created_at,
            updated_at: result.updated_at,
          };
        }
      } else {
        // Creating new variable
        const result = await apiClient.createEnvVar({
          ...variableData,
          value_type: formData.type as 'raw' | 'linked' | 'concatenated',
          description: variableData.description || '', // Ensure description is not undefined
        });
        newVariable = {
          id: result.id,
          name: result.name,
          raw_value: result.raw_value,
          linked_to: result.linked_to,
          concat_parts: result.concat_parts,
          description: result.description,
          is_encrypted: false, // Default value since API doesn't return this
          created_at: result.created_at,
          updated_at: result.updated_at,
        };
      }

      if (editingVariableId) {
        setVariables(variables.map(v => v.id === editingVariableId ? newVariable : v));
      } else {
        setVariables([...variables, newVariable]);
      }
      handleCloseDialog();
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Failed to save variable');
    }
  };

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement> | { target: { value: unknown } }) => {
    setFormData(prev => ({ ...prev, [field]: event.target.value }));
    if (formError) setFormError(null);
    
    // Check for type changes when editing
    if (editingVariableId && field === 'type') {
      const originalVariable = variables.find(v => v.id === editingVariableId);
      if (originalVariable) {
        const originalType = originalVariable.raw_value ? 'raw' : originalVariable.linked_to ? 'linked' : 'concatenated';
        const newType = event.target.value as string;
        
        if (originalType !== newType) {
          setTypeChangeWarning(`Warning: You are changing this variable from ${originalType} to ${newType} type. This will delete the current variable and create a new one.`);
        } else {
          setTypeChangeWarning(null);
        }
      }
    }
  };

  const getVariableType = (variable: EnvironmentVariable) => {
    if (variable.raw_value) return 'Raw Value';
    if (variable.linked_to) return 'Linked';
    if (variable.concat_parts) return 'Concatenated';
    return 'Unknown';
  };

  const [resolvedValues, setResolvedValues] = useState<Record<string, string>>({});

  // Load resolved values for linked and concatenated variables
  useEffect(() => {
    const loadResolvedValues = async () => {
      const variablesNeedingResolution = variables.filter(v => v.linked_to || v.concat_parts);
      if (variablesNeedingResolution.length === 0) return;

      try {
        const response = await fetch(`http://localhost:8088/api/v1/env-vars/resolve`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_id: Number(id) })
        });
        
        if (response.ok) {
          const data = await response.json();
          // Use the resolved values directly - the API returns variable names as keys
          setResolvedValues(data.resolved_values || {});
        }
      } catch (error) {
        console.error('Error loading resolved values:', error);
      }
    };

    if (variables.length > 0) {
      loadResolvedValues();
    }
  }, [variables, id]);

  const handleLinkedVariableClick = (linkedTo: string) => {
    const [projectName, varName] = linkedTo.split(':');
    // Find the project by name
    const targetProject = projects.find(p => p.name === projectName);
    if (targetProject) {
      // Navigate to the target project with a highlight parameter
      navigate(`/projects/${targetProject.id}?highlight=${varName}`);
    }
  };

  const getVariableDisplayValue = (variable: EnvironmentVariable) => {
    if (variable.raw_value) {
      return showValues ? variable.raw_value : '••••••••';
    }
    if (variable.linked_to) {
      const resolvedValue = resolvedValues[variable.name]; // Use variable name as key
      
      return (
        <Box
          component="span"
          sx={{
            cursor: 'pointer',
            color: 'primary.main',
            textDecoration: 'underline',
            '&:hover': {
              color: 'primary.dark',
            }
          }}
          onClick={() => handleLinkedVariableClick(variable.linked_to!)}
        >
          <Box component="div" sx={{ color: showValues ? 'text.secondary' : 'primary.main' }}>
            → {variable.linked_to}
          </Box>
          {showValues && resolvedValue && (
            <Box component="div" sx={{ color: 'text.primary', fontWeight: 'normal', mt: 0.5 }}>
              {resolvedValue}
            </Box>
          )}
        </Box>
      );
    }
    if (variable.concat_parts) {
      const resolvedValue = resolvedValues[variable.name]; // Use variable name as key
      
      return (
        <Box>
          <Box component="div" sx={{ color: showValues ? 'text.secondary' : 'text.primary' }}>
            ⊕ {variable.concat_parts}
          </Box>
          {showValues && resolvedValue && (
            <Box component="div" sx={{ color: 'text.primary', fontWeight: 'normal', mt: 0.5 }}>
              {resolvedValue}
            </Box>
          )}
        </Box>
      );
    }
    return 'No value';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" my={4}>
        <Typography>Loading project details...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box my={4}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  if (!project) {
    return (
      <Box my={4}>
        <Alert severity="warning">Project not found</Alert>
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" alignItems="center" mb={3}>
        <IconButton onClick={handleBack} sx={{ mr: 2 }}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          {project.name}
        </Typography>
      </Box>

      <Box display="grid" gridTemplateColumns="1fr 2fr" gap={3}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Project Information
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              {project.description || 'No description available'}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Created:</strong> {new Date(project.created_at).toLocaleDateString()}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Updated:</strong> {new Date(project.updated_at).toLocaleDateString()}
            </Typography>
          </CardContent>
        </Card>

        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Environment Variables ({variables.length})
            </Typography>
            <Box display="flex" gap={1}>
              <Button
                variant="outlined"
                startIcon={showValues ? <HideIcon /> : <ViewIcon />}
                onClick={() => setShowValues(!showValues)}
              >
                {showValues ? 'Hide Values' : 'Show Values'}
              </Button>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddVariable}
              >
                Add Variable
              </Button>
              <Button
                variant="outlined"
                startIcon={<ImportIcon />}
                onClick={() => setImportDialogOpen(true)}
              >
                Import Variables
              </Button>
              <Button
                variant="outlined"
                startIcon={<SettingsIcon />}
                onClick={handleOpenHistorySettings}
              >
                History Settings
              </Button>
            </Box>
          </Box>

          {deletionError && (
            <Alert 
              severity="error" 
              sx={{ mb: 2 }}
              onClose={() => setDeletionError(null)}
            >
              {deletionError}
            </Alert>
          )}

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Value/Reference</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {variables.map((variable) => (
                  <TableRow 
                    key={variable.id} 
                    hover
                    sx={{
                      backgroundColor: highlightVar && variable.id.toString() === highlightVar 
                        ? 'warning.light' 
                        : 'inherit',
                      '&:hover': {
                        backgroundColor: highlightVar && variable.id.toString() === highlightVar 
                          ? 'warning.main' 
                          : undefined,
                      }
                    }}
                  >
                    <TableCell>
                      <Typography variant="subtitle2" fontWeight="medium">
                        {variable.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={getVariableType(variable)} 
                        size="small" 
                        color="primary" 
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography 
                        variant="body2" 
                        fontFamily="monospace"
                        sx={{ 
                          wordBreak: 'break-all',
                          color: variable.is_encrypted ? 'warning.main' : 'text.primary'
                        }}
                      >
                        {getVariableDisplayValue(variable)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {variable.description || 'No description'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box display="flex" gap={1}>
                        <Tooltip title="Edit Variable">
                          <IconButton
                            size="small"
                            onClick={() => handleEditVariable(variable.id)}
                            color="secondary"
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete Variable">
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteVariable(variable.id)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Variable History">
                          <IconButton
                            size="small"
                            onClick={() => handleShowHistory(variable.id, variable.name)}
                            color="primary"
                          >
                            <HistoryIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Impact Analysis">
                          <IconButton
                            size="small"
                            onClick={() => handleShowImpactAnalysis(variable.id)}
                            color="info"
                          >
                            <AnalyticsIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {variables.length === 0 && (
            <Box textAlign="center" my={4}>
              <Typography variant="h6" color="text.secondary">
                No environment variables found
              </Typography>
              <Typography variant="body2" color="text.secondary" mt={1}>
                Add your first environment variable to get started
              </Typography>
            </Box>
          )}
        </Box>
      </Box>

      {/* Add/Edit Variable Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingVariableId ? 'Edit Environment Variable' : 'Add Environment Variable'}
        </DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          {typeChangeWarning && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              {typeChangeWarning}
            </Alert>
          )}
          <Box sx={{ pt: 1 }}>
            <TextField
              autoFocus
              margin="dense"
              label="Variable Name"
              fullWidth
              variant="outlined"
              value={formData.name}
              onChange={handleInputChange('name')}
              error={!!formError && !formData.name.trim()}
              helperText={formError && !formData.name.trim() ? 'Variable name is required' : ''}
              sx={{ mb: 2 }}
            />

            <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
              <InputLabel>Variable Type</InputLabel>
              <Select
                value={formData.type}
                label="Variable Type"
                onChange={handleInputChange('type')}
              >
                <MenuItem value="raw">Raw Value</MenuItem>
                <MenuItem value="linked">Linked Variable</MenuItem>
                <MenuItem value="concatenated">Concatenated Variables</MenuItem>
              </Select>
              <FormHelperText>
                {formData.type === 'raw' && 'Direct value stored in this variable'}
                {formData.type === 'linked' && 'Reference to another project\'s variable (format: PROJECT:VAR)'}
                {formData.type === 'concatenated' && 'Combine multiple variables (format: PROJECT:VAR|PROJECT:VAR)'}
              </FormHelperText>
            </FormControl>

            {formData.type === 'raw' && (
              <TextField
                margin="dense"
                label="Raw Value"
                fullWidth
                variant="outlined"
                multiline
                rows={3}
                value={formData.raw_value}
                onChange={handleInputChange('raw_value')}
                error={!!formError && !formData.raw_value.trim()}
                helperText={formError && !formData.raw_value.trim() ? 'Raw value is required' : ''}
                sx={{ mb: 2 }}
              />
            )}

            {formData.type === 'linked' && (
              <Box>
                <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
                  <InputLabel>Select Project</InputLabel>
                  <Select
                    value={selectedProjectId || ''}
                    label="Select Project"
                    onChange={(e) => {
                      const projectId = e.target.value as number;
                      setSelectedProjectId(projectId);
                      setFormData(prev => ({ ...prev, linked_to: '' }));
                      setAvailableVariables([]);
                      if (projectId) {
                        loadVariablesForProject(projectId);
                      }
                    }}
                  >
                    <MenuItem value="">
                      <em>Select a project...</em>
                    </MenuItem>
                    {availableProjects.map((project) => (
                      <MenuItem key={project.id} value={project.id}>
                        {project.name} - {project.description}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>Select a project to link variables from</FormHelperText>
                </FormControl>

                {selectedProjectId && (
                  <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
                    <InputLabel>Select Variable</InputLabel>
                    <Select
                      value={formData.linked_to}
                      label="Select Variable"
                      onChange={handleInputChange('linked_to')}
                      disabled={availableVariables.length === 0}
                    >
                      <MenuItem value="">
                        <em>Select a variable...</em>
                      </MenuItem>
                      {availableVariables.map((variable) => (
                        <MenuItem key={variable.id} value={`${availableProjects.find(p => p.id === selectedProjectId)?.name}:${variable.name}`}>
                          {variable.name} - {variable.description || 'No description'}
                        </MenuItem>
                      ))}
                    </Select>
                    <FormHelperText>
                      {availableVariables.length === 0 ? 'No variables available in selected project' : 'Select a variable to link to'}
                    </FormHelperText>
                  </FormControl>
                )}
              </Box>
            )}

            {formData.type === 'concatenated' && (
              <Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Build concatenation string by selecting variables and adding separators:
                </Typography>
                
                                  <TextField
                    margin="dense"
                    label="Concatenation String"
                    fullWidth
                    variant="outlined"
                    value={formData.concat_parts}
                    onChange={handleInputChange('concat_parts')}
                    placeholder={'e.g., "Test:VAR1"|"Test:VAR2" or "Test:VAR1"_"Test:VAR2"'}
                    helperText={'Variables are quoted and can be separated by any character: "PROJECT:VAR"_"PROJECT:VAR"'}
                    sx={{ mb: 2 }}
                  />

                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Available variables from current project:
                  </Typography>
                  <FormControl fullWidth margin="dense" sx={{ mb: 2 }}>
                    <InputLabel>Select Variable to Add</InputLabel>
                    <Select
                      value=""
                      label="Select Variable to Add"
                      onChange={(e) => {
                        const selectedVarName = e.target.value as string;
                        if (selectedVarName) {
                          const projectName = project?.name || '';
                          const currentValue = formData.concat_parts;
                          
                          // Check if we need a separator
                          if (currentValue) {
                            const lastChar = currentValue.slice(-1);
                            const isSeparator = ['|', '_', '-', '/', '\\', ';', ',', ' '].includes(lastChar);
                            
                            if (!isSeparator) {
                              // Show error - user must add a separator first
                              setFormError('You must add a separator before adding another variable');
                              return;
                            }
                          }
                          
                          // Add the variable with quotes
                          const quotedVariable = `"${projectName}:${selectedVarName}"`;
                          const newValue = currentValue 
                            ? `${currentValue}${quotedVariable}`
                            : quotedVariable;
                          setFormData(prev => ({ ...prev, concat_parts: newValue }));
                          
                          // Clear any previous errors
                          if (formError) setFormError(null);
                        }
                      }}
                    >
                      {currentProjectVariables
                        .filter((variable) => {
                          // Exclude the current variable being edited from the dropdown
                          if (editingVariableId) {
                            const currentVar = variables.find(v => v.id === editingVariableId);
                            return currentVar ? variable.name !== currentVar.name : true;
                          }
                          return true;
                        })
                        .map((variable) => (
                          <MenuItem key={variable.id} value={variable.name}>
                            {variable.name} ({variable.value_type})
                          </MenuItem>
                        ))}
                    </Select>
                    <FormHelperText>
                      {(() => {
                        const currentValue = formData.concat_parts;
                        if (!currentValue) {
                          return 'Select the first variable for concatenation';
                        }
                        const lastChar = currentValue.slice(-1);
                        const isSeparator = ['|', '_', '-', '/', '\\', ';', ',', ' '].includes(lastChar);
                        
                        if (isSeparator) {
                          return 'Select the next variable to add';
                        } else {
                          return 'Add a separator first before selecting another variable';
                        }
                      })()}
                    </FormHelperText>
                  </FormControl>
                  
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    Quick separators {formData.concat_parts && !['|', '_', '-', '/', '\\', ';', ',', ' '].includes(formData.concat_parts.slice(-1)) ? '(required before next variable):' : ':'}
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {['|', '_', '-', '/', '\\', ';', ',', ' '].map((separator) => {
                      const currentValue = formData.concat_parts;
                      const lastChar = currentValue.slice(-1);
                      const isSeparator = ['|', '_', '-', '/', '\\', ';', ',', ' '].includes(lastChar);
                      const isDisabled = !currentValue || isSeparator;
                      
                      return (
                        <Chip
                          key={separator}
                          label={separator === ' ' ? 'SPACE' : separator}
                          size="small"
                          variant={isDisabled ? "filled" : "outlined"}
                          color={isDisabled ? "default" : "primary"}
                          onClick={() => {
                            if (!isDisabled) {
                              setFormData(prev => ({ ...prev, concat_parts: `${currentValue}${separator}` }));
                            }
                          }}
                          sx={{ 
                            cursor: isDisabled ? 'not-allowed' : 'pointer',
                            opacity: isDisabled ? 0.5 : 1
                          }}
                        />
                      );
                    })}
                  </Box>
                </Box>
              </Box>
            )}

            <TextField
              margin="dense"
              label="Description"
              fullWidth
              variant="outlined"
              multiline
              rows={2}
              value={formData.description}
              onChange={handleInputChange('description')}
              placeholder="Optional description of this variable"
              sx={{ mb: 2 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button 
            onClick={handleSubmit} 
            variant="contained"
            disabled={!formData.name.trim() || 
              (formData.type === 'raw' && !formData.raw_value.trim()) ||
              (formData.type === 'linked' && !formData.linked_to.trim()) ||
              (formData.type === 'concatenated' && !formData.concat_parts.trim())
            }
          >
            {editingVariableId ? 'Update Variable' : 'Create Variable'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Impact Analysis Dialog */}
      <ImpactAnalysisDialog
        open={impactDialogOpen}
        onClose={handleCloseImpactDialog}
        impactData={impactAnalysisData}
        loading={impactAnalysisLoading}
        onProceedWithEdit={handleProceedWithEdit}
        onUntrackExport={handleUntrackExport}
      />

      {/* Import Variables Dialog */}
      <ImportEnvDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        projectId={Number(id)}
        projectName={project?.name || 'Unknown Project'}
        onImportComplete={handleImportComplete}
      />

      {/* Variable History Dialog */}
      {selectedVariableId && (
        <VariableHistoryDialog
          open={historyDialogOpen}
          onClose={handleCloseHistory}
          variableId={selectedVariableId}
          variableName={selectedVariableName}
          onVariableUpdated={handleVariableUpdated}
        />
      )}

      {/* Project History Settings Dialog */}
      <ProjectHistorySettingsDialog
        open={historySettingsOpen}
        onClose={handleCloseHistorySettings}
        projectId={Number(id)}
        projectName={project?.name || 'Unknown Project'}
      />
    </Box>
  );
};

export default ProjectDetail; 