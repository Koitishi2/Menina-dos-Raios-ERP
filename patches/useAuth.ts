// Sem autenticação — app local, sempre logado como administrador
export function useAuth() {
  return {
    user:      { email: "local@bmmonteiro.local", id: "local" },
    isAdmin:   true,
    loading:   false,
    signOut:   async () => {},
  };
}
