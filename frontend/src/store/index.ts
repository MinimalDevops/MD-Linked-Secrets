import { create } from 'zustand';
import { apiClient, Project, EnvVar, Export } from '../api/client';

interface AppState {
  // State
  projects: Project[];
  envVars: EnvVar[];
  exports: Export[];
  loading: boolean;
  error: string | null;
  selectedProject: Project | null;
  resolvedValues: Record<string, string>;

  // Actions
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setSelectedProject: (project: Project | null) => void;
  
  // Projects
  fetchProjects: () => Promise<void>;
  createProject: (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  updateProject: (id: number, project: Partial<Project>) => Promise<void>;
  deleteProject: (id: number) => Promise<void>;
  
  // Environment Variables
  fetchEnvVars: (projectId?: number) => Promise<void>;
  createEnvVar: (envVar: Omit<EnvVar, 'id' | 'created_at' | 'updated_at'>) => Promise<void>;
  updateEnvVar: (id: number, envVar: Partial<EnvVar>) => Promise<void>;
  deleteEnvVar: (id: number) => Promise<void>;
  
  // Variable Resolution
  resolveVariables: (projectId?: number, varId?: number) => Promise<void>;
  
  // Exports
  fetchExports: (projectId?: number) => Promise<void>;
  exportProject: (
    projectName: string,
    outDir: string,
    options?: {
      withPrefix?: boolean;
      withSuffix?: boolean;
      prefixValue?: string;
      suffixValue?: string;
    }
  ) => Promise<void>;
  checkUpdates: (projectId?: number) => Promise<{ total_checked: number; outdated_count: number }>;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  projects: [],
  envVars: [],
  exports: [],
  loading: false,
  error: null,
  selectedProject: null,
  resolvedValues: {},

  // Basic actions
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  setSelectedProject: (project) => set({ selectedProject: project }),

  // Projects
  fetchProjects: async () => {
    set({ loading: true, error: null });
    try {
      const projects = await apiClient.getProjects();
      set({ projects, loading: false });
    } catch (error) {
      set({ 
        loading: false 
        // Don't set global error for project fetching - handle in component if needed
      });
      // Log the error but don't display it globally
      console.error('Failed to fetch projects:', error);
    }
  },

  createProject: async (project) => {
    set({ loading: true, error: null });
    try {
      const newProject = await apiClient.createProject(project);
      set(state => ({ 
        projects: [...state.projects, newProject], 
        loading: false 
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create project';
      set({ 
        loading: false 
        // Don't set global error - let component handle it
      });
      throw new Error(errorMessage); // Re-throw for component handling
    }
  },

  updateProject: async (id, project) => {
    set({ loading: true, error: null });
    try {
      const updatedProject = await apiClient.updateProject(id, project);
      set(state => ({ 
        projects: state.projects.map(p => p.id === id ? updatedProject : p), 
        loading: false 
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update project';
      set({ 
        loading: false 
        // Don't set global error - let component handle it
      });
      throw new Error(errorMessage); // Re-throw for component handling
    }
  },

  deleteProject: async (id) => {
    set({ loading: true, error: null });
    try {
      await apiClient.deleteProject(id);
      set(state => ({ 
        projects: state.projects.filter(p => p.id !== id), 
        loading: false 
      }));
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to delete project', 
        loading: false 
      });
    }
  },

  // Environment Variables
  fetchEnvVars: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const envVars = await apiClient.getEnvVars(projectId);
      set({ envVars, loading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch environment variables', 
        loading: false 
      });
    }
  },

  createEnvVar: async (envVar) => {
    set({ loading: true, error: null });
    try {
      const newEnvVar = await apiClient.createEnvVar(envVar);
      set(state => ({ 
        envVars: [...state.envVars, newEnvVar], 
        loading: false 
      }));
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to create environment variable', 
        loading: false 
      });
    }
  },

  updateEnvVar: async (id, envVar) => {
    set({ loading: true, error: null });
    try {
      const updatedEnvVar = await apiClient.updateEnvVar(id, envVar);
      set(state => ({ 
        envVars: state.envVars.map(v => v.id === id ? updatedEnvVar : v), 
        loading: false 
      }));
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to update environment variable', 
        loading: false 
      });
    }
  },

  deleteEnvVar: async (id) => {
    set({ loading: true, error: null });
    try {
      await apiClient.deleteEnvVar(id);
      set(state => ({ 
        envVars: state.envVars.filter(v => v.id !== id), 
        loading: false 
      }));
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to delete environment variable', 
        loading: false 
      });
    }
  },

  // Variable Resolution
  resolveVariables: async (projectId, varId) => {
    set({ loading: true, error: null });
    try {
      const result = await apiClient.resolveVariables(projectId, varId);
      set({ resolvedValues: result.resolved_values, loading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to resolve variables', 
        loading: false 
      });
    }
  },

  // Exports
  fetchExports: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const exports = await apiClient.getExports(projectId);
      set({ exports, loading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to fetch exports', 
        loading: false 
      });
    }
  },

  exportProject: async (projectName, outDir, options) => {
    set({ loading: true, error: null });
    try {
      const result = await apiClient.exportProject(projectName, outDir, options);
      if (result.success) {
        // Refresh exports after successful export
        await get().fetchExports();
      }
      set({ loading: false });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to export project', 
        loading: false 
      });
    }
  },

  checkUpdates: async (projectId) => {
    set({ loading: true, error: null });
    try {
      const result = await apiClient.checkUpdates(projectId);
      set({ loading: false });
      return result;
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : 'Failed to check updates', 
        loading: false 
      });
      return { total_checked: 0, outdated_count: 0 };
    }
  },
})); 