import axios from "axios";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;

    if (
      error.response?.status === 401 &&
      !original._retry &&
      !original.url?.includes("/auth/login") &&
      !original.url?.includes("/auth/refresh")
    ) {
      original._retry = true;

      try {
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) throw new Error("No refresh token");

        const { data } = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        original.headers.Authorization = `Bearer ${data.access_token}`;

        return api(original);
      } catch {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
        return Promise.reject(error);
      }
    }

    return Promise.reject(error);
  },
);

export default api;

// ─── Auth API ───

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface UserResponse {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  auth_provider: string;
  avatar_url: string | null;
  created_at: string;
  last_login_at: string | null;
}

export interface MessageResponse {
  message: string;
}

export const authApi = {
  register(data: { email: string; password: string; full_name: string }) {
    return api.post<{ data: UserResponse }>("/auth/register", data);
  },

  login(data: { email: string; password: string }) {
    return api.post<TokenResponse>("/auth/login", data);
  },

  refresh(refresh_token: string) {
    return api.post<TokenResponse>("/auth/refresh", { refresh_token });
  },

  me() {
    return api.get<{ data: UserResponse }>("/auth/me");
  },

  verifyEmail(token: string) {
    return api.post<MessageResponse>("/auth/verify-email", { token });
  },

  forgotPassword(email: string) {
    return api.post<MessageResponse>("/auth/forgot-password", { email });
  },

  resetPassword(data: { token: string; new_password: string }) {
    return api.post<MessageResponse>("/auth/reset-password", data);
  },

  googleAuthUrl() {
    return `${API_BASE_URL}/auth/google`;
  },
};
