import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import api from '@/api/axios';

export const useAuthStore = create(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
      
      login: async (values) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/auth/token', new URLSearchParams(values));
          const { access_token } = response.data;

          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          const userResponse = await api.get('/auth/users/me');

          set({
            token: access_token,
            user: userResponse.data,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error.response?.data?.detail || 'Login failed',
            isLoading: false,
            isAuthenticated: false,
            token: null,
            user: null,
          });
          throw error;
        }
      },

      loginWithGoogle: async (credential) => {
        set({ isLoading: true, error: null });
        try {
          const response = await api.post('/auth/google', { credential });
          const { access_token } = response.data;

          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          const userResponse = await api.get('/auth/users/me');

          set({
            token: access_token,
            user: userResponse.data,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error.response?.data?.detail || 'Google login failed',
            isLoading: false,
          });
          throw error;
        }
      },

      signup: async (values) => {
         set({ isLoading: true, error: null });
         try {
            await api.post('/auth/signup', values);
            set({ isLoading: false });
         } catch(error) {
            set({
              error: error.response?.data?.detail || 'Signup failed',
              isLoading: false,
            });
            throw error;
         }
      },
      
      logout: () => {
        delete api.defaults.headers.common['Authorization'];
        set({ token: null, user: null, isAuthenticated: false });
      },
      
      checkAuth: () => {
        const token = get().token;
        if (token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          api.get('/auth/users/me').then(response => {
              set({ user: response.data, isAuthenticated: true, isLoading: false });
          }).catch(() => {
              get().logout();
              set({ isLoading: false });
          });
        } else {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
    }
  )
);
