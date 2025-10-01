import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  IconButton,
  Collapse,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  AccountTree as GitIcon,
} from '@mui/icons-material';
import { VariableImpactAnalysis } from '../api/client';
import { useState } from 'react';

interface ImpactAnalysisDialogProps {
  open: boolean;
  onClose: () => void;
  impactData: VariableImpactAnalysis | null;
  loading?: boolean;
  onProceedWithEdit: () => void;
  onUntrackExport?: (exportId: number) => void;
}

const ImpactAnalysisDialog: React.FC<ImpactAnalysisDialogProps> = ({
  open,
  onClose,
  impactData,
  loading = false,
  onProceedWithEdit,
  onUntrackExport,
}) => {
  const [expandedProjects, setExpandedProjects] = useState<Record<string, boolean>>({});

  const toggleProjectExpansion = (projectName: string) => {
    setExpandedProjects(prev => ({
      ...prev,
      [projectName]: !prev[projectName]
    }));
  };

  const handleUntrackExport = (exportId: number) => {
    if (onUntrackExport) {
      onUntrackExport(exportId);
    }
  };

  const getSeverityLevel = () => {
    if (!impactData) return 'info';
    
    const { impact_summary } = impactData;
    if (impact_summary.has_cross_project_impact || impact_summary.total_variables_affected > 5) {
      return 'warning';
    } else if (impact_summary.total_variables_affected > 0) {
      return 'info';
    } else {
      return 'success';
    }
  };

  const getSeverityIcon = () => {
    const severity = getSeverityLevel();
    switch (severity) {
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'info':
        return <InfoIcon color="info" />;
      case 'success':
        return <CheckCircleIcon color="success" />;
      default:
        return <InfoIcon />;
    }
  };

  const getSeverityMessage = () => {
    if (!impactData) return 'Loading impact analysis...';
    
    const { impact_summary } = impactData;
    
    if (impact_summary.total_variables_affected === 0) {
      return 'No variables will be affected by this change.';
    }
    
    if (impact_summary.has_cross_project_impact) {
      return `This change will affect ${impact_summary.total_variables_affected} variables across ${impact_summary.total_projects_affected} projects.`;
    } else {
      return `This change will affect ${impact_summary.total_variables_affected} variables within the current project.`;
    }
  };

  if (loading) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>Analyzing Impact...</DialogTitle>
        <DialogContent>
          <Box display="flex" justifyContent="center" py={4}>
            <Typography>Loading impact analysis...</Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
        </DialogActions>
      </Dialog>
    );
  }

  if (!impactData) {
    return null;
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center" gap={1}>
          {getSeverityIcon()}
          <Typography variant="h6">
            Impact Analysis: {impactData.source_variable.name}
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Box mb={3}>
          <Alert severity={getSeverityLevel()}>
            <Typography variant="body1" fontWeight="medium">
              {getSeverityMessage()}
            </Typography>
          </Alert>
        </Box>

        {/* Summary Stats */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Impact Summary
            </Typography>
            <Box display="flex" gap={2} flexWrap="wrap">
              <Chip 
                label={`${impactData.impact_summary.total_projects_affected} Projects`}
                color={impactData.impact_summary.total_projects_affected > 1 ? "warning" : "default"}
              />
              <Chip 
                label={`${impactData.impact_summary.total_variables_affected} Variables`}
                color={impactData.impact_summary.total_variables_affected > 0 ? "info" : "default"}
              />
              <Chip 
                label={`${impactData.impact_summary.total_exports_affected} Exports`}
                color={impactData.impact_summary.total_exports_affected > 0 ? "secondary" : "default"}
              />
              {impactData.impact_summary.has_cross_project_impact && (
                <Chip 
                  label="Cross-Project Impact"
                  color="warning"
                  icon={<WarningIcon />}
                />
              )}
            </Box>
          </CardContent>
        </Card>

        {/* Affected Projects */}
        {impactData.affected_projects.length > 0 && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Affected Projects & Variables
              </Typography>
              
              {impactData.affected_projects.map((project, index) => (
                <Box key={project.project_id} mb={2}>
                  <Box 
                    display="flex" 
                    alignItems="center" 
                    justifyContent="space-between"
                    sx={{ 
                      cursor: 'pointer',
                      p: 1,
                      borderRadius: 1,
                      '&:hover': { bgcolor: 'action.hover' }
                    }}
                    onClick={() => toggleProjectExpansion(project.project_name)}
                  >
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="subtitle1" fontWeight="medium">
                        📁 {project.project_name}
                      </Typography>
                      <Chip 
                        size="small" 
                        label={`${project.variables.length} variables`}
                        color="primary"
                        variant="outlined"
                      />
                    </Box>
                    <IconButton size="small">
                      {expandedProjects[project.project_name] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                    </IconButton>
                  </Box>
                  
                  <Collapse in={expandedProjects[project.project_name]}>
                    <Box ml={2}>
                      {project.project_description && (
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {project.project_description}
                        </Typography>
                      )}
                      
                      <List dense>
                        {project.variables.map((variable) => (
                          <ListItem key={variable.id} sx={{ py: 0.5 }}>
                            <ListItemText
                              primary={
                                <Box display="flex" alignItems="center" gap={1}>
                                  <Typography variant="body2" fontWeight="medium">
                                    {variable.name}
                                  </Typography>
                                  <Chip 
                                    size="small" 
                                    label={variable.type}
                                    variant="outlined"
                                    color={variable.type === 'linked' ? 'info' : variable.type === 'concatenated' ? 'secondary' : 'default'}
                                  />
                                </Box>
                              }
                              secondary={
                                <Box>
                                  {variable.description && (
                                    <Typography variant="caption" display="block">
                                      {variable.description}
                                    </Typography>
                                  )}
                                  {variable.reference && (
                                    <Typography variant="caption" color="text.secondary" display="block">
                                      Reference: {variable.reference}
                                    </Typography>
                                  )}
                                </Box>
                              }
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  </Collapse>
                  
                  {index < impactData.affected_projects.length - 1 && <Divider sx={{ my: 1 }} />}
                </Box>
              ))}
            </CardContent>
          </Card>
        )}

        {/* Affected Exports */}
        {impactData.affected_exports.length > 0 && (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Affected Exports
              </Typography>
              <List dense>
                {impactData.affected_exports.map((exportItem) => (
                  <ListItem key={exportItem.export_id} sx={{ flexDirection: 'column', alignItems: 'stretch', py: 2 }}>
                    <Box>
                      <Typography variant="body2" fontWeight="medium" gutterBottom>
                        Full export path:
                      </Typography>
                      <Box display="flex" alignItems="center" gap={2} mb={1}>
                        <Typography variant="body2" fontFamily="monospace" sx={{ 
                          bgcolor: 'grey.50', 
                          p: 1, 
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: 'grey.300',
                          flex: 1
                        }}>
                          {exportItem.export_path}
                        </Typography>
                        <Button
                          size="small"
                          color="error"
                          variant="outlined"
                          onClick={() => handleUntrackExport(exportItem.export_id)}
                          sx={{ 
                            minWidth: '80px',
                            height: '32px',
                            alignSelf: 'stretch'
                          }}
                        >
                          Untrack
                        </Button>
                      </Box>
                      
                      {/* Git Information */}
                      {exportItem.is_git_repo && (
                        <Box sx={{ 
                          bgcolor: 'primary.50', 
                          p: 1, 
                          borderRadius: 1,
                          border: '1px solid',
                          borderColor: 'primary.200',
                          mb: 1
                        }}>
                          <Box display="flex" alignItems="center" gap={1} mb={0.5}>
                            <GitIcon color="primary" fontSize="small" />
                            <Typography variant="body2" fontWeight="medium" color="primary.main">
                              Git Repository
                            </Typography>
                          </Box>
                          <Box display="flex" flexDirection="column" gap={0.5}>
                            {exportItem.git_branch && (
                              <Typography variant="body2" color="text.secondary">
                                <strong>Branch:</strong> {exportItem.git_branch}
                              </Typography>
                            )}
                            {exportItem.git_commit_hash && (
                              <Typography variant="body2" color="text.secondary" fontFamily="monospace">
                                <strong>Commit:</strong> {exportItem.git_commit_hash.substring(0, 8)}...
                              </Typography>
                            )}
                            {exportItem.git_remote_url && (
                              <Typography variant="body2" color="text.secondary" sx={{ 
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                whiteSpace: 'nowrap',
                                maxWidth: '300px'
                              }}>
                                <strong>Remote:</strong> {exportItem.git_remote_url}
                              </Typography>
                            )}
                          </Box>
                        </Box>
                      )}
                      
                      <Typography variant="body2" color="text.secondary">
                        Exported: {new Date(exportItem.exported_at).toLocaleString()}
                      </Typography>
                    </Box>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        )}

        {/* Recommendations */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recommendations
            </Typography>
            <List dense>
              {impactData.recommendations.map((recommendation, index) => (
                <ListItem key={index}>
                  <ListItemText
                    primary={
                      <Typography variant="body2">
                        • {recommendation}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </CardContent>
        </Card>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onClose} color="secondary">
          Cancel Changes
        </Button>
        <Button 
          onClick={() => {
            onProceedWithEdit();
            onClose();
          }} 
          variant="contained"
          color={getSeverityLevel() === 'warning' ? 'warning' : 'primary'}
        >
          {getSeverityLevel() === 'warning' ? 'Proceed with Caution' : 'Proceed with Edit'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ImpactAnalysisDialog; 