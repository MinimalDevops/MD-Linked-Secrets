import React, { useEffect } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Chip,
} from '@mui/material';
import {
  Folder as FolderIcon,
  Settings as SettingsIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { useAppStore } from '../store';

const Dashboard: React.FC = () => {
  const { projects, exports, resolvedValues, loading, resolveVariables, fetchProjects, fetchExports } = useAppStore();

  useEffect(() => {
    fetchProjects();
    fetchExports();
  }, [fetchProjects, fetchExports]);

  const handleResolveAll = async () => {
    if (projects.length > 0) {
      // Resolve variables for all projects
      for (const project of projects) {
        await resolveVariables(project.id);
      }
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(300px, 1fr))" gap={3}>
        {/* Projects Overview */}
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <FolderIcon color="primary" sx={{ mr: 1 }} />
              <Typography variant="h6">Projects</Typography>
            </Box>
            <Typography variant="h3" color="primary" gutterBottom>
              {projects.length}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total projects managed
            </Typography>
            <Button
              component={RouterLink}
              to="/projects"
              variant="outlined"
              size="small"
              sx={{ mt: 1 }}
            >
              View Projects
            </Button>
          </CardContent>
        </Card>

        {/* Variables Overview */}
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <SettingsIcon color="secondary" sx={{ mr: 1 }} />
              <Typography variant="h6">Variables</Typography>
            </Box>
            <Typography variant="h3" color="secondary" gutterBottom>
              {projects.reduce((total, project) => total + (project.variables_count || 0), 0)}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total environment variables
            </Typography>
            <Button
              onClick={handleResolveAll}
              variant="outlined"
              size="small"
              sx={{ mt: 1 }}
              disabled={loading || projects.length === 0}
            >
              {loading ? 'Resolving...' : 'Resolve All Variables'}
            </Button>
          </CardContent>
        </Card>

        {/* Exports Overview */}
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <DownloadIcon color="success" sx={{ mr: 1 }} />
              <Typography variant="h6">Exports</Typography>
            </Box>
            <Typography variant="h3" color="success.main" gutterBottom>
              {exports.length}
            </Typography>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Total exports created
            </Typography>
            <Button
              component={RouterLink}
              to="/exports"
              variant="outlined"
              size="small"
              sx={{ mt: 1 }}
            >
              View Exports
            </Button>
          </CardContent>
        </Card>

        {/* Recent Projects */}
        <Card sx={{ gridColumn: '1 / -1' }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Projects
            </Typography>
            <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(250px, 1fr))" gap={2}>
              {projects.slice(0, 3).map((project) => (
                <Card variant="outlined" key={project.id}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {project.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {project.description}
                    </Typography>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Chip
                        label={`${project.variables_count || 0} variables`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                      <Button
                        component={RouterLink}
                        to={`/projects/${project.id}`}
                        size="small"
                      >
                        View Details
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </CardContent>
        </Card>

        {/* Resolved Values */}
        {Object.keys(resolvedValues).length > 0 && (
          <Card sx={{ gridColumn: '1 / -1' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recently Resolved Variables
              </Typography>
              <Box display="grid" gridTemplateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={1}>
                {Object.entries(resolvedValues).slice(0, 6).map(([key, value]) => (
                  <Card variant="outlined" key={key}>
                    <CardContent sx={{ py: 1 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        {key}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {value}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            </CardContent>
          </Card>
        )}
      </Box>
    </Box>
  );
};

export default Dashboard; 