import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { useAppStore } from '../store';

const Projects: React.FC = () => {
  const navigate = useNavigate();
  const { projects, loading, fetchProjects, createProject, updateProject, deleteProject } = useAppStore();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ name: '', description: '' });
  const [formError, setFormError] = useState<string | null>(null);
  const [editingProjectId, setEditingProjectId] = useState<number | null>(null);

  useEffect(() => {
    fetchProjects();
    // Clear any global errors when Projects component loads
    useAppStore.getState().setError(null);
  }, [fetchProjects]);

  // Refresh projects when the page becomes visible (user navigates back)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        fetchProjects();
      }
    };

    const handleFocus = () => {
      fetchProjects();
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('focus', handleFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [fetchProjects]);

  const handleViewProject = (projectId: number) => {
    navigate(`/projects/${projectId}`);
  };

  const handleAddProject = () => {
    setDialogOpen(true);
    setFormData({ name: '', description: '' });
    setFormError(null);
    setEditingProjectId(null);
    // Clear any global errors from the store
    useAppStore.getState().setError(null);
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setFormData({ name: '', description: '' });
    setFormError(null);
    setEditingProjectId(null);
  };

  const handleSubmit = async () => {
    if (!formData.name.trim()) {
      setFormError('Project name is required');
      return;
    }

    // Clear any previous form errors
    setFormError(null);

    try {
      if (editingProjectId) {
        // Update existing project
        await updateProject(editingProjectId, {
          name: formData.name.trim(),
          description: formData.description.trim() || '',
        });
      } else {
        // Create new project
        await createProject({
          name: formData.name.trim(),
          description: formData.description.trim() || '',
        });
      }
      handleCloseDialog();
    } catch (error) {
      // Display the error in the dialog
      setFormError(error instanceof Error ? error.message : `Failed to ${editingProjectId ? 'update' : 'create'} project`);
    }
  };

  const handleInputChange = (field: 'name' | 'description') => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [field]: event.target.value }));
    if (formError) setFormError(null);
  };

  const handleEditProject = (projectId: number) => {
    const project = projects.find(p => p.id === projectId);
    if (project) {
      setFormData({ name: project.name, description: project.description || '' });
      setDialogOpen(true);
      setFormError(null);
      setEditingProjectId(projectId);
      // Clear any global errors from the store
      useAppStore.getState().setError(null);
    }
  };

  const handleDeleteProject = async (projectId: number) => {
    if (window.confirm('Are you sure you want to delete this project? This action cannot be undone.')) {
      try {
        await deleteProject(projectId);
      } catch (error) {
        console.error('Failed to delete project:', error);
      }
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" my={4}>
        <Typography>Loading projects...</Typography>
      </Box>
    );
  }

  // Remove global error display since we handle errors in dialogs

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Projects
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddProject}
        >
          Add Project
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Description</TableCell>
              <TableCell>Variables</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {projects.map((project) => (
              <TableRow key={project.id} hover>
                <TableCell>
                  <Typography variant="subtitle1" fontWeight="medium">
                    {project.name}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {project.description || 'No description'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip 
                    label={`${project.variables_count || 0} vars`} 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {new Date(project.created_at).toLocaleDateString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => handleViewProject(project.id)}
                        color="primary"
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Edit Project">
                      <IconButton
                        size="small"
                        onClick={() => handleEditProject(project.id)}
                        color="secondary"
                      >
                        <EditIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete Project">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteProject(project.id)}
                        color="error"
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {projects.length === 0 && (
        <Box textAlign="center" my={4}>
          <Typography variant="h6" color="text.secondary">
            No projects found
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={1}>
            Create your first project to get started
          </Typography>
        </Box>
      )}

      {/* Add/Edit Project Dialog */}
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>{editingProjectId ? 'Edit Project' : 'Add New Project'}</DialogTitle>
        <DialogContent>
          {formError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {formError}
            </Alert>
          )}
          <Box sx={{ pt: 1 }}>
            <TextField
              autoFocus
              margin="dense"
              label="Project Name"
              fullWidth
              variant="outlined"
              value={formData.name}
              onChange={handleInputChange('name')}
              error={!!formError && !formData.name.trim()}
              helperText={formError && !formData.name.trim() ? 'Project name is required' : ''}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Description"
              fullWidth
              variant="outlined"
              multiline
              rows={3}
              value={formData.description}
              onChange={handleInputChange('description')}
              placeholder="Optional description of the project"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
                              <Button 
                      onClick={handleSubmit} 
                      variant="contained"
                      disabled={!formData.name.trim()}
                    >
                      {editingProjectId ? 'Update Project' : 'Create Project'}
                    </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Projects; 