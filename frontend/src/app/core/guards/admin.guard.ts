import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const adminGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const user = authService.currentUserValue;

  if (authService.isAuthenticated && user && user.role === 'ADMIN') {
    return true;
  }

  // Redirect non-admins back to dashboard
  return router.parseUrl('/dashboard');
};
