import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import {
  History as HistoryIcon,
  Restore as RestoreIcon,
  AccessTime as TimeIcon,
  Person as PersonIcon,
  Edit as EditIcon,
  Close as CloseIcon
} from '@mui/icons-material';
import { apiClient, VariableWithHistory, VariableHistoryEntry, RestoreVariableRequest } from '../api/client';

interface VariableHistoryDialogProps {
  open: boolean;
  onClose: () => void;
  variableId: number;
  variableName: string;
  onVariableUpdated?: () => void;
}

const VariableHistoryDialog: React.FC<VariableHistoryDialogProps> = ({
  open,
  onClose,
  variableId,
  variableName,
  onVariableUpdated
}) => {
  const [data, setData] = useState<VariableWithHistory | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [restoring, setRestoring] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.getVariableWithHistory(variableId);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load variable history');
    } finally {
      setLoading(false);
    }
  }, [variableId]);

  useEffect(() => {
    if (open && variableId) {
      loadData();
    }
  }, [open, variableId, loadData]);

  const handleRestore = async (version: number) => {
    setRestoring(version);
    setError(null);

    try {
      const request: RestoreVariableRequest = {
        version_number: version,
        change_reason: `Restored via UI to version ${version}`,
        changed_by: 'web_user'
      };

      await apiClient.restoreVariableVersion(variableId, request);
      
      // Reload data to show the restoration
      await loadData();
      
      // Notify parent component
      if (onVariableUpdated) {
        onVariableUpdated();
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restore variable');
    } finally {
      setRestoring(null);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getChangeTypeColor = (changeType: string) => {
    switch (changeType) {
      case 'created': return 'success';
      case 'updated': return 'primary';
      case 'deleted': return 'error';
      case 'restored': return 'warning';
      default: return 'default';
    }
  };

  const getCurrentValue = () => {
    if (!data?.current) return null;
    
    const current = data.current;
    if (current.linked_to) {
      return `→ ${current.linked_to}`;
    } else if (current.concat_parts) {
      return `⚡ ${current.concat_parts}`;
    } else {
      return current.raw_value || '';
    }
  };

  const getHistoryValue = (entry: VariableHistoryEntry) => {
    if (entry.linked_to) {
      return `→ ${entry.linked_to}`;
    } else if (entry.concat_parts) {
      return `⚡ ${entry.concat_parts}`;
    } else {
      return entry.raw_value || '';
    }
  };

  const renderCurrentVariable = () => {
    if (!data?.current) return null;

    return (
      <Card sx={{ mb: 3, bgcolor: 'primary.50', border: '1px solid', borderColor: 'primary.200' }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={1} mb={2}>
            <EditIcon color="primary" />
            <Typography variant="h6" color="primary">
              Current Value
            </Typography>
          </Box>
          
          <Typography variant="body1" fontFamily="monospace" sx={{ 
            bgcolor: 'white', 
            p: 1, 
            borderRadius: 1,
            border: '1px solid #e0e0e0',
            wordBreak: 'break-all'
          }}>
            {getCurrentValue()}
          </Typography>
          
          {data.current.description && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {data.current.description}
            </Typography>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{
        sx: { minHeight: '70vh' }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <HistoryIcon />
            <Typography variant="h6">
              Variable History: {variableName}
            </Typography>
          </Box>
          <IconButton onClick={onClose} size="small">
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {renderCurrentVariable()}

            <Divider sx={{ my: 3 }} />

            <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <HistoryIcon />
              Version History ({data?.history?.length || 0} entries)
            </Typography>

            {data?.history && data.history.length > 0 ? (
              <TableContainer component={Paper} sx={{ mt: 2 }}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Version</strong></TableCell>
                      <TableCell><strong>Value</strong></TableCell>
                      <TableCell><strong>Change Type</strong></TableCell>
                      <TableCell><strong>Reason</strong></TableCell>
                      <TableCell><strong>Time</strong></TableCell>
                      <TableCell><strong>Actions</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {data.history.map((entry) => (
                      <TableRow key={entry.id} hover>
                        <TableCell>
                          <Chip 
                            label={`v${entry.version_number}`} 
                            size="small" 
                            variant="outlined"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography 
                            variant="body2" 
                            fontFamily="monospace"
                            sx={{ 
                              maxWidth: 300,
                              wordBreak: 'break-all',
                              bgcolor: 'grey.50',
                              p: 0.5,
                              borderRadius: 0.5
                            }}
                          >
                            {getHistoryValue(entry)}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={entry.change_type}
                            size="small"
                            color={getChangeTypeColor(entry.change_type) as any}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {entry.change_reason || 'No reason provided'}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={0.5}>
                            <TimeIcon fontSize="small" color="action" />
                            <Typography variant="body2">
                              {formatTimestamp(entry.created_at)}
                            </Typography>
                          </Box>
                          {entry.changed_by && (
                            <Box display="flex" alignItems="center" gap={0.5} mt={0.5}>
                              <PersonIcon fontSize="small" color="action" />
                              <Typography variant="caption" color="text.secondary">
                                {entry.changed_by}
                              </Typography>
                            </Box>
                          )}
                        </TableCell>
                        <TableCell>
                          <Tooltip title={`Restore to version ${entry.version_number}`}>
                            <IconButton
                              size="small"
                              onClick={() => handleRestore(entry.version_number)}
                              disabled={restoring === entry.version_number}
                              color="primary"
                            >
                              {restoring === entry.version_number ? (
                                <CircularProgress size={16} />
                              ) : (
                                <RestoreIcon fontSize="small" />
                              )}
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Alert severity="info" sx={{ mt: 2 }}>
                No history entries found for this variable.
              </Alert>
            )}
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default VariableHistoryDialog; 