import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
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
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Visibility as ViewIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Compare as CompareIcon,
} from '@mui/icons-material';
import { useAppStore } from '../store';

interface Export {
  id: number;
  project_id: number;
  project_name?: string;
  export_path: string;
  exported_at: string;
  with_prefix: boolean;
  with_suffix: boolean;
  prefix_value?: string;
  suffix_value?: string;
  resolved_values: Record<string, string>;
  export_hash?: string;
}

const Exports: React.FC = () => {
  const { exports: exportHistory, loading, error, fetchExports } = useAppStore();
  const [selectedExport, setSelectedExport] = useState<Export | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    fetchExports();
  }, [fetchExports]);

  const handleViewExport = (exportItem: Export) => {
    setSelectedExport(exportItem);
    setDialogOpen(true);
  };

  const handleRefresh = () => {
    fetchExports();
  };

  const handleDownloadExport = (exportItem: Export) => {
    // TODO: Implement download functionality
    console.log('Download export:', exportItem);
  };

  const handleDeleteExport = (exportId: number) => {
    // TODO: Implement delete functionality
    console.log('Delete export:', exportId);
  };

  const handleCompareExport = (exportId: number) => {
    // TODO: Implement compare functionality
    console.log('Compare export:', exportId);
  };

  const formatExportPath = (path: string) => {
    const parts = path.split('/');
    return parts.length > 2 ? `.../${parts.slice(-2).join('/')}` : path;
  };

  const getExportStatus = (exportItem: Export) => {
    // TODO: Implement status checking logic
    return 'current'; // Placeholder
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" my={4}>
        <Typography>Loading exports...</Typography>
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

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Export History
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
        >
          Refresh
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Project</TableCell>
              <TableCell>Export Path</TableCell>
              <TableCell>Exported At</TableCell>
              <TableCell>Variables</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {exportHistory.map((exportItem) => (
              <TableRow key={exportItem.id} hover>
                <TableCell>
                  <Typography variant="subtitle2" fontWeight="medium">
                    {(exportItem as any).project_name || `Project ${exportItem.project_id}`}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace">
                    {formatExportPath(exportItem.export_path)}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {new Date(exportItem.exported_at).toLocaleString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip 
                    label={`${Object.keys(exportItem.resolved_values).length} vars`} 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                  />
                </TableCell>
                <TableCell>
                  <Chip 
                    label={getExportStatus(exportItem)} 
                    size="small" 
                    color={getExportStatus(exportItem) === 'current' ? 'success' : 'warning'}
                  />
                </TableCell>
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Tooltip title="View Details">
                      <IconButton
                        size="small"
                        onClick={() => handleViewExport(exportItem)}
                        color="primary"
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Download">
                      <IconButton
                        size="small"
                        onClick={() => handleDownloadExport(exportItem)}
                        color="secondary"
                      >
                        <DownloadIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Compare">
                      <IconButton
                        size="small"
                        onClick={() => handleCompareExport(exportItem.id)}
                        color="info"
                      >
                        <CompareIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteExport(exportItem.id)}
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

      {exportHistory.length === 0 && (
        <Box textAlign="center" my={4}>
          <Typography variant="h6" color="text.secondary">
            No exports found
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={1}>
            Export some environment variables to see them here
          </Typography>
        </Box>
      )}

      {/* Export Details Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Export Details
          {selectedExport && (
            <Typography variant="body2" color="text.secondary">
              {(selectedExport as any).project_name} - {formatExportPath(selectedExport.export_path)}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedExport && (
            <Box>
              <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={2}>
                <Box>
                  <Typography variant="subtitle2">Export Path:</Typography>
                  <Typography variant="body2" fontFamily="monospace">
                    {selectedExport.export_path}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2">Exported At:</Typography>
                  <Typography variant="body2">
                    {new Date(selectedExport.exported_at).toLocaleString()}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2">Prefix:</Typography>
                  <Typography variant="body2">
                    {selectedExport.with_prefix ? selectedExport.prefix_value || 'Yes' : 'No'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="subtitle2">Suffix:</Typography>
                  <Typography variant="body2">
                    {selectedExport.with_suffix ? selectedExport.suffix_value || 'Yes' : 'No'}
                  </Typography>
                </Box>
              </Box>
              
              <Typography variant="h6" gutterBottom>
                Resolved Variables
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Variable</TableCell>
                      <TableCell>Value</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(selectedExport.resolved_values).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell>
                          <Typography variant="body2" fontWeight="medium">
                            {key}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {value}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Exports; 