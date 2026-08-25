import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { PlanService, Plan } from '../../core/services/plan.service';
import { PaymentService } from '../../core/services/payment.service';
import { AuthService } from '../../core/services/auth.service';
import { SubscriptionService, SubscriptionStatus } from '../../core/services/subscription.service';

@Component({
  selector: 'app-pricing',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './pricing.component.html',
  styleUrls: ['./pricing.component.css']
})
export class PricingComponent implements OnInit {
  plans: Plan[] = [];
  loading = true;
  error: string | null = null;
  processingPlanId: string | null = null;
  subscriptionStatus: SubscriptionStatus | null = null;
  isAuthenticated = false;

  constructor(
    private planService: PlanService,
    private paymentService: PaymentService,
    private authService: AuthService,
    private subscriptionService: SubscriptionService,
    private router: Router
  ) {}

  ngOnInit() {
    this.isAuthenticated = this.authService.isAuthenticated;
    this.loadPlans();
    if (this.isAuthenticated) {
      this.loadSubscriptionStatus();
    }
  }

  loadPlans() {
    this.loading = true;
    this.planService.listPlans().subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.plans = response.data;
        }
        this.loading = false;
      },
      error: (error) => {
        console.error('Failed to load plans:', error);
        this.error = 'Failed to load pricing plans. Please try again.';
        this.loading = false;
      }
    });
  }

  loadSubscriptionStatus() {
    this.subscriptionService.getSubscriptionStatus().subscribe({
      next: (response) => {
        if (response.success && response.data) {
          this.subscriptionStatus = response.data;
        }
      },
      error: (error) => {
        console.error('Failed to load subscription status:', error);
      }
    });
  }

  isCurrentPlan(planKey: string): boolean {
    return this.subscriptionStatus?.plan_key === planKey;
  }

  getButtonText(plan: Plan): string {
    const price = +plan.price_monthly;
    if (!this.isAuthenticated) {
      return price === 0 ? 'Get Started' : 'Subscribe';
    }

    if (this.isCurrentPlan(plan.key)) {
      return 'Current Plan';
    }

    return price === 0 ? 'Downgrade' : 'Subscribe';
  }

  isButtonDisabled(plan: Plan): boolean {
    return this.isCurrentPlan(plan.key) || this.processingPlanId !== null;
  }

  selectPlan(plan: Plan) {
    const price = +plan.price_monthly;
    // Free plan - just redirect to register or dashboard
    if (price === 0) {
      if (!this.isAuthenticated) {
        this.router.navigate(['/register']);
      } else {
        alert('You are already on the free tier. To downgrade from a paid plan, please cancel your subscription.');
      }
      return;
    }

    // Paid plans require authentication
    if (!this.isAuthenticated) {
      // Store intended plan and redirect to login
      sessionStorage.setItem('intended_plan_id', plan.id);
      this.router.navigate(['/login'], { 
        queryParams: { returnUrl: '/pricing', action: 'subscribe' } 
      });
      return;
    }

    // Create checkout session
    this.processingPlanId = plan.id;
    const successUrl = `${window.location.origin}/dashboard?payment=success`;
    const cancelUrl = `${window.location.origin}/pricing?payment=cancelled`;

    this.paymentService.createCheckoutSession(plan.id, successUrl, cancelUrl).subscribe({
      next: (response) => {
        if (response.success && response.data) {
          // Redirect to Stripe Checkout
          window.location.href = response.data.checkout_url;
        } else {
          this.processingPlanId = null;
          alert('Failed to create checkout session. Please try again.');
        }
      },
      error: (error) => {
        console.error('Checkout error:', error);
        this.processingPlanId = null;
        const errorMsg = error.error?.detail || 'Failed to start checkout process. Please try again.';
        alert(errorMsg);
      }
    });
  }

  formatPrice(price: number | string): string {
    const p = +price;
    return p === 0 ? 'Free' : `$${p.toFixed(0)}`;
  }

  formatNumber(num: number): string {
    return num.toLocaleString();
  }
}
