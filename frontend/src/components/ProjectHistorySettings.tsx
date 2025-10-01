import React, { useState, useEffect, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Divider
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Warning as WarningIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { apiClient, type ProjectHistorySettings, HistorySettingsUpdate, HistorySettingsResponse } from '../api/client';

interface ProjectHistorySettingsProps {
  open: boolean;
  onClose: () => void;
  projectId: number;
  projectName: string;
}

const ProjectHistorySettingsDialog: React.FC<ProjectHistorySettingsProps> = ({
  open,
  onClose,
  projectId,
  projectName
}) => {
  const [settings, setSettings] = useState<ProjectHistorySettings | null>(null);
  const [newLimit, setNewLimit] = useState<number>(5);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warning, setWarning] = useState<HistorySettingsResponse | null>(null);

  const loadSettings = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.getProjectHistorySettings(projectId);
      setSettings(result);
      setNewLimit(result.history_limit);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load project settings');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (open && projectId) {
      loadSettings();
    }
  }, [open, projectId, loadSettings]);

  const handleSave = async (confirmCleanup: boolean = false) => {
    setSaving(true);
    setError(null);
    setWarning(null);

    try {
      const request: HistorySettingsUpdate = {
        history_limit: newLimit,
        confirm_cleanup: confirmCleanup
      };

      const result = await apiClient.updateProjectHistorySettings(projectId, request);

      if (result.requires_confirmation && !confirmCleanup) {
        setWarning(result);
      } else if (result.success) {
        setSettings(prev => prev ? { ...prev, history_limit: newLimit } : null);
        setWarning(null);
      } else {
        setError(result.error || 'Failed to update settings');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update settings');
    } finally {
      setSaving(false);
    }
  };

  const handleConfirmCleanup = () => {
    handleSave(true);
  };

  const handleCancelCleanup = () => {
    setWarning(null);
    setNewLimit(settings?.history_limit || 5);
  };

  const renderWarningDialog = () => {
    if (!warning) return null;

    return (
      <Alert severity="warning" sx={{ mt: 2 }}>
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            <WarningIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
            History Cleanup Required
          </Typography>
          
          <Typography variant="body2" paragraph>
            {warning.warning}
          </Typography>
          
          <Box display="flex" gap={1} mt={2}>
            <Button
              variant="contained"
              color="warning"
              size="small"
              onClick={handleConfirmCleanup}
              disabled={saving}
            >
              Confirm & Delete History
            </Button>
            <Button
              variant="outlined"
              size="small"
              onClick={handleCancelCleanup}
              disabled={saving}
            >
              Cancel
            </Button>
          </Box>
        </Box>
      </Alert>
    );
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="md" 
      fullWidth
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <SettingsIcon />
            <Typography variant="h6">
              History Settings: {projectName}
            </Typography>
          </Box>
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
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <HistoryIcon />
                  Variable History Configuration
                </Typography>
                
                <Typography variant="body2" color="text.secondary" paragraph>
                  Configure how many versions of each variable to keep in history. 
                  Variable history is automatically enabled and cannot be disabled.
                </Typography>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Current Settings:
                  </Typography>
                  
                  <Box display="flex" gap={3} mb={3}>
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        History Status
                      </Typography>
                      <Typography variant="body1" fontWeight="bold" color="success.main">
                        ✓ Enabled (Always On)
                      </Typography>
                    </Box>
                    
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Current Limit
                      </Typography>
                      <Typography variant="body1" fontWeight="bold">
                        {settings?.history_limit || 'Loading...'} versions per variable
                      </Typography>
                    </Box>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <FormControl fullWidth sx={{ mt: 2 }}>
                    <InputLabel>History Limit (per variable)</InputLabel>
                    <Select
                      value={newLimit}
                      label="History Limit (per variable)"
                      onChange={(e) => setNewLimit(Number(e.target.value))}
                    >
                      {[1, 2, 3, 4, 5, 10, 15, 20, 25, 30].map((limit) => (
                        <MenuItem key={limit} value={limit}>
                          {limit} version{limit === 1 ? '' : 's'} per variable
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <Alert severity="info" sx={{ mt: 2 }}>
                    <Typography variant="body2">
                      <strong>Note:</strong> Reducing the history limit will permanently delete older versions. 
                      Increasing the limit will retain more history going forward.
                    </Typography>
                  </Alert>
                </Box>
              </CardContent>
            </Card>

            {renderWarningDialog()}
          </>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={saving}>
          Cancel
        </Button>
        <Button 
          variant="contained" 
          onClick={() => handleSave(false)}
          disabled={saving || newLimit === settings?.history_limit}
        >
          {saving ? <CircularProgress size={20} /> : 'Save Settings'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProjectHistorySettingsDialog; 